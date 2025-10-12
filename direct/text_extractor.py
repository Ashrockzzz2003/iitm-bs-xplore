#!/usr/bin/env python3
"""
Text Extraction Module

Extracts clean plain text content from HTML pages, removing all tags,
scripts, and styles while preserving semantic structure.
"""

import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup, Tag, NavigableString


class TextExtractor:
    """Extracts clean text content from HTML."""
    
    def __init__(self):
        """Initialize the text extractor."""
        self.soup = None
    
    def extract_text_from_html(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Extract clean text content from HTML.
        
        Args:
            html: Raw HTML content
            url: Source URL for context
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            self.soup = BeautifulSoup(html, "lxml")
            
            # Remove unwanted elements
            self._remove_unwanted_elements()
            
            # Extract text content
            text_content = self._extract_text_content()
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text_content)
            
            # Extract metadata
            metadata = self._extract_metadata(url)
            
            return {
                "text": cleaned_text,
                "metadata": metadata,
                "word_count": len(cleaned_text.split()),
                "char_count": len(cleaned_text)
            }
            
        except Exception as e:
            return {
                "text": f"Error extracting text: {str(e)}",
                "metadata": {"error": str(e)},
                "word_count": 0,
                "char_count": 0
            }
    
    def _remove_unwanted_elements(self):
        """Remove script, style, and other unwanted elements."""
        if not self.soup:
            return
            
        # Remove script and style elements
        for element in self.soup(["script", "style", "meta", "link", "noscript"]):
            element.decompose()
        
        # Remove comments
        from bs4 import Comment
        comments = self.soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
    
    def _extract_text_content(self) -> str:
        """Extract text content while preserving structure."""
        if not self.soup:
            return ""
        
        # Find the main content area
        main_content = self._find_main_content()
        
        if main_content:
            return self._extract_text_from_element(main_content)
        else:
            # Fallback to body or entire document
            body = self.soup.find("body")
            if body:
                return self._extract_text_from_element(body)
            else:
                return self._extract_text_from_element(self.soup)
    
    def _find_main_content(self) -> Optional[Tag]:
        """Find the main content area of the page."""
        if not self.soup:
            return None
        
        # Common selectors for main content
        main_selectors = [
            "main",
            "[role='main']",
            ".main-content",
            ".content",
            "#content",
            ".container",
            ".wrapper"
        ]
        
        for selector in main_selectors:
            element = self.soup.select_one(selector)
            if element:
                return element
        
        # If no main content found, return None
        return None
    
    def _extract_text_from_element(self, element: Tag) -> str:
        """Extract text from a specific element while preserving structure."""
        text_parts = []
        
        for child in element.descendants:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    text_parts.append(text)
            elif isinstance(child, Tag):
                # Add line breaks for block elements
                if child.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']:
                    text_parts.append('\n')
                # Add spaces for inline elements
                elif child.name in ['span', 'strong', 'em', 'b', 'i']:
                    text_parts.append(' ')
        
        return ' '.join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize the extracted text."""
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Clean up common HTML artifacts
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#39;', "'", text)
        
        return text
    
    def _extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from the HTML document."""
        if not self.soup:
            return {"url": url}
        
        metadata = {"url": url}
        
        # Extract title
        title_tag = self.soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Extract meta description
        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["description"] = meta_desc.get("content").strip()
        
        # Extract headings for structure
        headings = []
        for i in range(1, 7):
            for heading in self.soup.find_all(f"h{i}"):
                heading_text = heading.get_text().strip()
                if heading_text:
                    headings.append({
                        "level": i,
                        "text": heading_text
                    })
        
        if headings:
            metadata["headings"] = headings
        
        # Extract page type based on URL patterns
        if "/academics.html" in url:
            metadata["page_type"] = "academics"
        elif "/course_pages/" in url:
            metadata["page_type"] = "course"
            # Extract course ID from URL
            course_match = re.search(r'/([A-Z]{2,4}\d{4})\.html', url)
            if course_match:
                metadata["course_id"] = course_match.group(1)
        else:
            metadata["page_type"] = "other"
        
        return metadata


def extract_text_from_url(url: str, html: str) -> Dict[str, Any]:
    """
    Convenience function to extract text from a URL and HTML.
    
    Args:
        url: Source URL
        html: HTML content
        
    Returns:
        Dict containing extracted text and metadata
    """
    extractor = TextExtractor()
    return extractor.extract_text_from_html(html, url)


if __name__ == "__main__":
    # Test the extractor
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python text_extractor.py <html_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    result = extract_text_from_url("test.html", html_content)
    print(f"Extracted {result['word_count']} words, {result['char_count']} characters")
    print(f"Title: {result['metadata'].get('title', 'N/A')}")
    print(f"First 200 characters: {result['text'][:200]}...")
