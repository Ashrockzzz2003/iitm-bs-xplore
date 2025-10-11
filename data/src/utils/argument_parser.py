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
        "--output", type=str, help="Path to write KG JSON (default: auto-generated filename in out-dir)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/kg",
        help="Directory for generated JSON files when a bare filename is given",
    )
    parser.add_argument(
        "--outline-summary",
        action="store_true",
        help="Print logical summary: each parent section and its immediate children",
    )
    parser.add_argument(
        "--data-sources",
        type=str,
        nargs="*",
        help="Multiple data sources (URLs) to process and create unified hierarchy",
        default=None,
    )
    
    # Neo4j integration options
    neo4j_group = parser.add_argument_group('Neo4j Integration')
    neo4j_group.add_argument(
        "--neo4j",
        action="store_true",
        help="Upload knowledge graph to Neo4j database"
    )
    neo4j_group.add_argument(
        "--neo4j-uri",
        type=str,
        default="neo4j://127.0.0.1:7687",
        help="Neo4j URI (default: neo4j://127.0.0.1:7687)"
    )
    neo4j_group.add_argument(
        "--neo4j-username",
        type=str,
        default="neo4j",
        help="Neo4j username (default: neo4j)"
    )
    neo4j_group.add_argument(
        "--neo4j-password",
        type=str,
        default="password",
        help="Neo4j password (default: password)"
    )
    neo4j_group.add_argument(
        "--neo4j-database",
        type=str,
        default="neo4j",
        help="Neo4j database name (default: neo4j)"
    )
    neo4j_group.add_argument(
        "--neo4j-clear",
        action="store_true",
        help="Clear Neo4j database before uploading"
    )
    
    return parser.parse_args()
