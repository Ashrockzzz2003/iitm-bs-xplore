import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from rapidfuzz import fuzz, process
from .types import Node, Edge
from .outline import SectionOutline, build_outline
from .utils import normalize_whitespace, text_of, slugify


def guess_course_id_from_text(text: str) -> Optional[str]:
    """Extract course ID from text using regex pattern matching.
    
    Looks for patterns like 'BSDA1001', 'CS-2001', etc. in the given text.
    """
    match = re.search(r"\b[A-Z]{2,4}\s?-?\d{3,4}\b", text or "")
    if match:
        return match.group(0).replace(" ", "").upper()
    return None


def guess_course_id_from_href(href: str) -> Optional[str]:
    """Extract course ID from URL/href using multiple pattern matching strategies.
    
    Tries different patterns to find course IDs in URLs:
    1. Query parameter id=COURSE_ID
    2. Path segment /COURSE_ID.html or /COURSE_ID/
    3. Any occurrence of COURSE_ID pattern in the URL
    """
    m = re.search(r"[?&#]id=([A-Za-z0-9_-]+)", href)
    if m:
        return m.group(1).upper()
    m = re.search(r"/([A-Za-z]{2,4}\d{3,4})(?:\.|/|$)", href)
    if m:
        return m.group(1).upper()
    m = re.search(r"([A-Za-z]{2,4}\d{3,4})", href)
    if m:
        return m.group(1).upper()
    return None


def collect_headings(soup: BeautifulSoup) -> List[Tag]:
    """Collect all heading-like elements from the HTML soup.
    
    This function identifies both standard HTML headings (h1-h6) and
    elements that are styled to look like headings (divs with heading classes).
    """
    heading_like = []
    for el in soup.find_all(True):
        name = el.name or ""
        classes = " ".join(el.get("class", []))
        
        # Standard HTML headings
        if re.fullmatch(r"h[1-6]", name):
            heading_like.append(el)
            continue
            
        # Styled elements that act as headings
        if name in ("p", "div", "span") and (
            re.search(r"\bh[1-6]\b", classes)
            or (
                "font-weight-600" in classes
                and ("text-dark" in classes or "text-secondary" in classes)
            )
            or (el.has_attr("id") and re.match(r"AC\d+", el.get("id", "")))
        ):
            heading_like.append(el)
    return heading_like


def fuzzy_find_section(
    soup: BeautifulSoup, targets: List[str], min_score: int = 70
) -> Dict[str, Tag]:
    result: Dict[str, Tag] = {}
    headings = collect_headings(soup)
    heading_texts = [text_of(h) for h in headings]
    for desired in targets:
        if not heading_texts:
            continue
        best = process.extractOne(
            desired,
            heading_texts,
            scorer=fuzz.token_set_ratio,
        )
        if best and best[1] >= min_score:
            idx = heading_texts.index(best[0])
            result[desired] = headings[idx]
    return result


def next_sibling_section_content(header: Tag) -> List[Tag]:
    content_nodes: List[Tag] = []
    level = int(header.name[1]) if header.name and header.name.startswith("h") else 7
    node = header
    while True:
        node = node.find_next_sibling()
        if node is None:
            break
        if isinstance(node, Tag) and node.name and node.name.startswith("h"):
            hlevel = int(node.name[1])
            if hlevel <= level:
                break
        content_nodes.append(node)
    return content_nodes


def extract_bullets(nodes: List[Tag]) -> List[str]:
    items: List[str] = []
    for n in nodes:
        for li in n.select("li"):
            t = text_of(li)
            if t:
                items.append(t)
    return items


def extract_paragraphs(nodes: List[Tag]) -> List[str]:
    paras: List[str] = []
    for n in nodes:
        # If the node itself is a paragraph, include its text
        if n.name == "p":
            t = text_of(n)
            if t:
                paras.append(t)
        # Also look for paragraph tags inside the node
        for p in n.select("p"):
            t = text_of(p)
            if t:
                paras.append(t)
    return paras


def parse_labeled_fields(nodes: List[Tag]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for dl in [n for parent in nodes for n in parent.select("dl")]:
        for dt in dl.select("dt"):
            key = text_of(dt)
            dd = dt.find_next_sibling("dd")
            if key and dd:
                fields[key] = text_of(dd)
    for parent in nodes:
        for strong in parent.select("strong, b"):
            key = text_of(strong).rstrip(":")
            if not key:
                continue
            value_parts: List[str] = []
            for sib in strong.next_siblings:
                if isinstance(sib, Tag) and sib.name and sib.name.startswith("h"):
                    break
                txt = normalize_whitespace(
                    getattr(sib, "get_text", lambda *_: str(sib))(" ", strip=True)
                )
                if txt:
                    value_parts.append(txt)
            value = normalize_whitespace(" ".join(value_parts))
            if value:
                fields.setdefault(key, value)
    return fields


def extract_tables(nodes: List[Tag]) -> List[List[List[str]]]:
    tables_rows: List[List[List[str]]] = []
    for table in [n for parent in nodes for n in parent.select("table")]:
        tbody = table.find("tbody") or table
        table_data: List[List[str]] = []
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            row = [text_of(c) for c in cells]
            if any(cell for cell in row):
                table_data.append(row)
        if table_data:
            tables_rows.append(table_data)
    return tables_rows


def classify_heading(text: str) -> Optional[str]:
    """Classify a heading text to determine its level (foundation, diploma, degree, etc.)."""
    level_defs = [
        {"id": "level:foundation", "title": "Foundation", "match": ["Foundation Level", "Foundation"]},
        {"id": "level:diploma", "title": "Diploma", "match": ["Diploma Level", "Diploma"]},
        {"id": "level:degree", "title": "Degree", "match": ["Degree Level", "Degree"]},
    ]
    
    t = normalize_whitespace(text)
    best_score = 0
    best_id: Optional[str] = None
    for ld in level_defs:
        for pattern in ld["match"]:
            score = fuzz.token_set_ratio(t, pattern)
            if score > best_score:
                best_score = score
                best_id = ld["id"]
    return best_id if best_score >= 70 else None


def parse_academics_html(
    html: str, base_url: Optional[str] = None
) -> Dict[str, object]:
    soup = BeautifulSoup(html, "lxml")

    outline_roots = build_outline(soup)

    target_sections = [
        "Program Structure",
        "Term Structure",
        "Course Structure",
        "Assessments",
        "Exam Cities",
        "Fee Structure",
        "Foundation Level",
        "Diploma Level",
        "Degree Level",
        "Rules",
        "Policies",
        "Attendance",
    ]
    matched = fuzzy_find_section(soup, target_sections, min_score=65)

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []
    outline_summary: List[Dict[str, object]] = []

    def ensure_node(nid: str, ntype: str, props: Dict[str, object]) -> Node:
        if nid not in nodes:
            nodes[nid] = Node(id=nid, type=ntype, properties=dict(props))
        else:
            nodes[nid].properties.update(props)
        return nodes[nid]

    root = ensure_node(
        "program:IITM_BS", "Program", {"name": "IIT Madras BS Degree Program"}
    )

    def register_outline(
        node: SectionOutline, parent_id: Optional[str], depth: int
    ) -> None:
        sec_id = f"section:{slugify(node.title) or (node.tag_id or 'untitled')}"
        props = {
            "title": node.title,
            "level": node.level,
            "childCount": node.child_count(),
            "depth": depth,
            "isParent": node.child_count() > 0,
        }
        if node.tag_id:
            props["anchorId"] = node.tag_id
        sec_node = ensure_node(sec_id, "Section", props)
        if parent_id:
            edges.append(
                Edge(
                    source=parent_id,
                    target=sec_node.id,
                    type="HAS_SECTION",
                    properties={"hierarchical": True},
                )
            )
        else:
            edges.append(
                Edge(
                    source=root.id,
                    target=sec_node.id,
                    type="HAS_SECTION",
                    properties={"hierarchical": True},
                )
            )
        for child in node.children:
            register_outline(child, sec_node.id, depth + 1)

    for r in outline_roots:
        register_outline(r, parent_id=None, depth=0)

    # Attach table data to outline-based sections where anchorId is available
    for n in list(nodes.values()):
        if n.type == "Section" and n.properties.get("anchorId"):
            start = soup.find(id=n.properties.get("anchorId"))
            if start is not None:
                content_nodes = next_sibling_section_content(start)
                tables = extract_tables(content_nodes)
                if tables:
                    n.properties["tables"] = tables

    def iter_outline(nodes_: List[SectionOutline]):
        for n in nodes_:
            yield n
            for c in iter_outline(n.children):
                yield c

    parents_ = [n for n in iter_outline(outline_roots) if n.child_count() > 0]

    def pack_outline(n: SectionOutline) -> Dict[str, object]:
        return {
            "title": n.title,
            "level": n.level,
            "anchorId": n.tag_id,
            "sectionId": f"section:{slugify(n.title) or (n.tag_id or 'untitled')}",
        }

    for p in parents_:
        outline_summary.append(
            {
                "parent": pack_outline(p),
                "children": [pack_outline(c) for c in p.children],
            }
        )

    level_defs = [
        {
            "id": "level:foundation",
            "title": "Foundation",
            "match": ["Foundation Level", "Foundation"],
        },
        {
            "id": "level:diploma",
            "title": "Diploma",
            "match": ["Diploma Level", "Diploma"],
        },
        {
            "id": "level:diploma_programming",
            "title": "Diploma - Programming",
            "match": ["Diploma in Programming", "Programming Diploma"],
        },
        {
            "id": "level:diploma_ds",
            "title": "Diploma - Data Science",
            "match": [
                "Diploma in Data Science",
                "Data Science Diploma",
                "Diploma DS",
                "DS Diploma",
            ],
        },
        {
            "id": "level:bsc",
            "title": "BSc Degree",
            "match": ["BSc Degree Level", "BSc Level", "BSc Degree"],
        },
        {
            "id": "level:bs",
            "title": "BS Degree",
            "match": ["BS Degree Level", "BS Level", "BS Degree"],
        },
        {"id": "level:degree", "title": "Degree", "match": ["Degree Level", "Degree"]},
    ]

    def classify_heading(text: str) -> Optional[str]:
        t = normalize_whitespace(text)
        best_score = 0
        best_id: Optional[str] = None
        for ld in level_defs:
            for pattern in ld["match"]:
                score = fuzz.token_set_ratio(t, pattern)
                if score > best_score:
                    best_score = score
                    best_id = ld["id"]
        return best_id if best_score >= 70 else None

    current_level: Optional[str] = None
    heading_level_ctx: Dict[int, Optional[str]] = {}
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
            heading_level_ctx[id(el)] = current_level
            hid = classify_heading(text_of(el))
            if hid:
                current_level = hid

    for label, header in matched.items():
        content_nodes = next_sibling_section_content(header)
        bullets = extract_bullets(content_nodes)
        paras = extract_paragraphs(content_nodes)
        fields = parse_labeled_fields(content_nodes)

        sec_id = f"section:{re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')}"
        sec_node = ensure_node(
            sec_id,
            "Section",
            {"title": label, "bullets": bullets, "paragraphs": paras, "fields": fields},
        )
        ctx = heading_level_ctx.get(id(header))
        if ctx:
            edges.append(
                Edge(source=ctx, target=sec_node.id, type="HAS_SECTION", properties={})
            )
        else:
            edges.append(
                Edge(
                    source=root.id,
                    target=sec_node.id,
                    type="HAS_SECTION",
                    properties={},
                )
            )

    courses_by_level: Dict[str, List[Dict[str, str]]] = defaultdict(list)
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
        if el.name == "a" and el.has_attr("href"):
            label = text_of(el)
            href = el.get("href", "")
            cid = guess_course_id_from_text(label) or guess_course_id_from_href(href)
            if cid:
                key = current_level or "level:unknown"
                courses_by_level[key].append(
                    {"courseId": cid, "label": label, "href": href}
                )

    for level_key, items in courses_by_level.items():
        if not items:
            continue
        if level_key != "level:unknown":
            lnode = ensure_node(
                level_key, "Level", {"title": level_key.split(":", 1)[-1].upper()}
            )
            edges.append(
                Edge(source=root.id, target=lnode.id, type="HAS_LEVEL", properties={})
            )
            list_node = ensure_node(
                f"list:courses:{level_key}",
                "Collection",
                {"title": f"Courses - {lnode.properties.get('title')}", "items": items},
            )
            edges.append(
                Edge(
                    source=lnode.id,
                    target=list_node.id,
                    type="HAS",
                    properties={"what": "courses"},
                )
            )
        else:
            list_node = ensure_node(
                "list:courses", "Collection", {"title": "Courses", "items": items}
            )
            edges.append(
                Edge(
                    source=root.id,
                    target=list_node.id,
                    type="HAS",
                    properties={"what": "courses"},
                )
            )

    return {
        "nodes": [n.__dict__ for n in nodes.values()],
        "edges": [e.__dict__ for e in edges],
        "meta": {"outlineSummary": outline_summary},
    }
