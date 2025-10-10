# Knowledge Graph Visualization Guide

This guide explains how to visualize your knowledge graph data using the `visualize_kg.py` script.

## Prerequisites

1. **Install Graphviz**: The script uses Graphviz to generate PNG images from DOT files.
   ```bash
   # macOS
   brew install graphviz
   
   # Ubuntu/Debian
   sudo apt-get install graphviz
   
   # Windows: Download from https://graphviz.org/download/
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Basic Usage

### Generate All Visualizations
```bash
python visualize_kg.py outputs/production_full_courses.json
```

This creates four different visualizations in the `outputs/viz/` directory:
- `hierarchical_graph.png` - Shows program structure (Program → Level → Section)
- `course_graph.png` - Focuses on courses and their relationships
- `network_graph.png` - Shows all nodes and relationships in a network layout
- `focused_network.png` - Less cluttered network view with key nodes only

### Specific Layouts

#### Hierarchical Layout (Program Structure)
```bash
python visualize_kg.py outputs/production_full_courses.json --layout hierarchical
```

#### Course-Focused Layout
```bash
python visualize_kg.py outputs/production_full_courses.json --layout network --node-types Course
```

#### Focused Network Layout (Less Cluttered)
```bash
python visualize_kg.py outputs/production_full_courses.json --layout focused
```

#### Circular Layout
```bash
python visualize_kg.py outputs/production_full_courses.json --layout circular
```

### Filtering Options

#### Limit Number of Nodes
```bash
python visualize_kg.py outputs/production_full_courses.json --max-nodes 50
```

#### Filter by Node Types
```bash
python visualize_kg.py outputs/production_full_courses.json --node-types Program Level Course
```

#### Show Statistics
```bash
python visualize_kg.py outputs/production_full_courses.json --stats
```

### Custom Output Directory
```bash
python visualize_kg.py outputs/production_full_courses.json --output-dir my_visualizations
```

## Understanding the Visualizations

### Node Colors
- **Red**: Program nodes
- **Teal**: Level nodes  
- **Blue**: Section nodes
- **Green**: Course nodes
- **Yellow**: Collection nodes
- **Plum**: Other node types

### Edge Colors
- **Dark Blue**: HAS_LEVEL relationships
- **Dark Gray**: HAS_SECTION relationships
- **Green**: HAS relationships
- **Red**: REQUIRES relationships (prerequisites)
- **Gray**: Other relationships

### Layout Types

1. **Hierarchical**: Best for understanding program structure and hierarchy
2. **Network**: Good for seeing all relationships and connections
3. **Course-focused**: Emphasizes courses and their prerequisites
4. **Circular**: Alternative layout for smaller graphs

## File Outputs

For each visualization, the script generates:
- `.dot` file: Graphviz DOT format (text-based graph description)
- `.png` file: Rendered image

You can edit the `.dot` files manually if you want to customize the visualization further.

## Troubleshooting

### Graphviz Not Found
If you get "Graphviz not found" error:
1. Install Graphviz using the commands above
2. Make sure it's in your system PATH
3. Try running `dot -V` to verify installation

### Large Graphs
For very large knowledge graphs:
- Use `--max-nodes` to limit the number of nodes
- Use `--node-types` to focus on specific node types
- Consider using the course-focused layout for course-heavy graphs

### Memory Issues
If you encounter memory issues with large graphs:
- Reduce `--max-nodes` value
- Use more specific `--node-types` filters
- Process the graph in smaller chunks

## Examples

### Quick Course Overview
```bash
python visualize_kg.py outputs/production_full_courses.json --layout network --node-types Course --max-nodes 30
```

### Program Structure Only
```bash
python visualize_kg.py outputs/production_full_courses.json --layout hierarchical --node-types Program Level Section
```

### Full Statistics
```bash
python visualize_kg.py outputs/production_full_courses.json --stats
```
