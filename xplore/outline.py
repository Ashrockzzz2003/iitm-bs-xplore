import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag
from .utils import text_of


@dataclass
class SectionOutline:
    title: str
    level: int
    tag_id: Optional[str]
    tag_name: str
    children: List["SectionOutline"]

    def child_count(self) -> int:
        return len(self.children)


def heading_level_of(el: Tag) -> Optional[int]:
    name = (el.name or "").lower()
    if re.fullmatch(r"h[1-6]", name):
        return int(name[1])
    classes = " ".join(el.get("class", []))
    m = re.search(r"\bh([1-6])\b", classes)
    if m:
        return int(m.group(1))
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
    def is_valid_heading_title(title: str) -> bool:
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
