from typing import Optional
import re
from bs4 import Tag


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def text_of(node: Optional[Tag]) -> str:
    if not node:
        return ""
    return normalize_whitespace(node.get_text(" ", strip=True))
