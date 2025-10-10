import re
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from .types import Node, Edge
from .utils import text_of, normalize_whitespace
from .academics import (
    fuzzy_find_section,
    next_sibling_section_content,
    parse_labeled_fields,
    extract_bullets,
    extract_paragraphs,
)


def guess_course_id_from_text(text: str) -> Optional[str]:
    m = re.search(r"\b[A-Z]{2,4}\s?-?\d{3,4}\b", text or "")
    if m:
        return m.group(0).replace(" ", "").upper()
    return None


def parse_course_html(
    html: str, source_path: Optional[str] = None
) -> Dict[str, object]:
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
        "Course Credits",
        "Course Type",
        "Duration",
        "Evaluation Method",
        "Assessment Method",
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
        "Course Duration",
        "Course Evaluation",
        "Course Assessment",
        "Course Structure",
        "Course Structure & Assessments",
        "Structure",
        "Structure & Assessments",
    ]

    # Initialize attributes dictionary
    attr: Dict[str, object] = {}

    # Extract course details from briefDetails section
    brief_details = soup.find("div", class_="briefDetails")
    if brief_details:
        brief_text = text_of(brief_details)
        # Parse course details from the brief section
        brief_fields = {}
        
        # First try to split by common separators
        text_parts = re.split(r'(?=Course [A-Z][a-z]+:|Credits:|Type:|Pre-requisites:)', brief_text)
        
        for part in text_parts:
            part = part.strip()
            if ':' in part:
                # Split by colon and clean up
                if part.count(':') == 1:
                    key, value = part.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        brief_fields[key] = value
                else:
                    # Handle cases where there are multiple colons
                    lines = part.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ':' in line and line.count(':') == 1:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key and value:
                                brief_fields[key] = value
        
        # If the above didn't work well, try a more aggressive approach
        if not brief_fields:
            # Look for patterns like "Course ID: BSCS3001 Course Credits: 4"
            patterns = [
                r'Course ID:\s*([A-Z0-9]+)',
                r'Course Credits:\s*(\d+)',
                r'Course Type:\s*([^P]+?)(?=Pre-requisites:|$)',
                r'Pre-requisites:\s*([^$]+)',
                r'Duration:\s*([^$]+)',
                r'Evaluation Method:\s*([^$]+)',
                r'Assessment Method:\s*([^$]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, brief_text, re.IGNORECASE)
                if match:
                    if 'Course ID' in pattern:
                        brief_fields['Course ID'] = match.group(1)
                    elif 'Credits' in pattern:
                        brief_fields['Course Credits'] = match.group(1)
                    elif 'Type' in pattern:
                        brief_fields['Course Type'] = match.group(1).strip()
                    elif 'Pre-requisites' in pattern:
                        brief_fields['Pre-requisites'] = match.group(1).strip()
                    elif 'Duration' in pattern:
                        brief_fields['Duration'] = match.group(1).strip()
                    elif 'Evaluation' in pattern:
                        brief_fields['Evaluation Method'] = match.group(1).strip()
                    elif 'Assessment' in pattern:
                        brief_fields['Assessment Method'] = match.group(1).strip()
        
        if brief_fields:
            attr["Course Details"] = {"fields": brief_fields}

    # Look for other course metadata sections that might appear before weekly content
    course_meta_selectors = [
        "div.course-info",
        "div.course-meta", 
        "div.course-details",
        "div.course-header",
        "div.course-summary",
        "div.course-overview",
        "section.course-info",
        "section.course-meta",
        "section.course-details"
    ]
    
    for selector in course_meta_selectors:
        meta_section = soup.select_one(selector)
        if meta_section:
            meta_text = text_of(meta_section)
            if meta_text and len(meta_text.strip()) > 10:  # Only process substantial content
                meta_fields = {}
                lines = [line.strip() for line in meta_text.split('\n') if line.strip()]
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value and len(value) > 1:
                            meta_fields[key] = value
                
                if meta_fields:
                    section_name = selector.replace('div.', '').replace('section.', '').replace('-', ' ').title()
                    attr[section_name] = {"fields": meta_fields}

    field_sections = fuzzy_find_section(soup, possible_fields, min_score=65)
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
            prev = (
                attr["Details"].get("fields", {})
                if isinstance(attr["Details"], dict)
                else {}
            )
            merged = dict(prev)
            merged.update({k: v for k, v in table_fields.items() if k not in prev})
            attr["Details"]["fields"] = merged
        else:
            attr.setdefault("Details", {}).update(details)

    if not title and source_path:
        title = Path(source_path).stem.replace("_", " ")

    course_id = (
        code
        or guess_course_id_from_text(title)
        or f"COURSE:{hash(title) & 0xFFFFFFFF:08X}"
    ).upper()

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
        edges.append(
            Edge(source=node.id, target=f"course:{pc}", type="REQUIRES", properties={})
        )

    return {
        "nodes": [node.__dict__],
        "edges": [e.__dict__ for e in edges],
    }
