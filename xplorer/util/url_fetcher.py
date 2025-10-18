#!/usr/bin/env python3
"""
URL Fetcher Module

Fetches HTML content from URLs and extracts course URLs from academics pages.
Reuses logic from the main application's URL processor.
"""

import os
import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

# Import utilities from the main application
from .xplore.academics import (
    classify_heading,
    guess_course_id_from_href,
    guess_course_id_from_text,
)
from .xplore.utils import text_of


class URLFetcher:
    """Fetches URLs and extracts course links from academics pages."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the URL fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from a URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            Exception: If fetching fails
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch URL {url}: {e}")

    def extract_course_urls_from_academics(
        self, html: str, base_url: str
    ) -> List[Dict[str, str]]:
        """
        Extract course URLs from academics page HTML.

        This reuses the logic from the main application's URL processor.

        Args:
            html: HTML content of academics page
            base_url: Base URL for resolving relative links

        Returns:
            List of course URL dictionaries with metadata
        """
        soup = BeautifulSoup(html, "lxml")
        course_urls = []
        seen_courses = set()  # To avoid duplicates
        current_level = None

        # Iterate through all HTML elements to find headings and course links
        for el in soup.descendants:
            if not isinstance(el, Tag):
                continue
            name = el.name or ""
            classes = " ".join(el.get("class", []))

            # Detect heading-like elements (h1-h6, styled divs, etc.)
            # This helps us track the current level/section context
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

            # Update current level context when we find a heading
            if is_heading_like:
                hid = classify_heading(text_of(el))
                if hid:
                    current_level = hid
                continue

            # Check for regular <a> tags with href (course links)
            if el.name == "a" and el.has_attr("href"):
                label = text_of(el)
                href = el.get("href", "")
                cid = guess_course_id_from_text(label) or guess_course_id_from_href(
                    href
                )

                # Handle "coming soon" links - extract course ID from table row context
                if not cid and "coming-soon.html" in href:
                    # Look for course ID in the same table row
                    row = el.find_parent("tr")
                    if row:
                        row_text = text_of(row)
                        cid = guess_course_id_from_text(row_text)

                # Add course to list if we found a valid course ID and haven't seen it before
                if cid and cid not in seen_courses:
                    # Convert relative URLs to absolute URLs
                    full_url = urljoin(base_url, href)
                    # Only include course pages, not other links (support both /ds/ and /es/)
                    if (
                        "/course_pages/" in full_url
                        or "/ds/" in full_url
                        or "/es/" in full_url
                    ):
                        course_urls.append(
                            {
                                "courseId": cid,
                                "label": label,
                                "href": full_url,
                                "level": current_level or "unknown",
                            }
                        )
                        seen_courses.add(cid)

            # Check for elements with data-url attribute (like table rows)
            elif el.has_attr("data-url"):
                data_url = el.get("data-url", "")
                # Extract course ID from the data-url
                cid = guess_course_id_from_href(data_url)
                if cid and cid not in seen_courses:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, data_url)
                    # Only include course pages, not other links (support both /ds/ and /es/)
                    if (
                        "/course_pages/" in full_url
                        or "/ds/" in full_url
                        or "/es/" in full_url
                    ):
                        # Try to get a meaningful label from the element
                        label = text_of(el)
                        if not label or len(label.strip()) < 3:
                            # If no good label, use the course ID
                            label = cid
                        course_urls.append(
                            {
                                "courseId": cid,
                                "label": label,
                                "href": full_url,
                                "level": current_level or "unknown",
                            }
                        )
                        seen_courses.add(cid)

        return course_urls

    def get_all_urls_for_program(self, program: str) -> List[Dict[str, Any]]:
        """
        Get all URLs for a specific program (DS or ES).

        Args:
            program: Program type ('ds' or 'es')

        Returns:
            List of URL dictionaries with metadata
        """
        if program.lower() not in ["ds", "es"]:
            raise ValueError("Program must be 'ds' or 'es'")

        program_upper = program.upper()
        academics_url = f"https://study.iitm.ac.in/{program.lower()}/academics.html"

        print(f"Fetching academics page for {program_upper}...")
        html = self.fetch_html(academics_url)

        print(f"Extracting course URLs from {program_upper} academics page...")
        course_urls = self.extract_course_urls_from_academics(html, academics_url)

        # Create list of all URLs to process
        all_urls = []

        # Add academics page
        all_urls.append(
            {
                "url": academics_url,
                "program": program_upper,
                "type": "academics",
                "level": "main",
            }
        )

        # Add course pages
        for course_info in course_urls:
            all_urls.append(
                {
                    "url": course_info["href"],
                    "program": program_upper,
                    "type": "course",
                    "course_id": course_info["courseId"],
                    "label": course_info["label"],
                    "level": course_info["level"],
                }
            )

        print(f"Found {len(course_urls)} course URLs for {program_upper}")
        return all_urls

    def get_all_urls_for_programs(self, programs: List[str]) -> List[Dict[str, Any]]:
        """
        Get all URLs for multiple programs.

        Args:
            programs: List of program types (e.g., ['ds', 'es'])

        Returns:
            List of all URL dictionaries with metadata
        """
        all_urls = []

        for program in programs:
            try:
                program_urls = self.get_all_urls_for_program(program)
                all_urls.extend(program_urls)
            except Exception as e:
                print(f"Warning: Failed to process {program.upper()} program: {e}")
                continue

        return all_urls

    def close(self):
        """Close the session."""
        self.session.close()


def get_urls_for_programs(programs: List[str]) -> List[Dict[str, Any]]:
    """
    Convenience function to get URLs for multiple programs.

    Args:
        programs: List of program types (e.g., ['ds', 'es'])

    Returns:
        List of all URL dictionaries with metadata
    """
    fetcher = URLFetcher()
    try:
        return fetcher.get_all_urls_for_programs(programs)
    finally:
        fetcher.close()


if __name__ == "__main__":
    # Test the URL fetcher
    import sys

    if len(sys.argv) < 2:
        print("Usage: python url_fetcher.py <program1> [program2] ...")
        print("Example: python url_fetcher.py ds es")
        sys.exit(1)

    programs = sys.argv[1:]
    print(f"Fetching URLs for programs: {', '.join(programs)}")

    urls = get_urls_for_programs(programs)

    print(f"\nTotal URLs found: {len(urls)}")
    print("\nURLs by type:")

    by_type = {}
    for url_info in urls:
        url_type = url_info["type"]
        if url_type not in by_type:
            by_type[url_type] = 0
        by_type[url_type] += 1

    for url_type, count in by_type.items():
        print(f"  {url_type}: {count}")

    print(f"\nFirst 5 URLs:")
    for i, url_info in enumerate(urls[:5]):
        print(f"  {i+1}. {url_info['url']} ({url_info['type']})")
