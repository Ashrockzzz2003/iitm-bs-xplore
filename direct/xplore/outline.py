import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag
from .utils import text_of


@dataclass
class SectionOutline:
    """Represents a section in the document outline hierarchy.
    
    This class models the hierarchical structure of a document by organizing
    headings and their content into a tree-like structure.
    """
    title: str
    level: int
    tag_id: Optional[str]
    tag_name: str
    children: List["SectionOutline"]

    def child_count(self) -> int:
        """Return the number of direct children in this section."""
        return len(self.children)


def heading_level_of(el: Tag) -> Optional[int]:
    """Determine the heading level of an HTML element.
    
    This function identifies heading levels for both standard HTML headings
    and elements that are styled to look like headings.
    """
    name = (el.name or "").lower()
    
    # Standard HTML headings (h1-h6)
    if re.fullmatch(r"h[1-6]", name):
        return int(name[1])
    
    # Check for heading classes (h1, h2, etc.)
    classes = " ".join(el.get("class", []))
    m = re.search(r"\bh([1-6])\b", classes)
    if m:
        return int(m.group(1))
    
    # Styled elements that act as headings (default to level 2)
    if name in ("p", "div", "span") and (
        (
            "font-weight-600" in classes
            and ("text-dark" in classes or "text-secondary" in classes)
        )
        or (el.has_attr("id") and re.match(r"AC\d+", el.get("id", "")))
    ):
        return 2
    return None


def build_outline(soup: BeautifulSoup) -> List[SectionOutline]:
    """Build a hierarchical outline from HTML soup.
    
    This function creates a tree structure representing the document's
    heading hierarchy, filtering out invalid headings and organizing
    them into a proper outline structure.
    """
    def is_valid_heading_title(title: str) -> bool:
        """Check if a heading title is valid for inclusion in the outline.
        
        Filters out titles that are:
        - Empty or too short
        - Pure numbers or currency amounts
        - Metric patterns (credits, courses, etc.)
        """
        t = (title or "").strip()
        if not t:
            return False
        if not re.search(r"[A-Za-z]", t):
            return False
        if re.fullmatch(r"[₹$€\d\s,\-–—\*]+", t):
            return False
        if len(t) < 4 and " " not in t:
            return False
        metric_pattern = re.compile(
            r"^\s*(?:[₹$€]?[\d,]+(?:\s*[\-–—]\s*[₹$€]?[\d,]+)?)(?:\s*(?:credits?|courses?|projects?|years?))?(?:\s*\*?)\s*$",
            re.IGNORECASE,
        )
        if metric_pattern.fullmatch(t):
            return False
        return True

    candidates: List[Tag] = []
    for el in soup.find_all(True):
        lvl = heading_level_of(el)
        if lvl is not None:
            candidates.append(el)
    roots: List[SectionOutline] = []
    stack: List[SectionOutline] = []
    prev_title_by_level: Dict[int, str] = {}
    for h in candidates:
        level = heading_level_of(h) or 6
        title = text_of(h)
        if not is_valid_heading_title(title):
            continue
        if prev_title_by_level.get(level) == title:
            continue
        prev_title_by_level[level] = title
        node = SectionOutline(
            title=title,
            level=level,
            tag_id=h.get("id"),
            tag_name=h.name or "",
            children=[],
        )
        while stack and stack[-1].level >= level:
            stack.pop()
        if not stack:
            roots.append(node)
        else:
            stack[-1].children.append(node)
        stack.append(node)
    return roots
