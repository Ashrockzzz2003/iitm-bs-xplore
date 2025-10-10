import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

from xplore import (
    parse_academics_html,
    parse_course_html,
    parse_generic_html,
    merge_graphs,
)
from xplore.outline import build_outline, SectionOutline


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


def print_outline_summary(html: str) -> None:
    """Print a logical summary of document structure."""
    soup = BeautifulSoup(html, "lxml")
    roots = build_outline(soup)

    def compact(text: str, max_len: int = 120) -> str:
        t = (text or "").strip()
        return t if len(t) <= max_len else (t[: max_len - 1] + "…")

    def iter_nodes(nodes: List[SectionOutline]):
        for n in nodes:
            yield n
            for c in iter_nodes(n.children):
                yield c

    parents = [n for n in iter_nodes(roots) if n.child_count() > 0]
    for p in parents:
        anchor = f" #{p.tag_id}" if p.tag_id else ""
        print(
            f"Parent: {compact(p.title)} (h{p.level}, children={p.child_count()}){anchor}"
        )
        for c in p.children:
            canchor = f" #{c.tag_id}" if c.tag_id else ""
            print(f"  - Child: {compact(c.title)} (h{c.level}){canchor}")


def get_parser_functions() -> Dict[str, Callable]:
    """Return a mapping of parser types to their functions."""
    return {
        "academics": lambda html, url: parse_academics_html(html, base_url=url),
        "course": lambda html, url: parse_course_html(html, source_path=url),
        "generic": lambda html, url: parse_generic_html(
            html,
            root_id=f"doc:{Path(urlparse(url).path).stem}",
            root_title=Path(urlparse(url).path).stem or "Document",
        ),
    }


def extract_course_urls_from_academics(html: str, base_url: str) -> List[Dict[str, str]]:
    """Extract course URLs from academics page HTML."""
    from bs4 import BeautifulSoup, Tag
    from urllib.parse import urljoin
    from xplore.academics import guess_course_id_from_text, guess_course_id_from_href, classify_heading
    from xplore.utils import text_of
    
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

    parser_functions = get_parser_functions()
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

    if outline_summary:
        print_outline_summary(html)

    return graph, parser_type


def process_file_inputs(args) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Process file inputs and return graphs and parser type."""
    graphs = []
    parser_used = None

    if args.academics:
        html = Path(args.academics).read_text(encoding="utf-8", errors="ignore")
        graphs.append(
            parse_academics_html(html, base_url=str(Path(args.academics).parent))
        )
        parser_used = "academics"

    if args.course_files:
        for cf in args.course_files:
            html = Path(cf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(parse_course_html(html, source_path=cf))
        parser_used = "course"

    if args.generic:
        for gf in args.generic:
            html = Path(gf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(
                parse_generic_html(
                    html, root_id=f"doc:{Path(gf).stem}", root_title=Path(gf).name
                )
            )
        parser_used = "generic"

    return graphs, parser_used


def write_output(
    kg: Dict[str, Any], output_path: str, out_dir: str, parser_used: Optional[str]
) -> None:
    """Write knowledge graph to file or print to stdout."""
    out = json.dumps(kg, indent=2, ensure_ascii=False)

    if output_path:
        out_path = Path(output_path)
        # If user provided a bare filename (no directory), place it under --out-dir
        if not out_path.is_absolute() and (out_path.parent == Path(".")):
            out_path = Path(out_dir) / out_path.name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out, encoding="utf-8")
        print(f"Knowledge graph saved to: {out_path}")
        if parser_used:
            print(f"Parser used: {parser_used}")
    else:
        print(out)


def main() -> None:
    """Main entry point for the application."""
    args = parse_arguments()
    graphs, parser_used = process_inputs(args)

    if not graphs:
        raise SystemExit(
            "No input provided. Use --url, --academics, --course-files, or --generic"
        )

    kg = merge_graphs(graphs)
    add_parser_metadata(kg, parser_used)
    write_output(kg, args.output, args.out_dir, parser_used)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse HTML into a knowledge graph JSON with automatic parser detection"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL to fetch and parse (automatically detects parser)",
        required=False,
    )
    parser.add_argument(
        "--academics", type=str, help="Path to academics.html file", required=False
    )
    parser.add_argument(
        "--course-files",
        type=str,
        nargs="*",
        help="Paths to course HTML pages",
        default=None,
    )
    parser.add_argument(
        "--generic",
        type=str,
        nargs="*",
        help="Paths to generic HTML pages",
        default=None,
    )
    parser.add_argument(
        "--output", type=str, help="Path to write KG JSON (default: print)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs",
        help="Directory for generated JSON files when a bare filename is given",
    )
    parser.add_argument(
        "--outline-summary",
        action="store_true",
        help="Print logical summary: each parent section and its immediate children",
    )
    return parser.parse_args()


def process_inputs(args) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Process all input sources and return graphs and parser type."""
    graphs = []
    parser_used = None

    # Handle URL input with automatic parser detection
    if args.url:
        graph, parser_type = process_url_input(args.url, args.outline_summary)
        graphs.append(graph)
        parser_used = parser_type

    # Handle file inputs (backward compatibility)
    file_graphs, file_parser = process_file_inputs(args)
    graphs.extend(file_graphs)
    if file_parser:
        parser_used = file_parser

    return graphs, parser_used


def add_parser_metadata(kg: Dict[str, Any], parser_used: Optional[str]) -> None:
    """Add parser information to knowledge graph metadata."""
    if "meta" not in kg:
        kg["meta"] = {}
    if parser_used:
        kg["meta"]["parser_used"] = parser_used


if __name__ == "__main__":
    main()
