# IITM BS Xplore - Production Structure

## 🏗️ **New Modular Architecture**

The codebase has been reorganized into a production-level modular structure with clear separation of concerns.

### **Directory Structure**

```
iitm-bs-xplore/
├── app.py                          # Main application entry point (only main function)
├── visualize_kg.py                 # Visualization CLI entry point
├── requirements.txt                # Dependencies
├── README.md                       # Original documentation
├── README_NEW_STRUCTURE.md         # This file
├── VISUALIZATION_GUIDE.md          # Visualization documentation
├── src/                            # Main source code
│   ├── __init__.py
│   ├── processors/                 # Data processing modules
│   │   ├── __init__.py
│   │   ├── url_processor.py        # URL fetching and processing
│   │   └── file_processor.py       # File-based processing
│   ├── visualizers/                # Visualization modules
│   │   ├── __init__.py
│   │   ├── kg_visualizer.py        # Core visualization logic
│   │   └── visualization_cli.py    # Visualization CLI
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       ├── argument_parser.py      # CLI argument parsing
│       ├── output_handler.py       # Output file handling
│       └── outline_printer.py      # Outline summary printing
├── xplore/                         # Core parsing modules (unchanged)
│   ├── __init__.py
│   ├── academics.py
│   ├── course.py
│   ├── generic.py
│   ├── merge.py
│   ├── outline.py
│   ├── types.py
│   └── utils.py
└── outputs/                        # Generated data files
    ├── *.json                      # Knowledge graph data files
    └── viz/                        # Visualization outputs (PNG, DOT files)
```

### **Key Improvements**

1. **Single Responsibility**: Each module has one clear purpose
2. **Clean Separation**: Processing, visualization, and utilities are separate
3. **Maintainable**: Easy to modify individual components
4. **Testable**: Each module can be tested independently
5. **Scalable**: Easy to add new processors or visualizers

### **Module Responsibilities**

#### **Processors** (`src/processors/`)
- **`url_processor.py`**: Handles URL fetching, parser detection, course extraction
- **`file_processor.py`**: Handles local file processing

#### **Visualizers** (`src/visualizers/`)
- **`kg_visualizer.py`**: Core visualization logic with Graphviz
- **`visualization_cli.py`**: Command-line interface for visualization

#### **Utils** (`src/utils/`)
- **`argument_parser.py`**: CLI argument parsing
- **`output_handler.py`**: File output handling
- **`outline_printer.py`**: Document structure printing

### **Usage**

#### **Main Application**
```bash
# Extract knowledge graph from URL
python app.py --url "https://study.iitm.ac.in/ds/academics.html" --output data.json

# Extract from local files
python app.py --academics academics.html --course-files course1.html course2.html
```

#### **Visualization**
```bash
# Generate all visualizations
python visualize_kg.py data.json

# Generate specific layout
python visualize_kg.py data.json --layout focused

# Show statistics
python visualize_kg.py data.json --stats
```

### **Benefits of New Structure**

1. **Cleaner Code**: Each file has a single, clear purpose
2. **Better Organization**: Related functionality is grouped together
3. **Easier Maintenance**: Changes to one feature don't affect others
4. **Improved Testing**: Individual modules can be unit tested
5. **Better Documentation**: Each module is self-documenting
6. **Production Ready**: Follows Python best practices

### **Migration from Old Structure**

The old `visualize_kg.py` (400+ lines) has been split into:
- `src/visualizers/kg_visualizer.py` - Core visualization logic
- `src/visualizers/visualization_cli.py` - CLI interface
- `src/utils/argument_parser.py` - Argument parsing

The old `app.py` (400+ lines) has been split into:
- `app.py` - Main function only (50 lines)
- `src/processors/url_processor.py` - URL processing
- `src/processors/file_processor.py` - File processing
- `src/utils/output_handler.py` - Output handling
- `src/utils/outline_printer.py` - Outline printing

### **Backward Compatibility**

- All existing command-line interfaces work exactly the same
- All existing functionality is preserved
- No breaking changes for end users
- Same output formats and file structures

This new structure makes the codebase much more maintainable and production-ready! 🚀
