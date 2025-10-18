"""
Output Handling Module

Handles writing knowledge graph data to files and printing output.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def print_kg_stats(kg: Dict[str, Any]) -> None:
    """Print knowledge graph statistics.
    
    Args:
        kg: Knowledge graph data
    """
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])
    
    # Count nodes by type
    node_types = {}
    for node in nodes:
        node_type = node.get("type", "Unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    # Count edges by type
    edge_types = {}
    for edge in edges:
        edge_type = edge.get("type", "Unknown")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    print("\n📊 Knowledge Graph Statistics:")
    print(f"   Total Nodes: {len(nodes)}")
    print(f"   Total Edges: {len(edges)}")
    
    if node_types:
        print("   Node Types:")
        for node_type, count in sorted(node_types.items()):
            print(f"     {node_type}: {count}")
    
    if edge_types:
        print("   Edge Types:")
        for edge_type, count in sorted(edge_types.items()):
            print(f"     {edge_type}: {count}")
    
    # Show parser info if available
    meta = kg.get("meta", {})
    if "parser_used" in meta:
        print(f"   Parser Used: {meta['parser_used']}")
    
    print()


def generate_default_filename(parser_used: Optional[str]) -> str:
    """Generate a default filename based on parser and timestamp.
    
    Args:
        parser_used: The parser that was used to generate the KG
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if parser_used:
        return f"kg_{parser_used}_{timestamp}.json"
    else:
        return f"kg_{timestamp}.json"


def write_output(
    kg: Dict[str, Any], 
    output_path: str, 
    out_dir: str, 
    parser_used: Optional[str]
) -> None:
    """Write knowledge graph to file and print statistics.
    
    This function always writes the knowledge graph to a file and prints statistics.
    If no output path is provided, it generates a default filename.
    """
    out = json.dumps(kg, indent=2, ensure_ascii=False)

    # Generate output path if not provided
    if not output_path:
        output_path = generate_default_filename(parser_used)
    
    out_path = Path(output_path)
    # If user provided a bare filename (no directory), place it under --out-dir
    if not out_path.is_absolute() and (out_path.parent == Path(".")):
        out_path = Path(out_dir) / out_path.name
    
    # Create directory and write file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    
    # Print file location and parser info
    print(f"✅ Knowledge graph saved to: {out_path}")
    if parser_used:
        print(f"📝 Parser used: {parser_used}")
    
    # Always print statistics
    print_kg_stats(kg)
