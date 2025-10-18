#!/usr/bin/env python3
"""
IITM BS Xplore - Main Application

Main entry point for the knowledge graph extraction and visualization tool.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from src.processors.dual_kg_processor import (
    process_multiple_urls_for_dual_kg,
)
from src.utils.argument_parser import parse_arguments
from src.utils.output_handler import write_output
from src.neo4j_integration import create_neo4j_uploader


def add_parser_metadata(kg: Dict[str, Any], parser_used: Optional[str]) -> None:
    """Add parser information to knowledge graph metadata.

    This helps track which parser was used to generate the knowledge graph,
    which is useful for debugging and understanding the data source.
    """
    if "meta" not in kg:
        kg["meta"] = {}
    if parser_used:
        kg["meta"]["parser_used"] = parser_used


def process_dual_kg_data_sources(
    data_sources: List[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process multiple data sources and create separate course and generic knowledge graphs.

    Args:
        data_sources: List of URLs to process

    Returns:
        Tuple of (course_kg, generic_kg)
    """
    print("🚀 Processing multiple data sources for dual KG generation...")

    # Process all URLs for dual KG
    course_kg, generic_kg = process_multiple_urls_for_dual_kg(data_sources, False)

    print(f"✅ Dual KG generation complete:")
    print(
        f"   📚 Course KG: {len(course_kg.get('nodes', []))} nodes, {len(course_kg.get('edges', []))} edges"
    )
    print(
        f"   🌐 Generic KG: {len(generic_kg.get('nodes', []))} nodes, {len(generic_kg.get('edges', []))} edges"
    )

    return course_kg, generic_kg


def upload_to_dual_neo4j_databases(
    course_kg: Dict[str, Any], generic_kg: Dict[str, Any], args
) -> bool:
    """Upload knowledge graphs to Neo4j with separate node labels for course and generic content.

    Args:
        course_kg: Course knowledge graph data
        generic_kg: Generic knowledge graph data
        args: Command line arguments

    Returns:
        bool: True if both uploads successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    success = True

    # Upload course KG with course-specific labels
    try:
        print("📚 Uploading course knowledge graph to Neo4j...")

        # Add course-specific labels to all nodes
        course_kg_labeled = add_kg_labels(course_kg, "Course")

        course_uploader = create_neo4j_uploader(
            uri=getattr(args, "neo4j_uri", "neo4j://127.0.0.1:7687"),
            username=getattr(args, "neo4j_username", "neo4j"),
            password=getattr(args, "neo4j_password", "password"),
            database=getattr(args, "neo4j_database", "iitm2"),
            clear_database=getattr(args, "neo4j_clear", False),
        )

        if course_uploader.upload_kg(course_kg_labeled):
            print("✅ Course knowledge graph uploaded successfully!")
        else:
            print("❌ Failed to upload course knowledge graph")
            success = False

    except Exception as e:
        print(f"❌ Course Neo4j upload error: {e}")
        success = False
    finally:
        if "course_uploader" in locals():
            course_uploader.disconnect()

    # Upload generic KG with generic-specific labels
    try:
        print("🌐 Uploading generic knowledge graph to Neo4j...")

        # Add generic-specific labels to all nodes
        generic_kg_labeled = add_kg_labels(generic_kg, "Generic")

        generic_uploader = create_neo4j_uploader(
            uri=getattr(args, "neo4j_uri", "neo4j://127.0.0.1:7687"),
            username=getattr(args, "neo4j_username", "neo4j"),
            password=getattr(args, "neo4j_password", "password"),
            database=getattr(args, "neo4j_database", "iitm2"),
            clear_database=False,  # Don't clear on second upload
        )

        if generic_uploader.upload_kg(generic_kg_labeled):
            print("✅ Generic knowledge graph uploaded successfully!")
        else:
            print("❌ Failed to upload generic knowledge graph")
            success = False

    except Exception as e:
        print(f"❌ Generic Neo4j upload error: {e}")
        success = False
    finally:
        if "generic_uploader" in locals():
            generic_uploader.disconnect()

    return success


def add_kg_labels(kg: Dict[str, Any], label_prefix: str) -> Dict[str, Any]:
    """Add Neo4j labels to distinguish between course and generic content.

    Args:
        kg: Knowledge graph data
        label_prefix: Prefix for the labels (Course/Generic)

    Returns:
        Knowledge graph with added labels
    """
    labeled_kg = kg.copy()

    # Add labels to all nodes
    for node in labeled_kg.get("nodes", []):
        if "labels" not in node:
            node["labels"] = []
        node["labels"].append(label_prefix)

    # Add labels to all edges
    for edge in labeled_kg.get("edges", []):
        if "labels" not in edge:
            edge["labels"] = []
        edge["labels"].append(f"{label_prefix}Relationship")

    return labeled_kg


def main() -> None:
    """Main entry point for the dual hierarchical knowledge graph system.

    This function orchestrates the dual KG extraction process:
    1. Parse command line arguments
    2. Process data sources for dual KG generation
    3. Create hierarchical course and generic knowledge graphs
    4. Write outputs and upload to Neo4j databases
    """
    args = parse_arguments()

    # Validate that data sources are provided
    if not args.data_sources:
        raise SystemExit(
            "Data sources are required. Use --data-sources to provide URLs."
        )

    print("🚀 Processing data sources for dual hierarchical KG generation...")
    course_kg, generic_kg = process_dual_kg_data_sources(args.data_sources)

    # Write both knowledge graphs
    write_output(course_kg, f"{args.output}_course", args.out_dir, "dual_course")
    write_output(generic_kg, f"{args.output}_generic", args.out_dir, "dual_generic")

    # Upload to Neo4j databases if enabled
    if hasattr(args, "neo4j") and args.neo4j:
        upload_to_dual_neo4j_databases(course_kg, generic_kg, args)


if __name__ == "__main__":
    main()
