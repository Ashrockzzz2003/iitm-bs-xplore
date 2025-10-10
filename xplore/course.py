import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from .types import Node, Edge
from .utils import text_of, normalize_whitespace
from .academics import fuzzy_find_section, next_sibling_section_content, parse_labeled_fields, extract_bullets, extract_paragraphs


def guess_course_id_from_text(text: str) -> Optional[str]:
    m = re.search(r"\b[A-Z]{2,4}\s?-?\d{3,4}\b", text or "")
    if m:
        return m.group(0).replace(" ", "").upper()
    return None


def parse_course_html(html: str, source_path: Optional[str] = None) -> Dict[str, object]:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    code = None
    h1 = soup.select_one("h1, .course-title, .tw\\:text-2xl, .tw\\:text-3xl")
    if h1:
        title = text_of(h1)
    if not title:
        if soup.title and soup.title.string:
            title = normalize_whitespace(soup.title.string)
    code = guess_course_id_from_text(title)

    if not code:
        for cand in [
            ("Code", 80),
            ("Course Code", 75),
            ("ID", 70),
        ]:
            m = fuzzy_find_section(soup, [cand[0]], min_score=cand[1])
            if m:
                content = next_sibling_section_content(next(iter(m.values())))
                fields = parse_labeled_fields(content)
                for k, v in fields.items():
                    maybe = guess_course_id_from_text(f"{k} {v}")
                    if maybe:
                        code = maybe
                        break
            if code:
                break

    possible_fields = [
        "Title",
        "Course Title",
        "Course Code",
        "Credits",
        "Prerequisites",
        "Pre-requisites",
        "Corequisites",
        "Co-requisites",
        "Description",
        "Syllabus",
        "Learning Outcomes",
        "Topics",
        "Assessment",
        "Grading Policy",
        "Instructors",
        "Level",
        "Term",
    ]

    field_sections = fuzzy_find_section(soup, possible_fields, min_score=65)
    attr: Dict[str, object] = {}
    for label, header in field_sections.items():
        content = next_sibling_section_content(header)
        fields = parse_labeled_fields(content)
        bullets = extract_bullets(content)
        paras = extract_paragraphs(content)
        composite: Dict[str, object] = {}
        if fields:
            composite["fields"] = fields
        if bullets:
            composite["bullets"] = bullets
        if paras:
            composite["paragraphs"] = paras
        if composite:
            attr[label] = composite

    for h in soup.find_all(re.compile(r"^h[2-4]$")):
        label = text_of(h)
        if not label or label in attr:
            continue
        content = next_sibling_section_content(h)
        fields = parse_labeled_fields(content)
        bullets = extract_bullets(content)
        paras = extract_paragraphs(content)
        composite: Dict[str, object] = {}
        if fields:
            composite["fields"] = fields
        if bullets:
            composite["bullets"] = bullets
        if paras:
            composite["paragraphs"] = paras
        if composite:
            attr[label] = composite

    table_fields: Dict[str, str] = {}
    for table in soup.find_all("table"):
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) == 2:
                k = text_of(cells[0])
                v = text_of(cells[1])
                if k and v and k not in table_fields:
                    table_fields[k] = v
    if table_fields:
        details = {"fields": table_fields}
        if "Details" in attr and isinstance(attr["Details"], dict):
            prev = attr["Details"].get("fields", {}) if isinstance(attr["Details"], dict) else {}
            merged = dict(prev)
            merged.update({k: v for k, v in table_fields.items() if k not in prev})
            attr["Details"]["fields"] = merged
        else:
            attr.setdefault("Details", {}).update(details)

    if not title and source_path:
        title = Path(source_path).stem.replace("_", " ")

    course_id = (code or guess_course_id_from_text(title) or f"COURSE:{hash(title) & 0xFFFFFFFF:08X}").upper()

    node = Node(
        id=f"course:{course_id}",
        type="Course",
        properties={
            "courseId": course_id,
            "title": title,
            **({} if not source_path else {"source": str(source_path)}),
            "attributes": attr,
        },
    )

    edges: List[Edge] = []
    prereq_texts: List[str] = []
    for k in ["Prerequisites", "Pre-requisites"]:
        v = attr.get(k)
        if isinstance(v, dict):
            prereq_texts.extend(v.get("bullets", []))
            if "fields" in v:
                prereq_texts.extend(v["fields"].values())
            prereq_texts.extend(v.get("paragraphs", []))
    prereq_codes: List[str] = []
    for t in prereq_texts:
        for m in re.findall(r"[A-Za-z]{2,4}\s?-?\d{3,4}", t):
            prereq_codes.append(m.replace(" ", "").upper())
    for pc in sorted(set(prereq_codes)):
        edges.append(Edge(source=node.id, target=f"course:{pc}", type="REQUIRES", properties={}))

    return {
        "nodes": [node.__dict__],
        "edges": [e.__dict__ for e in edges],
    }
