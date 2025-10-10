#!/usr/bin/env python3
"""
Knowledge Graph Visualizer

Converts JSON knowledge graph data to DOT format and generates PNG visualizations
using Graphviz. Supports different layout styles and filtering options.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import subprocess
import sys


class KnowledgeGraphVisualizer:
    """Visualizes knowledge graphs using Graphviz DOT format."""
    
    def __init__(self, kg_data: Dict[str, Any]):
        self.kg_data = kg_data
        self.nodes = {node["id"]: node for node in kg_data.get("nodes", [])}
        self.edges = kg_data.get("edges", [])
        
        # Color schemes for different node types
        self.node_colors = {
            "Program": "#FF6B6B",      # Red
            "Level": "#4ECDC4",        # Teal
            "Section": "#45B7D1",      # Blue
            "Course": "#96CEB4",       # Green
            "Collection": "#FFEAA7",   # Yellow
            "default": "#DDA0DD"       # Plum
        }
        
        # Edge colors for different relationship types
        self.edge_colors = {
            "HAS_LEVEL": "#2C3E50",      # Dark blue
            "HAS_SECTION": "#34495E",    # Dark gray
            "HAS": "#27AE60",            # Green
            "CONTAINS": "#27AE60",       # Green (same as HAS for level-course relationships)
            "REQUIRES": "#E74C3C",       # Red
            "default": "#7F8C8D"         # Gray
        }

    def sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for DOT format."""
        # Replace problematic characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = f"node_{sanitized}"
        return sanitized or "empty_id"

    def get_node_label(self, node: Dict[str, Any]) -> str:
        """Generate a readable label for a node."""
        node_type = node.get("type", "Unknown")
        properties = node.get("properties", {})
        
        # Try to get a meaningful title/name
        title = properties.get("name") or properties.get("courseId") or properties.get("title")
        
        if title:
            # Truncate long titles
            if len(title) > 30:
                title = title[:27] + "..."
            return f"{title}\\n({node_type})"
        else:
            return f"{node_type}\\n{node['id']}"

    def get_node_color(self, node: Dict[str, Any]) -> str:
        """Get color for a node based on its type."""
        node_type = node.get("type", "default")
        return self.node_colors.get(node_type, self.node_colors["default"])

    def get_edge_color(self, edge: Dict[str, Any]) -> str:
        """Get color for an edge based on its type."""
        edge_type = edge.get("type", "default")
        return self.edge_colors.get(edge_type, self.edge_colors["default"])

    def filter_nodes(self, node_types: Optional[List[str]] = None, 
                    max_nodes: Optional[int] = None) -> Set[str]:
        """Filter nodes based on type and limit count."""
        filtered_ids = set()
        
        # Filter by type
        if node_types:
            filtered_ids = {
                node["id"] for node in self.nodes.values() 
                if node.get("type") in node_types
            }
        else:
            filtered_ids = set(self.nodes.keys())
        
        # Limit count if specified
        if max_nodes and len(filtered_ids) > max_nodes:
            # Prioritize certain node types
            priority_types = ["Program", "Level", "Course"]
            priority_nodes = [
                node_id for node_id in filtered_ids
                if self.nodes[node_id].get("type") in priority_types
            ]
            
            if len(priority_nodes) <= max_nodes:
                filtered_ids = set(priority_nodes)
            else:
                filtered_ids = set(list(filtered_ids)[:max_nodes])
        
        return filtered_ids

    def filter_edges(self, node_ids: Set[str]) -> List[Dict[str, Any]]:
        """Filter edges to only include those connecting filtered nodes."""
        return [
            edge for edge in self.edges
            if edge.get("source") in node_ids and edge.get("target") in node_ids
        ]

    def generate_dot(self, layout: str = "hierarchical", 
                    node_types: Optional[List[str]] = None,
                    max_nodes: Optional[int] = None,
                    show_edge_labels: bool = False) -> str:
        """Generate DOT format string for the knowledge graph."""
        
        # Filter nodes and edges
        filtered_node_ids = self.filter_nodes(node_types, max_nodes)
        filtered_edges = self.filter_edges(filtered_node_ids)
        
        # Choose layout engine
        if layout == "hierarchical":
            dot_content = 'digraph KnowledgeGraph {\n'
            dot_content += '    rankdir=TB;\n'
            dot_content += '    node [shape=box, style=filled, fontname="Arial", fontsize=10];\n'
            dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        elif layout == "network":
            dot_content = 'digraph KnowledgeGraph {\n'
            dot_content += '    layout=neato;\n'
            dot_content += '    node [shape=ellipse, style=filled, fontname="Arial", fontsize=10];\n'
            dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        elif layout == "circular":
            dot_content = 'digraph KnowledgeGraph {\n'
            dot_content += '    layout=circo;\n'
            dot_content += '    node [shape=circle, style=filled, fontname="Arial", fontsize=10];\n'
            dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        else:
            dot_content = 'digraph KnowledgeGraph {\n'
            dot_content += '    node [shape=box, style=filled, fontname="Arial", fontsize=10];\n'
            dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        
        # Add nodes
        for node_id in filtered_node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                sanitized_id = self.sanitize_id(node_id)
                label = self.get_node_label(node)
                color = self.get_node_color(node)
                
                dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}"];\n'
        
        # Add edges
        for edge in filtered_edges:
            source_id = self.sanitize_id(edge["source"])
            target_id = self.sanitize_id(edge["target"])
            edge_type = edge.get("type", "")
            color = self.get_edge_color(edge)
            
            if show_edge_labels and edge_type:
                dot_content += f'    {source_id} -> {target_id} [label="{edge_type}", color="{color}"];\n'
            else:
                dot_content += f'    {source_id} -> {target_id} [color="{color}"];\n'
        
        dot_content += '}\n'
        return dot_content

    def save_dot(self, dot_content: str, output_path: str) -> None:
        """Save DOT content to file."""
        Path(output_path).write_text(dot_content, encoding='utf-8')
        print(f"DOT file saved to: {output_path}")

    def generate_png(self, dot_file: str, png_file: str, layout: str = "hierarchical") -> None:
        """Generate PNG from DOT file using Graphviz."""
        try:
            # Choose the appropriate Graphviz command based on layout
            if layout == "hierarchical":
                cmd = ["dot", "-Tpng", "-o", png_file, dot_file]
            elif layout == "network":
                cmd = ["neato", "-Tpng", "-o", png_file, dot_file]
            elif layout == "circular":
                cmd = ["circo", "-Tpng", "-o", png_file, dot_file]
            else:
                cmd = ["dot", "-Tpng", "-o", png_file, dot_file]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"PNG file generated: {png_file}")
            else:
                print(f"Error generating PNG: {result.stderr}")
                print("Make sure Graphviz is installed: brew install graphviz (macOS) or apt-get install graphviz (Ubuntu)")
                
        except FileNotFoundError:
            print("Error: Graphviz not found. Please install Graphviz:")
            print("  macOS: brew install graphviz")
            print("  Ubuntu/Debian: sudo apt-get install graphviz")
            print("  Windows: Download from https://graphviz.org/download/")

    def create_course_focused_view(self, output_dir: str) -> None:
        """Create a course-focused visualization showing courses properly connected to their levels."""
        print("Creating course-focused visualization...")
        
        # Filter to courses, levels, and their direct connections
        course_nodes = {node_id for node_id, node in self.nodes.items() 
                       if node.get("type") == "Course"}
        level_nodes = {node_id for node_id, node in self.nodes.items() 
                      if node.get("type") == "Level"}
        
        # Find nodes connected to courses and levels
        connected_nodes = set(course_nodes) | set(level_nodes)
        for edge in self.edges:
            if (edge.get("source") in connected_nodes or edge.get("target") in connected_nodes):
                connected_nodes.add(edge.get("source"))
                connected_nodes.add(edge.get("target"))
        
        # Create DOT content for course view
        dot_content = 'digraph CourseGraph {\n'
        dot_content += '    rankdir=TB;\n'
        dot_content += '    node [shape=box, style=filled, fontname="Arial", fontsize=10];\n'
        dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        
        # Add connected nodes
        for node_id in connected_nodes:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                sanitized_id = self.sanitize_id(node_id)
                label = self.get_node_label(node)
                color = self.get_node_color(node)
                
                # Make courses and levels more prominent
                if node.get("type") in ["Course", "Level"]:
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}", shape=box, style="filled,bold"];\n'
                else:
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}"];\n'
        
        # Add edges
        for edge in self.edges:
            if (edge.get("source") in connected_nodes and edge.get("target") in connected_nodes):
                source_id = self.sanitize_id(edge["source"])
                target_id = self.sanitize_id(edge["target"])
                edge_type = edge.get("type", "")
                color = self.get_edge_color(edge)
                
                if edge_type:
                    dot_content += f'    {source_id} -> {target_id} [label="{edge_type}", color="{color}"];\n'
                else:
                    dot_content += f'    {source_id} -> {target_id} [color="{color}"];\n'
        
        dot_content += '}\n'
        
        # Save and generate PNG
        dot_file = Path(output_dir) / "course_graph.dot"
        png_file = Path(output_dir) / "course_graph.png"
        
        self.save_dot(dot_content, str(dot_file))
        self.generate_png(str(dot_file), str(png_file))

    def create_hierarchical_view(self, output_dir: str) -> None:
        """Create a hierarchical visualization showing the program structure."""
        print("Creating hierarchical visualization...")
        
        # Filter to program structure (Program, Level, Section)
        structure_types = ["Program", "Level", "Section"]
        dot_content = self.generate_dot(
            layout="hierarchical",
            node_types=structure_types,
            max_nodes=100,
            show_edge_labels=True
        )
        
        dot_file = Path(output_dir) / "hierarchical_graph.dot"
        png_file = Path(output_dir) / "hierarchical_graph.png"
        
        self.save_dot(dot_content, str(dot_file))
        self.generate_png(str(dot_file), str(png_file))

    def create_complete_hierarchy_view(self, output_dir: str) -> None:
        """Create a complete hierarchical visualization showing Program -> Level -> Courses."""
        print("Creating complete hierarchy visualization...")
        
        # Get all relevant nodes
        program_nodes = {node_id: node for node_id, node in self.nodes.items() 
                        if node.get("type") == "Program"}
        level_nodes = {node_id: node for node_id, node in self.nodes.items() 
                      if node.get("type") == "Level"}
        course_nodes = {node_id: node for node_id, node in self.nodes.items() 
                       if node.get("type") == "Course"}
        
        # Create level-to-course mapping
        level_course_mapping = {}
        
        # Try to map courses to levels based on existing edges
        for edge in self.edges:
            if edge.get("type") == "HAS" and edge.get("target") in course_nodes:
                collection_id = edge.get("source")
                if collection_id in self.nodes:
                    collection = self.nodes[collection_id]
                    if collection.get("type") == "Collection":
                        # Find which level this collection belongs to
                        for level_edge in self.edges:
                            if (level_edge.get("type") == "HAS" and 
                                level_edge.get("source") in level_nodes and 
                                level_edge.get("target") == collection_id):
                                level_id = level_edge.get("source")
                                if level_id not in level_course_mapping:
                                    level_course_mapping[level_id] = []
                                level_course_mapping[level_id].append(edge.get("target"))
        
        # Create DOT content
        dot_content = 'digraph CompleteHierarchy {\n'
        dot_content += '    rankdir=TB;\n'
        dot_content += '    node [shape=box, style=filled, fontname="Arial", fontsize=10];\n'
        dot_content += '    edge [fontname="Arial", fontsize=8];\n'
        
        # Add program nodes
        for program_id, program in program_nodes.items():
            sanitized_id = self.sanitize_id(program_id)
            label = self.get_node_label(program)
            color = self.get_node_color(program)
            dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}", shape=box, style="filled,bold"];\n'
        
        # Add level nodes and connect to program
        for level_id, level in level_nodes.items():
            sanitized_id = self.sanitize_id(level_id)
            label = self.get_node_label(level)
            color = self.get_node_color(level)
            dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}", shape=box, style="filled,bold"];\n'
            
            # Connect to program
            for program_id in program_nodes:
                program_sanitized = self.sanitize_id(program_id)
                dot_content += f'    {program_sanitized} -> {sanitized_id} [label="HAS_LEVEL", color="#2C3E50"];\n'
        
        # Add course nodes and connect to levels
        for level_id, course_list in level_course_mapping.items():
            level_sanitized = self.sanitize_id(level_id)
            for course_id in course_list[:10]:  # Limit to first 10 courses per level for readability
                if course_id in course_nodes:
                    course = course_nodes[course_id]
                    sanitized_id = self.sanitize_id(course_id)
                    label = self.get_node_label(course)
                    color = self.get_node_color(course)
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}"];\n'
                    # Connect course to level
                    dot_content += f'    {level_sanitized} -> {sanitized_id} [label="CONTAINS", color="#27AE60"];\n'
        
        # Add prerequisite relationships between courses
        for edge in self.edges:
            if (edge.get("type") == "REQUIRES" and 
                edge.get("source") in course_nodes and 
                edge.get("target") in course_nodes):
                source_id = self.sanitize_id(edge["source"])
                target_id = self.sanitize_id(edge["target"])
                dot_content += f'    {source_id} -> {target_id} [label="REQUIRES", color="#E74C3C", style="dashed"];\n'
        
        dot_content += '}\n'
        
        # Save and generate PNG
        dot_file = Path(output_dir) / "complete_hierarchy.dot"
        png_file = Path(output_dir) / "complete_hierarchy.png"
        
        self.save_dot(dot_content, str(dot_file))
        self.generate_png(str(dot_file), str(png_file))

    def create_network_view(self, output_dir: str, max_nodes: int = 200) -> None:
        """Create a network visualization showing all relationships."""
        print("Creating network visualization...")
        
        # Filter nodes and edges for network view
        filtered_node_ids = self.filter_nodes(max_nodes=max_nodes)
        filtered_edges = self.filter_edges(filtered_node_ids)
        
        # Create DOT content with better spacing
        dot_content = 'digraph NetworkGraph {\n'
        dot_content += '    layout=neato;\n'
        dot_content += '    overlap=false;\n'
        dot_content += '    splines=true;\n'
        dot_content += '    sep="+20";\n'  # Increase separation between nodes
        dot_content += '    esep="+10";\n'  # Extra separation for edges
        dot_content += '    node [shape=ellipse, style=filled, fontname="Arial", fontsize=8, width=0.8, height=0.5];\n'
        dot_content += '    edge [fontname="Arial", fontsize=6, len=2.0];\n'  # Longer edges for more space
        
        # Add nodes with better positioning
        for node_id in filtered_node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                sanitized_id = self.sanitize_id(node_id)
                label = self.get_node_label(node)
                color = self.get_node_color(node)
                
                # Make important nodes more prominent
                if node.get("type") in ["Program", "Level"]:
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}", shape=box, style="filled,bold", width=1.2, height=0.8];\n'
                elif node.get("type") == "Course":
                    # Truncate course labels for better readability
                    short_label = label.replace("\\n", " ")[:25] + "..." if len(label) > 25 else label.replace("\\n", " ")
                    dot_content += f'    {sanitized_id} [label="{short_label}", fillcolor="{color}", width=1.0, height=0.6];\n'
                else:
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}"];\n'
        
        # Add edges with better styling
        for edge in filtered_edges:
            source_id = self.sanitize_id(edge["source"])
            target_id = self.sanitize_id(edge["target"])
            edge_type = edge.get("type", "")
            color = self.get_edge_color(edge)
            
            # Style edges based on type
            if edge_type == "CONTAINS":
                dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=2.0, len=3.0];\n'
            elif edge_type == "REQUIRES":
                dot_content += f'    {source_id} -> {target_id} [color="{color}", style="dashed", penwidth=1.5, len=2.5];\n'
            elif edge_type == "HAS_LEVEL":
                dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=3.0, len=4.0];\n'
            else:
                dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=1.0, len=2.0];\n'
        
        dot_content += '}\n'
        
        dot_file = Path(output_dir) / "network_graph.dot"
        png_file = Path(output_dir) / "network_graph.png"
        
        self.save_dot(dot_content, str(dot_file))
        self.generate_png(str(dot_file), str(png_file))

    def create_focused_network_view(self, output_dir: str) -> None:
        """Create a focused network visualization with only key nodes for better readability."""
        print("Creating focused network visualization...")
        
        # Focus on Program, Levels, and a sample of courses
        key_node_types = ["Program", "Level"]
        key_nodes = {node_id for node_id, node in self.nodes.items() 
                    if node.get("type") in key_node_types}
        
        # Add a sample of courses (first 20 from each level)
        course_nodes = {node_id for node_id, node in self.nodes.items() 
                       if node.get("type") == "Course"}
        
        # Group courses by level
        courses_by_level = {}
        for edge in self.edges:
            if edge.get("type") == "CONTAINS" and edge.get("target") in course_nodes:
                level_id = edge.get("source")
                if level_id not in courses_by_level:
                    courses_by_level[level_id] = []
                courses_by_level[level_id].append(edge.get("target"))
        
        # Add sample courses from each level
        sample_courses = set()
        for level_id, courses in courses_by_level.items():
            sample_courses.update(courses[:15])  # Take first 15 courses from each level
        
        all_nodes = key_nodes | sample_courses
        
        # Create DOT content with maximum spacing
        dot_content = 'digraph FocusedNetwork {\n'
        dot_content += '    layout=neato;\n'
        dot_content += '    overlap=false;\n'
        dot_content += '    splines=true;\n'
        dot_content += '    sep="+30";\n'  # Maximum separation
        dot_content += '    esep="+15";\n'  # Extra separation for edges
        dot_content += '    node [shape=ellipse, style=filled, fontname="Arial", fontsize=9, width=1.0, height=0.6];\n'
        dot_content += '    edge [fontname="Arial", fontsize=7, len=3.0];\n'  # Longer edges
        
        # Add nodes
        for node_id in all_nodes:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                sanitized_id = self.sanitize_id(node_id)
                label = self.get_node_label(node)
                color = self.get_node_color(node)
                
                if node.get("type") in ["Program", "Level"]:
                    dot_content += f'    {sanitized_id} [label="{label}", fillcolor="{color}", shape=box, style="filled,bold", width=1.5, height=1.0];\n'
                else:
                    # Shorten course labels
                    short_label = label.replace("\\n", " ")[:20] + "..." if len(label) > 20 else label.replace("\\n", " ")
                    dot_content += f'    {sanitized_id} [label="{short_label}", fillcolor="{color}"];\n'
        
        # Add edges
        for edge in self.edges:
            if (edge.get("source") in all_nodes and edge.get("target") in all_nodes):
                source_id = self.sanitize_id(edge["source"])
                target_id = self.sanitize_id(edge["target"])
                edge_type = edge.get("type", "")
                color = self.get_edge_color(edge)
                
                if edge_type == "CONTAINS":
                    dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=2.5, len=4.0];\n'
                elif edge_type == "HAS_LEVEL":
                    dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=4.0, len=5.0];\n'
                elif edge_type == "REQUIRES":
                    dot_content += f'    {source_id} -> {target_id} [color="{color}", style="dashed", penwidth=2.0, len=3.5];\n'
                else:
                    dot_content += f'    {source_id} -> {target_id} [color="{color}", penwidth=1.5, len=3.0];\n'
        
        dot_content += '}\n'
        
        dot_file = Path(output_dir) / "focused_network.dot"
        png_file = Path(output_dir) / "focused_network.png"
        
        self.save_dot(dot_content, str(dot_file))
        self.generate_png(str(dot_file), str(png_file))

    def print_statistics(self) -> None:
        """Print statistics about the knowledge graph."""
        print("\n=== Knowledge Graph Statistics ===")
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Total edges: {len(self.edges)}")
        
        # Count by node type
        type_counts = {}
        for node in self.nodes.values():
            node_type = node.get("type", "Unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        print("\nNode types:")
        for node_type, count in sorted(type_counts.items()):
            print(f"  {node_type}: {count}")
        
        # Count by edge type
        edge_type_counts = {}
        for edge in self.edges:
            edge_type = edge.get("type", "Unknown")
            edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
        
        print("\nEdge types:")
        for edge_type, count in sorted(edge_type_counts.items()):
            print(f"  {edge_type}: {count}")


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
        default="visualizations",
        help="Output directory for DOT and PNG files (default: visualizations)"
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
