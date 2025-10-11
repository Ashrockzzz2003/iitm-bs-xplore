"""
Visualization CLI Module

Command line interface for knowledge graph visualization.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .kg_visualizer import KnowledgeGraphVisualizer


def main():
    """Main entry point for the visualizer."""
    parser = argparse.ArgumentParser(
        description="Visualize knowledge graph data using Graphviz"
    )
    parser.add_argument(
        "input_file",
        help="Path to JSON knowledge graph file"
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/viz",
        help="Output directory for DOT and PNG files (default: outputs/viz)"
    )
    parser.add_argument(
        "--layout",
        choices=["hierarchical", "network", "focused", "circular", "all"],
        default="all",
        help="Layout style for visualization (default: all)"
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        help="Maximum number of nodes to include in visualization"
    )
    parser.add_argument(
        "--node-types",
        nargs="*",
        help="Filter to specific node types (e.g., Course Level Section)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print knowledge graph statistics"
    )
    
    args = parser.parse_args()
    
    # Load knowledge graph data
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {args.input_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input_file}: {e}")
        sys.exit(1)
    
    # Create visualizer
    visualizer = KnowledgeGraphVisualizer(kg_data)
    
    # Print statistics if requested
    if args.stats:
        visualizer.print_statistics()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Generate visualizations
    if args.layout == "all":
        visualizer.create_hierarchical_view(str(output_dir))
        visualizer.create_course_focused_view(str(output_dir))
        visualizer.create_network_view(str(output_dir), args.max_nodes or 200)
        visualizer.create_focused_network_view(str(output_dir))
    elif args.layout == "hierarchical":
        visualizer.create_hierarchical_view(str(output_dir))
    elif args.layout == "network":
        visualizer.create_network_view(str(output_dir), args.max_nodes or 200)
    elif args.layout == "focused":
        visualizer.create_focused_network_view(str(output_dir))
    elif args.layout == "circular":
        dot_content = visualizer.generate_dot(
            layout="circular",
            node_types=args.node_types,
            max_nodes=args.max_nodes,
            show_edge_labels=True
        )
        dot_file = output_dir / "circular_graph.dot"
        png_file = output_dir / "circular_graph.png"
        visualizer.save_dot(dot_content, str(dot_file))
        visualizer.generate_png(str(dot_file), str(png_file), "circular")
    
    print(f"\nVisualizations saved to: {output_dir}")


if __name__ == "__main__":
    main()
