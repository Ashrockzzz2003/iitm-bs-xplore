"""
URL Processing Module

Handles fetching and processing URLs, including course URL extraction
and automatic parser detection.
"""

import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Tag

from xplore import (
    parse_academics_html,
    parse_course_html,
    parse_generic_html,
    merge_graphs,
)
from xplore.academics import guess_course_id_from_text, guess_course_id_from_href, classify_heading
from xplore.utils import text_of


def fetch_html_from_url(url: str) -> str:
    """Fetch HTML content from a URL with proper error handling."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL {url}: {e}")


def detect_parser_from_url(url: str) -> str:
    """Detect which parser to use based on URL pattern."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    path = parsed_url.path.lower()

    # IITM Academics pages
    if "study.iitm.ac.in" in domain and "/ds/academics.html" in path:
        return "academics"

    # IITM Course pages (pattern: /ds/course_pages/*.html)
    if (
        "study.iitm.ac.in" in domain
        and "/ds/course_pages/" in path
        and path.endswith(".html")
    ):
        return "course"

    # Default to generic parser for unknown URLs
    return "generic"


def extract_course_urls_from_academics(html: str, base_url: str) -> List[Dict[str, str]]:
    """Extract course URLs from academics page HTML."""
    soup = BeautifulSoup(html, "lxml")
    course_urls = []
    seen_courses = set()  # To avoid duplicates
    current_level = None
    
    for el in soup.descendants:
        if not isinstance(el, Tag):
            continue
        name = el.name or ""
        classes = " ".join(el.get("class", []))
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
        if is_heading_like:
            hid = classify_heading(text_of(el))
            if hid:
                current_level = hid
            continue
        # Check for regular <a> tags with href
        if el.name == "a" and el.has_attr("href"):
            label = text_of(el)
            href = el.get("href", "")
            cid = guess_course_id_from_text(label) or guess_course_id_from_href(href)
            
            # If this is a "coming soon" link, try to extract course ID from the table row
            if not cid and "coming-soon.html" in href:
                # Look for course ID in the same table row
                row = el.find_parent("tr")
                if row:
                    row_text = text_of(row)
                    cid = guess_course_id_from_text(row_text)
            
            if cid and cid not in seen_courses:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                # Only include course pages, not other links
                if "/course_pages/" in full_url or "/ds/" in full_url:
                    course_urls.append({
                        "courseId": cid,
                        "label": label,
                        "href": full_url,
                        "level": current_level or "unknown"
                    })
                    seen_courses.add(cid)
        
        # Check for elements with data-url attribute (like table rows)
        elif el.has_attr("data-url"):
            data_url = el.get("data-url", "")
            # Extract course ID from the data-url
            cid = guess_course_id_from_href(data_url)
            if cid and cid not in seen_courses:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, data_url)
                # Only include course pages, not other links
                if "/course_pages/" in full_url or "/ds/" in full_url:
                    # Try to get a meaningful label from the element
                    label = text_of(el)
                    if not label or len(label.strip()) < 3:
                        # If no good label, use the course ID
                        label = cid
                    course_urls.append({
                        "courseId": cid,
                        "label": label,
                        "href": full_url,
                        "level": current_level or "unknown"
                    })
                    seen_courses.add(cid)
    
    return course_urls


def process_url_input(url: str, outline_summary: bool) -> tuple[Dict[str, Any], str]:
    """Process URL input and return knowledge graph and parser type."""
    print(f"Fetching URL: {url}")
    html = fetch_html_from_url(url)
    parser_type = detect_parser_from_url(url)
    print(f"Detected parser: {parser_type}")

    parser_functions = {
        "academics": lambda html, url: parse_academics_html(html, base_url=url),
        "course": lambda html, url: parse_course_html(html, source_path=url),
        "generic": lambda html, url: parse_generic_html(
            html,
            root_id=f"doc:{Path(urlparse(url).path).stem}",
            root_title=Path(urlparse(url).path).stem or "Document",
        ),
    }
    
    graph = parser_functions[parser_type](html, url)

    # If it's an academics page, also parse all course pages
    if parser_type == "academics":
        print("Extracting course URLs from academics page...")
        course_urls = extract_course_urls_from_academics(html, url)
        print(f"Found {len(course_urls)} course URLs")
        
        if course_urls:
            print("Parsing course pages...")
            course_graphs = []
            successful = 0
            failed = 0
            
            # Process all courses for production
            max_courses = len(course_urls)
            print(f"Processing all {max_courses} courses...")
            
            for i, course_info in enumerate(course_urls[:max_courses], 1):
                try:
                    print(f"  [{i}/{max_courses}] Parsing {course_info['courseId']}: {course_info['label']}")
                    course_html = fetch_html_from_url(course_info['href'])
                    course_graph = parse_course_html(course_html, source_path=course_info['href'])
                    
                    # Make course IDs unique by prefixing with the actual course ID
                    for node in course_graph.get("nodes", []):
                        if node.get("type") == "Course":
                            # Update the node ID to include the course ID for uniqueness
                            original_id = node["id"]
                            course_id = course_info['courseId']
                            node["id"] = f"course:{course_id}"
                            node["properties"]["courseId"] = course_id
                            # Update any edges that reference this node
                            for edge in course_graph.get("edges", []):
                                if edge.get("source") == original_id:
                                    edge["source"] = node["id"]
                                if edge.get("target") == original_id:
                                    edge["target"] = node["id"]
                    
                    # Add level information to the course graph
                    if "meta" not in course_graph:
                        course_graph["meta"] = {}
                    course_graph["meta"]["level"] = course_info['level']
                    course_graph["meta"]["course_id"] = course_info['courseId']
                    course_graph["meta"]["status"] = "success"
                    
                    course_graphs.append(course_graph)
                    successful += 1
                except Exception as e:
                    print(f"    Warning: Failed to parse {course_info['courseId']}: {e}")
                    # Add a placeholder entry for failed courses
                    failed_course = {
                        "nodes": [],
                        "edges": [],
                        "meta": {
                            "level": course_info['level'],
                            "course_id": course_info['courseId'],
                            "status": "failed",
                            "error": str(e)
                        }
                    }
                    course_graphs.append(failed_course)
                    failed += 1
                    continue
            
            # Merge course graphs with the main academics graph
            if course_graphs:
                print(f"Course parsing complete: {successful} successful, {failed} failed")
                all_graphs = [graph] + course_graphs
                graph = merge_graphs(all_graphs)
                graph["meta"]["courses_parsed"] = len(course_graphs)
                graph["meta"]["courses_successful"] = successful
                graph["meta"]["courses_failed"] = failed
                graph["meta"]["total_courses_found"] = len(course_urls)

    return graph, parser_type
