"""
Argument Parser Module

Handles command line argument parsing for the application.
"""

import argparse
from typing import List, Optional


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for dual hierarchical knowledge graph system."""
    parser = argparse.ArgumentParser(
        description="Dual Hierarchical Knowledge Graph Generator - Creates separate course and generic knowledge graphs"
    )
    parser.add_argument(
        "--data-sources",
        type=str,
        nargs="+",
        help="URLs to process for dual KG generation (required)",
        required=True,
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="dual_hierarchical_kg",
        help="Base name for output files (default: dual_hierarchical_kg)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="outputs/kg",
        help="Directory for generated JSON files (default: outputs/kg)",
    )
    parser.add_argument(
        "--outline-summary",
        action="store_true",
        help="Print logical summary: each parent section and its immediate children",
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
        default="iitm2",
        help="Neo4j database name (default: iitm2)"
    )
    neo4j_group.add_argument(
        "--neo4j-clear",
        action="store_true",
        help="Clear Neo4j database before uploading"
    )
    
    return parser.parse_args()
