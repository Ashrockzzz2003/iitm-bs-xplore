#!/usr/bin/env python3
"""
Knowledge Graph Visualizer

Converts JSON knowledge graph data to DOT format and generates PNG visualizations
using Graphviz. Supports different layout styles and filtering options.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import subprocess
import sys


class KnowledgeGraphVisualizer:
    """Visualizes knowledge graphs using Graphviz DOT format.
    
    This class provides comprehensive visualization capabilities for knowledge graphs,
    including different layout styles, filtering options, and color schemes to make
    complex academic program structures easily understandable.
    """
    
    def __init__(self, kg_data: Dict[str, Any]):
        self.kg_data = kg_data
        self.nodes = {node["id"]: node for node in kg_data.get("nodes", [])}
        self.edges = kg_data.get("edges", [])
        
        # Color schemes for different node types
        # Each node type has a distinct color for easy identification
        self.node_colors = {
            "Program": "#FF6B6B",      # Red - Main program nodes
            "Level": "#4ECDC4",        # Teal - Academic levels (Foundation, Diploma, etc.)
            "Section": "#45B7D1",      # Blue - Content sections
            "Course": "#96CEB4",       # Green - Individual courses
            "Collection": "#FFEAA7",   # Yellow - Course collections
            "default": "#DDA0DD"       # Plum - Other node types
        }
        
        # Edge colors for different relationship types
        # Colors help distinguish between different types of relationships
        self.edge_colors = {
            "HAS_LEVEL": "#2C3E50",      # Dark blue - Program has levels
            "HAS_SECTION": "#34495E",    # Dark gray - Level has sections
            "HAS": "#27AE60",            # Green - General containment
            "CONTAINS": "#27AE60",       # Green - Level contains courses
            "REQUIRES": "#E74C3C",       # Red - Prerequisite relationships
            "default": "#7F8C8D"         # Gray - Other relationships
        }

    def sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for DOT format.
        
        Graphviz DOT format has specific requirements for node IDs.
        This function ensures the ID is valid by replacing special characters
        and ensuring it starts with a letter.
        """
        # Replace problematic characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
        # Ensure it starts with a letter (DOT requirement)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"node_{sanitized}"
        return sanitized or "empty_id"

    def get_node_label(self, node: Dict[str, Any]) -> str:
        """Generate a readable label for a node.
        
        Creates a human-readable label by combining the node's title/name
        with its type, truncating long titles for better visualization.
        """
        node_type = node.get("type", "Unknown")
        properties = node.get("properties", {})
        
        # Try to get a meaningful title/name from various possible fields
        title = properties.get("name") or properties.get("courseId") or properties.get("title")
        
        if title:
            # Truncate long titles to keep visualization clean
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
