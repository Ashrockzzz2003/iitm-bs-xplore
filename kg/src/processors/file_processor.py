"""
File Processing Module

Handles processing of local HTML files and file-based inputs.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from src.xplore import (
    parse_academics_html,
    parse_course_html,
    parse_generic_html,
)


def process_file_inputs(academics_file: Optional[str] = None,
                       course_files: Optional[List[str]] = None,
                       generic_files: Optional[List[str]] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Process file inputs and return graphs and parser type.
    
    This function handles local file processing for backward compatibility.
    It reads HTML files from disk and parses them using the appropriate parser.
    """
    graphs = []
    parser_used = None

    # Process academics file (program structure and course listings)
    if academics_file:
        html = Path(academics_file).read_text(encoding="utf-8", errors="ignore")
        graphs.append(
            parse_academics_html(html, base_url=str(Path(academics_file).parent))
        )
        parser_used = "academics"

    # Process course files (individual course detail pages)
    if course_files:
        for cf in course_files:
            html = Path(cf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(parse_course_html(html, source_path=cf))
        parser_used = "course"

    # Process generic files (any other HTML documents)
    if generic_files:
        for gf in generic_files:
            html = Path(gf).read_text(encoding="utf-8", errors="ignore")
            graphs.append(
                parse_generic_html(
                    html, root_id=f"doc:{Path(gf).stem}", root_title=Path(gf).name
                )
            )
        parser_used = "generic"

    return graphs, parser_used
