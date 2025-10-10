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
    """Add parser information to knowledge graph metadata.
    
    This helps track which parser was used to generate the knowledge graph,
    which is useful for debugging and understanding the data source.
    """
    if "meta" not in kg:
        kg["meta"] = {}
    if parser_used:
        kg["meta"]["parser_used"] = parser_used


def process_inputs(args) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Process all input sources and return graphs and parser type.
    
    This function handles both URL and file inputs, automatically detecting
    the appropriate parser for URLs and using explicit parsers for files.
    """
    graphs = []
    parser_used = None

    # Handle URL input with automatic parser detection
    # URLs are processed first as they're the primary input method
    if args.url:
        graph, parser_type = process_url_input(args.url, args.outline_summary)
        graphs.append(graph)
        parser_used = parser_type

    # Handle file inputs (backward compatibility)
    # Files are processed after URLs to maintain backward compatibility
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
    """Main entry point for the application.
    
    This function orchestrates the entire knowledge graph extraction process:
    1. Parse command line arguments
    2. Process input sources (URLs/files)
    3. Merge multiple graphs if needed
    4. Add metadata and write output
    """
    args = parse_arguments()
    graphs, parser_used = process_inputs(args)

    # Validate that at least one input source was provided
    if not graphs:
        raise SystemExit(
            "No input provided. Use --url, --academics, --course-files, or --generic"
        )

    # Merge all graphs into a single knowledge graph
    kg = merge_graphs(graphs)
    
    # Add parser metadata for tracking and debugging
    add_parser_metadata(kg, parser_used)
    
    # Write the final knowledge graph to output
    write_output(kg, args.output, args.out_dir, parser_used)


if __name__ == "__main__":
    main()