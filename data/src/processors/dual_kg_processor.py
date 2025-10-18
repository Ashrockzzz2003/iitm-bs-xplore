"""
Dual Knowledge Graph Processor

Handles the creation of separate knowledge graphs for course-specific and generic content.
Uses LLM-based categorization to automatically separate content types.
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from urllib.parse import urlparse

from src.processors.url_processor import fetch_html_from_url, detect_parser_from_url
from src.utils.content_categorizer import categorize_url_content
from src.utils.kg_cleaner import clean_dual_kgs
from src.xplore import (
    parse_academics_html,
    parse_course_html,
    parse_generic_html,
    merge_graphs,
)
from src.xplore.academics import guess_course_id_from_text, guess_course_id_from_href, classify_heading
from src.xplore.utils import text_of
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


def process_url_for_dual_kg(url: str, outline_summary: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """Process a URL and create separate course and generic knowledge graphs.
    
    Args:
        url: URL to process
        outline_summary: Whether to include outline summary in output
        
    Returns:
        Tuple of (course_kg, generic_kg, categorization_type)
    """
    logger.info(f"Processing URL for dual KG: {url}")
    
    # Fetch HTML content
    html = fetch_html_from_url(url)
    
    # Categorize content using LLM
    categorization, category_type = categorize_url_content(url, html)
    
    logger.info(f"Content categorized as: {category_type}")
    
    # Initialize empty knowledge graphs
    course_kg = {"nodes": [], "edges": [], "meta": {"type": "course", "source_url": url}}
    generic_kg = {"nodes": [], "edges": [], "meta": {"type": "generic", "source_url": url}}
    
    # Process based on categorization
    if category_type == "course":
        # Process as course content
        course_kg = process_course_content(url, html, outline_summary)
        generic_kg = {"nodes": [], "edges": [], "meta": {"type": "generic", "source_url": url}}
        logger.info(f"Created course KG with {len(course_kg.get('nodes', []))} nodes")
        
    elif category_type == "generic":
        # Process as generic content
        course_kg = {"nodes": [], "edges": [], "meta": {"type": "course", "source_url": url}}
        generic_kg = process_generic_content(url, html, outline_summary)
        logger.info(f"Created generic KG with {len(generic_kg.get('nodes', []))} nodes")
        
    else:  # mixed
        # Process both types
        course_kg = process_course_content(url, html, outline_summary)
        generic_kg = process_generic_content(url, html, outline_summary)
        logger.info(f"Created mixed KGs: course={len(course_kg.get('nodes', []))} nodes, generic={len(generic_kg.get('nodes', []))} nodes")
    
    # Add categorization metadata
    course_kg["meta"]["categorization"] = categorization
    course_kg["meta"]["category_type"] = category_type
    generic_kg["meta"]["categorization"] = categorization
    generic_kg["meta"]["category_type"] = category_type
    
    # Clean both knowledge graphs to remove unwanted content
    course_kg, generic_kg = clean_dual_kgs(course_kg, generic_kg)
    
    return course_kg, generic_kg, category_type


def process_course_content(url: str, html: str, outline_summary: bool) -> Dict[str, Any]:
    """Process content as course-specific.
    
    Args:
        url: Source URL
        html: HTML content
        outline_summary: Whether to include outline summary
        
    Returns:
        Course-specific knowledge graph
    """
    logger.info("Processing content as course-specific")
    
    # Detect parser type
    parser_type = detect_parser_from_url(url)
    
    # Map parser types to their corresponding parsing functions
    parser_functions = {
        "academics": lambda html, url: parse_academics_html(html, base_url=url),
        "course": lambda html, url: parse_course_html(html, source_path=url),
        "generic": lambda html, url: parse_generic_html(
            html,
            root_id=f"doc:{Path(urlparse(url).path).stem}",
            root_title=Path(urlparse(url).path).stem or "Document",
        ),
    }
    
    # Parse the content
    kg = parser_functions[parser_type](html, url)
    
    # Add course-specific metadata
    kg["meta"]["type"] = "course"
    kg["meta"]["source_url"] = url
    kg["meta"]["parser_used"] = parser_type
    
    # For academics pages, also extract and parse course pages
    if parser_type == "academics":
        course_urls = extract_course_urls_from_academics(html, url)
        logger.info(f"Found {len(course_urls)} course URLs in academics page")
        
        if course_urls:
            course_graphs = []
            successful = 0
            failed = 0
            
            for i, course_info in enumerate(course_urls, 1):
                try:
                    logger.info(f"  [{i}/{len(course_urls)}] Parsing course {course_info['courseId']}")
                    course_html = fetch_html_from_url(course_info['href'])
                    course_graph = parse_course_html(course_html, source_path=course_info['href'])
                    
                    # Update course node IDs for uniqueness
                    for node in course_graph.get("nodes", []):
                        if node.get("type") == "Course":
                            original_id = node["id"]
                            course_id = course_info['courseId']
                            node["id"] = f"course:{course_id}"
                            node["properties"]["courseId"] = course_id
                            
                            # Use label from academics page if available
                            course_label = course_info['label']
                            current_title = node["properties"].get("title", "")
                            
                            if (course_label and course_label != course_id and 
                                (not current_title or 
                                 current_title in ["Course Page - IIT Madras Degree Program", "IIT Madras Degree Program", "Course Information"] or
                                 current_title.startswith("COURSE:"))):
                                node["properties"]["title"] = course_label
                            
                            # Update edges
                            for edge in course_graph.get("edges", []):
                                if edge.get("source") == original_id:
                                    edge["source"] = node["id"]
                                if edge.get("target") == original_id:
                                    edge["target"] = node["id"]
                    
                    # Add course metadata
                    if "meta" not in course_graph:
                        course_graph["meta"] = {}
                    course_graph["meta"]["level"] = course_info['level']
                    course_graph["meta"]["course_id"] = course_info['courseId']
                    course_graph["meta"]["status"] = "success"
                    
                    course_graphs.append(course_graph)
                    successful += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to parse course {course_info['courseId']}: {e}")
                    failed += 1
                    continue
            
            # Merge course graphs with main graph
            if course_graphs:
                logger.info(f"Course parsing complete: {successful} successful, {failed} failed")
                all_graphs = [kg] + course_graphs
                kg = merge_graphs(all_graphs)
                
                # Add course parsing statistics
                kg["meta"]["courses_parsed"] = len(course_graphs)
                kg["meta"]["courses_successful"] = successful
                kg["meta"]["courses_failed"] = failed
                kg["meta"]["total_courses_found"] = len(course_urls)
    
    return kg


def process_generic_content(url: str, html: str, outline_summary: bool) -> Dict[str, Any]:
    """Process content as generic (non-course) content.
    
    Args:
        url: Source URL
        html: HTML content
        outline_summary: Whether to include outline summary
        
    Returns:
        Generic knowledge graph
    """
    logger.info("Processing content as generic")
    
    # Use generic parser for all content
    kg = parse_generic_html(
        html,
        root_id=f"doc:{Path(urlparse(url).path).stem}",
        root_title=Path(urlparse(url).path).stem or "Document",
    )
    
    # Add generic-specific metadata
    kg["meta"]["type"] = "generic"
    kg["meta"]["source_url"] = url
    kg["meta"]["parser_used"] = "generic"
    
    return kg


def extract_course_urls_from_academics(html: str, base_url: str) -> List[Dict[str, str]]:
    """Extract course URLs from academics page HTML.
    
    This is a copy of the function from url_processor.py to avoid circular imports.
    """
    soup = BeautifulSoup(html, "lxml")
    course_urls = []
    seen_courses = set()
    current_level = None
    
    # Iterate through all HTML elements to find headings and course links
    for el in soup.descendants:
        if not isinstance(el, Tag):
            continue
        name = el.name or ""
        classes = " ".join(el.get("class", []))
        
        # Detect heading-like elements
        is_heading_like = bool(
            re.fullmatch(r"h[1-6]", name)
            or (
                name in ("p", "div", "span")
                and (
                    re.search(r"\bh[1-6]\b", classes)
                    or (
                        "font-weight-600" in classes
                        and ("text-dark" in classes or "text-secondary" in classes)
                    )
                    or (el.has_attr("id") and re.match(r"AC\d+", el.get("id", "")))
                )
            )
        )
        
        # Update current level context when we find a heading
        if is_heading_like:
            hid = classify_heading(text_of(el))
            if hid:
                current_level = hid
            continue
            
        # Check for regular <a> tags with href (course links)
        if el.name == "a" and el.has_attr("href"):
            label = text_of(el)
            href = el.get("href", "")
            cid = guess_course_id_from_text(label) or guess_course_id_from_href(href)
            
            # Handle "coming soon" links
            if not cid and "coming-soon.html" in href:
                row = el.find_parent("tr")
                if row:
                    row_text = text_of(row)
                    cid = guess_course_id_from_text(row_text)
            
            # Add course to list if we found a valid course ID
            if cid and cid not in seen_courses:
                from urllib.parse import urljoin
                full_url = urljoin(base_url, href)
                if "/course_pages/" in full_url or "/ds/" in full_url or "/es/" in full_url:
                    course_urls.append({
                        "courseId": cid,
                        "label": label,
                        "href": full_url,
                        "level": current_level or "unknown"
                    })
                    seen_courses.add(cid)
        
        # Check for elements with data-url attribute
        elif el.has_attr("data-url"):
            data_url = el.get("data-url", "")
            cid = guess_course_id_from_href(data_url)
            if cid and cid not in seen_courses:
                from urllib.parse import urljoin
                full_url = urljoin(base_url, data_url)
                if "/course_pages/" in full_url or "/ds/" in full_url or "/es/" in full_url:
                    label = text_of(el)
                    if not label or len(label.strip()) < 3:
                        label = cid
                    course_urls.append({
                        "courseId": cid,
                        "label": label,
                        "href": full_url,
                        "level": current_level or "unknown"
                    })
                    seen_courses.add(cid)
    
    return course_urls


def create_hierarchical_course_kg(ds_graphs: List[Dict[str, Any]], es_graphs: List[Dict[str, Any]], other_graphs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a hierarchical course knowledge graph with proper DS/ES separation.
    
    Args:
        ds_graphs: List of DS course graphs
        es_graphs: List of ES course graphs  
        other_graphs: List of other course graphs
        
    Returns:
        Hierarchical course knowledge graph
    """
    logger.info("Creating hierarchical course knowledge graph")
    
    # Create main BS program node
    main_program = {
        "id": "BS",
        "type": "Program",
        "properties": {
            "title": "Bachelor of Science",
            "description": "IITM Online Bachelor of Science Program",
            "institution": "Indian Institute of Technology Madras",
            "programs": []
        }
    }
    
    nodes = [main_program]
    edges = []
    meta = {
        "type": "course",
        "hierarchical": True,
        "main_program": "BS",
        "programs": {}
    }
    
    # Process DS program
    if ds_graphs:
        ds_kg = merge_graphs(ds_graphs)
        ds_nodes, ds_edges = create_program_hierarchy("DS", "Data Science", ds_kg)
        nodes.extend(ds_nodes)
        edges.extend(ds_edges)
        meta["programs"]["DS"] = {
            "name": "Data Science",
            "node_count": len(ds_nodes),
            "edge_count": len(ds_edges)
        }
        main_program["properties"]["programs"].append("DS")
    
    # Process ES program
    if es_graphs:
        es_kg = merge_graphs(es_graphs)
        es_nodes, es_edges = create_program_hierarchy("ES", "Electronics Systems", es_kg)
        nodes.extend(es_nodes)
        edges.extend(es_edges)
        meta["programs"]["ES"] = {
            "name": "Electronics Systems", 
            "node_count": len(es_nodes),
            "edge_count": len(es_edges)
        }
        main_program["properties"]["programs"].append("ES")
    
    # Process other programs
    if other_graphs:
        other_kg = merge_graphs(other_graphs)
        other_nodes = other_kg.get("nodes", [])
        other_edges = other_kg.get("edges", [])
        nodes.extend(other_nodes)
        edges.extend(other_edges)
        meta["programs"]["OTHER"] = {
            "name": "Other Programs",
            "node_count": len(other_nodes),
            "edge_count": len(other_edges)
        }
        main_program["properties"]["programs"].append("OTHER")
    
    meta["total_nodes"] = len(nodes)
    meta["total_edges"] = len(edges)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": meta
    }


def create_program_hierarchy(program_code: str, program_name: str, program_kg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Create hierarchical structure for a specific program.
    
    Args:
        program_code: Program code (DS/ES)
        program_name: Program name
        program_kg: Program knowledge graph
        
    Returns:
        Tuple of (nodes, edges) for the program hierarchy
    """
    nodes = []
    edges = []
    
    # Create program node
    program_node = {
        "id": f"program:{program_code}",
        "type": "Program",
        "properties": {
            "title": program_name,
            "code": program_code,
            "description": f"IITM {program_name} Program"
        }
    }
    nodes.append(program_node)
    
    # Connect to main BS program
    edges.append({
        "source": "BS",
        "target": f"program:{program_code}",
        "type": "HAS_PROGRAM",
        "properties": {"program_code": program_code}
    })
    
    # Create program sections based on course levels
    if program_code == "DS":
        # DS has Foundation, Diploma in DS, Diploma in Programming, and Degree levels
        sections = [
            ("foundation", "Foundation Level", "Foundation level courses"),
            ("diploma_ds", "Diploma in Data Science", "Data Science diploma courses"),
            ("diploma_prog", "Diploma in Programming", "Programming diploma courses"),
            ("degree", "Degree Level", "Degree level courses")
        ]
    else:
        # ES has Foundation, Diploma, and Degree levels
        sections = [
            ("foundation", "Foundation Level", "Foundation level courses"),
            ("diploma", "Diploma Level", "Diploma level courses"),
            ("degree", "Degree Level", "Degree level courses")
        ]
    
    # Create section nodes and connect to program
    for section_id, section_title, section_desc in sections:
        section_node = {
            "id": f"section:{program_code}_{section_id}",
            "type": "Section",
            "properties": {
                "title": section_title,
                "description": section_desc,
                "program": program_code,
                "level": section_id
            }
        }
        nodes.append(section_node)
        
        edges.append({
            "source": f"program:{program_code}",
            "target": f"section:{program_code}_{section_id}",
            "type": "HAS_SECTION",
            "properties": {"section_type": section_id}
        })
    
    # Add courses from the program KG to appropriate sections
    program_nodes = program_kg.get("nodes", [])
    program_edges = program_kg.get("edges", [])
    
    for node in program_nodes:
        if node.get("type") == "Course":
            course_id = node.get("properties", {}).get("courseId", "")
            course_code = course_id.upper()
            
            # Determine which section this course belongs to
            target_section = None
            if program_code == "DS":
                if course_code.startswith(("BSMA100", "BSCS100", "BSHS100")):
                    target_section = f"section:{program_code}_foundation"
                elif course_code.startswith(("BSDA200", "BSMS200")):
                    target_section = f"section:{program_code}_diploma_ds"
                elif course_code.startswith(("BSMA200", "BSCS200", "BSHS200", "BSSE200")):
                    target_section = f"section:{program_code}_diploma_prog"
                elif course_code.startswith(("BSMA300", "BSCS300", "BSHS300", "BSMS300", "BSSE300", "BSDA300", "BSGN300", "BSMA400", "BSCS400", "BSHS400", "BSMS400", "BSSE400", "BSDA400", "BSBT400", "BSMA500", "BSCS500", "BSHS500", "BSMS500", "BSSE500", "BSDA500", "BSEE500", "BSMA600", "BSCS600", "BSHS600", "BSMS600", "BSSE600", "BSDA600", "BSMA690", "BSCS690", "BSHS690", "BSMS690", "BSSE690", "BSDA690")):
                    target_section = f"section:{program_code}_degree"
            else:  # ES
                if course_code.startswith(("EE110", "CS110", "MA110", "HS110")):
                    target_section = f"section:{program_code}_foundation"
                elif course_code.startswith(("EE210", "CS210", "MA210", "EE190", "CS190")):
                    target_section = f"section:{program_code}_diploma"
                elif course_code.startswith(("EE310", "EE410", "EE510", "EE390", "EE490", "MA310", "BS")):
                    target_section = f"section:{program_code}_degree"
            
            if target_section:
                # Add course to nodes
                course_node = node.copy()
                course_node["properties"]["program"] = program_code
                course_node["properties"]["section"] = target_section
                nodes.append(course_node)
                
                # Connect course to section
                edges.append({
                    "source": target_section,
                    "target": course_node["id"],
                    "type": "CONTAINS_COURSE",
                    "properties": {"course_id": course_id}
                })
    
    # Add other nodes and edges from the program KG
    for node in program_nodes:
        if node.get("type") != "Course":  # We already processed courses above
            node_copy = node.copy()
            node_copy["properties"]["program"] = program_code
            nodes.append(node_copy)
    
    for edge in program_edges:
        edge_copy = edge.copy()
        edge_copy["properties"]["program"] = program_code
        edges.append(edge_copy)
    
    return nodes, edges


def process_multiple_urls_for_dual_kg(urls: List[str], outline_summary: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process multiple URLs and create unified course and generic knowledge graphs with proper program hierarchy.
    
    Args:
        urls: List of URLs to process
        outline_summary: Whether to include outline summary
        
    Returns:
        Tuple of (unified_course_kg, unified_generic_kg)
    """
    logger.info(f"Processing {len(urls)} URLs for dual KG generation")
    
    # Separate URLs by program type
    ds_urls = []
    es_urls = []
    other_urls = []
    
    for url in urls:
        if "/ds/" in url.lower():
            ds_urls.append(url)
        elif "/es/" in url.lower():
            es_urls.append(url)
        else:
            other_urls.append(url)
    
    logger.info(f"Found {len(ds_urls)} DS URLs, {len(es_urls)} ES URLs, {len(other_urls)} other URLs")
    
    # Process each program separately to maintain hierarchy
    ds_course_graphs = []
    ds_generic_graphs = []
    es_course_graphs = []
    es_generic_graphs = []
    other_course_graphs = []
    other_generic_graphs = []
    
    # Process DS URLs
    for url in ds_urls:
        try:
            course_kg, generic_kg, category_type = process_url_for_dual_kg(url, outline_summary)
            if course_kg.get("nodes"):
                # Add program metadata
                course_kg["meta"]["program"] = "DS"
                ds_course_graphs.append(course_kg)
            if generic_kg.get("nodes"):
                generic_kg["meta"]["program"] = "DS"
                ds_generic_graphs.append(generic_kg)
        except Exception as e:
            logger.error(f"Failed to process DS URL {url}: {e}")
    
    # Process ES URLs
    for url in es_urls:
        try:
            course_kg, generic_kg, category_type = process_url_for_dual_kg(url, outline_summary)
            if course_kg.get("nodes"):
                # Add program metadata
                course_kg["meta"]["program"] = "ES"
                es_course_graphs.append(course_kg)
            if generic_kg.get("nodes"):
                generic_kg["meta"]["program"] = "ES"
                es_generic_graphs.append(generic_kg)
        except Exception as e:
            logger.error(f"Failed to process ES URL {url}: {e}")
    
    # Process other URLs
    for url in other_urls:
        try:
            course_kg, generic_kg, category_type = process_url_for_dual_kg(url, outline_summary)
            if course_kg.get("nodes"):
                course_kg["meta"]["program"] = "OTHER"
                other_course_graphs.append(course_kg)
            if generic_kg.get("nodes"):
                generic_kg["meta"]["program"] = "OTHER"
                other_generic_graphs.append(generic_kg)
        except Exception as e:
            logger.error(f"Failed to process other URL {url}: {e}")
    
    # Create unified course KG with proper hierarchy
    unified_course_kg = create_hierarchical_course_kg(ds_course_graphs, es_course_graphs, other_course_graphs)
    
    # Create unified generic KG
    all_generic_graphs = ds_generic_graphs + es_generic_graphs + other_generic_graphs
    unified_generic_kg = merge_graphs(all_generic_graphs) if all_generic_graphs else {"nodes": [], "edges": [], "meta": {"type": "generic"}}
    
    # Add metadata about the processing
    unified_course_kg["meta"]["total_urls_processed"] = len(urls)
    unified_course_kg["meta"]["ds_urls"] = len(ds_urls)
    unified_course_kg["meta"]["es_urls"] = len(es_urls)
    unified_course_kg["meta"]["other_urls"] = len(other_urls)
    unified_generic_kg["meta"]["total_urls_processed"] = len(urls)
    unified_generic_kg["meta"]["generic_urls_found"] = len(all_generic_graphs)
    
    # Clean both knowledge graphs to remove unwanted content
    unified_course_kg, unified_generic_kg = clean_dual_kgs(unified_course_kg, unified_generic_kg)
    
    logger.info(f"Dual KG generation complete: {len(unified_course_kg.get('nodes', []))} course nodes, {len(unified_generic_kg.get('nodes', []))} generic nodes")
    
    return unified_course_kg, unified_generic_kg
