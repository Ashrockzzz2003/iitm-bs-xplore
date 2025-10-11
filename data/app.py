#!/usr/bin/env python3
"""
IITM BS Xplore - Main Application

Main entry point for the knowledge graph extraction and visualization tool.
"""

import logging
from typing import List, Dict, Any, Optional

from src.processors.url_processor import process_url_input
from src.processors.file_processor import process_file_inputs
from src.utils.argument_parser import parse_arguments
from src.utils.output_handler import write_output
from src.xplore import merge_graphs
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


def process_multiple_data_sources(data_sources: List[str]) -> Dict[str, Any]:
    """Process multiple data sources and create a unified knowledge graph.
    
    Args:
        data_sources: List of URLs to process
        
    Returns:
        Dict: Unified knowledge graph with proper hierarchy
    """
    all_graphs = []
    program_info = {}
    
    for source in data_sources:
        print(f"\n🔄 Processing data source: {source}")
        
        # Parse the URL to determine program type
        if "/ds/" in source:
            program_type = "DS"
            program_name = "Data Science"
        elif "/es/" in source:
            program_type = "ES" 
            program_name = "Electronics Systems"
        else:
            print(f"⚠️  Unknown program type for {source}, skipping...")
            continue
            
        # Process the source
        try:
            graph, parser_used = process_url_input(source, False)
            all_graphs.append(graph)
            program_info[program_type] = {
                "name": program_name,
                "url": source,
                "parser": parser_used,
                "graph": graph
            }
            print(f"✅ Successfully processed {program_name} program")
        except Exception as e:
            print(f"❌ Failed to process {source}: {e}")
            continue
    
    if not all_graphs:
        raise SystemExit("No valid data sources could be processed")
    
    # Create unified knowledge graph with proper hierarchy
    unified_kg = create_unified_program_hierarchy(program_info)
    
    return unified_kg


def create_unified_program_hierarchy(program_info: Dict[str, Dict]) -> Dict[str, Any]:
    """Create a unified knowledge graph with IITM BS -> DS/ES hierarchy.
    
    Args:
        program_info: Dictionary containing program information
        
    Returns:
        Dict: Unified knowledge graph
    """
    # Create the main IITM BS program node
    main_program = {
        "id": "program:IITM_BS",
        "type": "Program", 
        "properties": {
            "title": "IITM Bachelor of Science",
            "description": "IITM Online Bachelor of Science Program",
            "institution": "Indian Institute of Technology Madras",
            "programs": list(program_info.keys())
        }
    }
    
    nodes = [main_program]
    edges = []
    meta = {
        "unified_program": True,
        "main_program": "IITM_BS",
        "sub_programs": {}
    }
    
    # Process each sub-program
    for program_type, info in program_info.items():
        sub_program = {
            "id": f"program:{program_type}",
            "type": "SubProgram",
            "properties": {
                "title": info["name"],
                "program_type": program_type,
                "source_url": info["url"],
                "parser_used": info["parser"]
            }
        }
        nodes.append(sub_program)
        
        # Connect sub-program to main program
        edges.append({
            "source": "program:IITM_BS",
            "target": f"program:{program_type}",
            "type": "HAS_SUBPROGRAM",
            "properties": {"program_type": program_type}
        })
        
        # Process the sub-program's graph
        sub_graph = info["graph"]
        sub_nodes = sub_graph.get("nodes", [])
        sub_edges = sub_graph.get("edges", [])
        
        # Update node IDs to include program prefix
        for node in sub_nodes:
            if node.get("type") == "Program":
                # Skip the original program node, we have our own
                continue
            # Add program prefix to node ID
            original_id = node["id"]
            node["id"] = f"{program_type}:{original_id}"
            node["properties"]["program"] = program_type
            nodes.append(node)
        
        # Update edge references and add program prefix
        for edge in sub_edges:
            source = edge["source"]
            target = edge["target"]
            
            # Add program prefix to node references
            if not source.startswith("program:"):
                edge["source"] = f"{program_type}:{source}"
            if not target.startswith("program:"):
                edge["target"] = f"{program_type}:{target}"
            
            edges.append(edge)
        
        # Store sub-program metadata
        meta["sub_programs"][program_type] = {
            "name": info["name"],
            "url": info["url"],
            "parser": info["parser"],
            "node_count": len(sub_nodes),
            "edge_count": len(sub_edges)
        }
    
    # Add total counts to metadata
    meta["total_nodes"] = len(nodes)
    meta["total_edges"] = len(edges)
    meta["program_count"] = len(program_info)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": meta
    }


def upload_to_neo4j(kg: Dict[str, Any], args) -> bool:
    """Upload knowledge graph to Neo4j if enabled.
    
    Args:
        kg: Knowledge graph data
        args: Command line arguments
        
    Returns:
        bool: True if upload successful, False otherwise
    """
    if not hasattr(args, 'neo4j') or not args.neo4j:
        return True
    
    logger = logging.getLogger(__name__)
    
    try:
        uploader = create_neo4j_uploader(
            uri=getattr(args, 'neo4j_uri', 'neo4j://127.0.0.1:7687'),
            username=getattr(args, 'neo4j_username', 'neo4j'),
            password=getattr(args, 'neo4j_password', 'password'),
            database=getattr(args, 'neo4j_database', 'neo4j'),
            clear_database=getattr(args, 'neo4j_clear', False)
        )
        
        if uploader.upload_kg(kg):
            logger.info("✅ Knowledge graph uploaded to Neo4j successfully!")
            return True
        else:
            logger.error("❌ Failed to upload knowledge graph to Neo4j")
            return False
            
    except Exception as e:
        logger.error(f"❌ Neo4j upload error: {e}")
        return False
    finally:
        if 'uploader' in locals():
            uploader.disconnect()


def main() -> None:
    """Main entry point for the application.
    
    This function orchestrates the entire knowledge graph extraction process:
    1. Parse command line arguments
    2. Process input sources (URLs/files) or multiple data sources
    3. Merge multiple graphs if needed
    4. Add metadata and write output
    5. Upload to Neo4j if enabled
    """
    args = parse_arguments()
    
    # Check if multiple data sources are provided
    if args.data_sources:
        print("🚀 Processing multiple data sources for unified hierarchy...")
        kg = process_multiple_data_sources(args.data_sources)
        parser_used = "unified"
    else:
        # Original single source processing
        graphs, parser_used = process_inputs(args)

        # Validate that at least one input source was provided
        if not graphs:
            raise SystemExit(
                "No input provided. Use --url, --academics, --course-files, --generic, or --data-sources"
            )

        # Merge all graphs into a single knowledge graph
        kg = merge_graphs(graphs)
        
        # Add parser metadata for tracking and debugging
        add_parser_metadata(kg, parser_used)
    
    # Write the final knowledge graph to output
    write_output(kg, args.output, args.out_dir, parser_used)
    
    # Upload to Neo4j if enabled
    if hasattr(args, 'neo4j') and args.neo4j:
        upload_to_neo4j(kg, args)


if __name__ == "__main__":
    main()