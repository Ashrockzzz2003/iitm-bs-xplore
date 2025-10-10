"""
Argument Parser Module

Handles command line argument parsing for the application.
"""

import argparse
from typing import List, Optional


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse HTML into a knowledge graph JSON with automatic parser detection"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL to fetch and parse (automatically detects parser)",
        required=False,
    )
    parser.add_argument(
        "--academics", type=str, help="Path to academics.html file", required=False
    )
    parser.add_argument(
        "--course-files",
        type=str,
        nargs="*",
        help="Paths to course HTML pages",
        default=None,
    )
    parser.add_argument(
        "--generic",
        type=str,
        nargs="*",
        help="Paths to generic HTML pages",
        default=None,
    )
    parser.add_argument(
        "--output", type=str, help="Path to write KG JSON (default: print)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs",
        help="Directory for generated JSON files when a bare filename is given",
    )
    parser.add_argument(
        "--outline-summary",
        action="store_true",
        help="Print logical summary: each parent section and its immediate children",
    )
    return parser.parse_args()
