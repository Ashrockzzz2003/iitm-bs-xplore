"""
Outline Printing Module

Handles printing logical summaries of document structure.
"""

from typing import List
from bs4 import BeautifulSoup
from src.xplore.outline import build_outline, SectionOutline


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
