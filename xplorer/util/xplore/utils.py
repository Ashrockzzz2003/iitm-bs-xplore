from typing import Optional
import re
from bs4 import Tag


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text by collapsing multiple spaces into single spaces."""
    return re.sub(r"\s+", " ", text or "").strip()


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug by replacing non-alphanumeric characters with underscores."""
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def text_of(node: Optional[Tag]) -> str:
    """Extract and normalize text content from a BeautifulSoup Tag element.
    
    This function safely extracts text from HTML elements and normalizes
    whitespace for consistent text processing.
    """
    if not node:
        return ""
    return normalize_whitespace(node.get_text(" ", strip=True))
