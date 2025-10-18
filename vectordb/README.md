# ChromaDB Vector Database

This module provides functionality to upload text files from `direct/outputs/` into ChromaDB collections for vector search and retrieval.

## Overview

The vectordb module automatically processes text files from the outputs directory and creates ChromaDB collections based on the folder structure. Each txt file becomes a separate collection with vector embeddings for semantic search.

## Collection Naming Convention

Collections are named based on the folder structure in `direct/outputs/`:

- `direct/outputs/ds/degree/content.txt` → collection: `ds_degree`
- `direct/outputs/ds/diploma/content.txt` → collection: `ds_diploma`
- `direct/outputs/ds/foundation/content.txt` → collection: `ds_foundation`
- `direct/outputs/es/degree/content.txt` → collection: `es_degree`
- `direct/outputs/es/diploma/content.txt` → collection: `es_diploma`
- `direct/outputs/es/foundation/content.txt` → collection: `es_foundation`
- `direct/outputs/generic/content.txt` → collection: `generic`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The module will automatically create a `chroma_data/` directory for persistent storage.

## Usage

### AI Agent Tools (Recommended)

The easiest way for AI agents to use the vector database:

```python
from agent_tools import VectorDBTools, quick_search, quick_search_by_program

# Initialize tools
tools = VectorDBTools()

# Search across all collections
results = tools.search_content("machine learning", n_results=5)

# Search specific program
ds_results = tools.search_by_program("deep learning", "ds", n_results=3)

# Search specific academic level
degree_results = tools.search_by_level("software engineering", "degree", n_results=3)

# Find similar content
similar = tools.get_similar_content("neural networks", "ds_degree", n_results=3)

# Get collection information
collections = tools.list_collections()
```

### Quick Functions for Simple Use Cases

```python
from agent_tools import quick_search, quick_search_by_program

# Quick search across all collections
results = quick_search("artificial intelligence", n_results=5)

# Quick search by program
ds_results = quick_search_by_program("data science", "ds", n_results=3)
```

### Command Line Interface

#### Upload all txt files to ChromaDB
```bash
python cli.py upload
```

#### List all available collections
```bash
python cli.py list
```

#### Query a collection
```bash
python cli.py query -c ds_degree -q "software engineering"
```

#### Get collection information
```bash
python cli.py info -c ds_degree
```

### Low-Level Python API

```python
from chroma_uploader import ChromaUploader

# Initialize uploader
uploader = ChromaUploader()

# Upload all files
uploader.upload_all_files("path/to/outputs")

# List collections
collections = uploader.list_collections()

# Query a collection
results = uploader.query_collection("ds_degree", "software engineering", n_results=5)

# Get collection info
info = uploader.get_collection_info("ds_degree")
```

## Features

- **Automatic Collection Creation**: Collections are created based on folder structure
- **Text Chunking**: Large text files are automatically chunked for better search performance
- **Metadata Preservation**: File paths, program types, and levels are preserved as metadata
- **Semantic Search**: Vector embeddings enable semantic similarity search
- **Persistent Storage**: Data is stored persistently in the `chroma_data/` directory

## Text Chunking

Large text files are automatically split into overlapping chunks (default: 1000 characters with 200 character overlap) to:
- Handle token limits
- Improve search granularity
- Enable better retrieval of specific content sections

## Metadata

Each document chunk includes metadata:
- `file_path`: Original file path
- `program`: Program type (ds, es, generic)
- `level`: Academic level (degree, diploma, foundation)
- `chunk_index`: Position within the original file
- `total_chunks`: Total number of chunks in the file
- `chunk_size`: Size of the current chunk
- `content_length`: Total length of the original file

## File Structure

```
vectordb/
├── __init__.py
├── chroma_uploader.py    # Core upload logic
├── cli.py               # Command-line interface
├── requirements.txt     # Dependencies
├── README.md           # This file
└── chroma_data/        # ChromaDB persistent storage (created automatically)
```

## Examples

### Upload and Search
```bash
# Upload all files
python cli.py upload

# Search for software engineering content
python cli.py query -c ds_degree -q "software testing methodologies"

# Search for AI-related content
python cli.py query -c ds_degree -q "artificial intelligence search methods"
```

### Programmatic Usage
```python
from chroma_uploader import ChromaUploader

uploader = ChromaUploader()

# Upload specific directory
uploader.upload_all_files("/path/to/outputs")

# Search across all collections
for collection in uploader.list_collections():
    results = uploader.query_collection(collection, "your query")
    print(f"Results from {collection}: {len(results.get('documents', [[]])[0])}")
```
