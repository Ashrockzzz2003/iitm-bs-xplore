#!/usr/bin/env python3
"""
IITM BS Xplore - Main Application

Main entry point for the knowledge graph extraction and visualization tool.
"""

import sys
from typing import List, Dict, Any, Optional

from src.processors.url_processor import process_url_input
from src.processors.file_processor import process_file_inputs
from src.utils.argument_parser import parse_arguments
from src.utils.output_handler import write_output
from src.utils.outline_printer import print_outline_summary
from xplore import merge_graphs


def add_parser_metadata(kg: Dict[str, Any], parser_used: Optional[str]) -> None:
    """Add parser information to knowledge graph metadata."""
    if "meta" not in kg:
        kg["meta"] = {}
    if parser_used:
        kg["meta"]["parser_used"] = parser_used


def process_inputs(args) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Process all input sources and return graphs and parser type."""
    graphs = []
    parser_used = None

    # Handle URL input with automatic parser detection
    if args.url:
        graph, parser_type = process_url_input(args.url, args.outline_summary)
        graphs.append(graph)
        parser_used = parser_type

    # Handle file inputs (backward compatibility)
    file_graphs, file_parser = process_file_inputs(
        academics_file=args.academics,
        course_files=args.course_files,
        generic_files=args.generic
    )
    graphs.extend(file_graphs)
    if file_parser:
        parser_used = file_parser

    return graphs, parser_used


def main() -> None:
    """Main entry point for the application."""
    args = parse_arguments()
    graphs, parser_used = process_inputs(args)

    if not graphs:
        raise SystemExit(
            "No input provided. Use --url, --academics, --course-files, or --generic"
        )

    kg = merge_graphs(graphs)
    add_parser_metadata(kg, parser_used)
    write_output(kg, args.output, args.out_dir, parser_used)


if __name__ == "__main__":
    main()