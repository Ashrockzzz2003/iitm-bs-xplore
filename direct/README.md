# Direct Text Extraction Pipeline

A streamlined pipeline for extracting text content from HTML pages and uploading to Neo4j for automatic knowledge graph generation.

## Overview

This pipeline:
1. Fetches HTML from multiple parent URLs (DS, ES academics pages) and all linked course pages
2. Extracts plain text content from HTML (removing tags, scripts, styles)
3. Combines all text into a single large txt file with clear URL separators
4. Uploads the text file to Neo4j to leverage its NLP/AI features for automatic KG generation

## Quick Start

### 1. Install Dependencies

```bash
# Install additional dependencies
pip install -r requirements.txt

# Or install from main project
pip install -r ../data/requirements.txt
```

### 2. Basic Usage

```bash
# Extract text from DS program only
python main.py --programs ds

# Extract text from both DS and ES programs
python main.py --programs ds es

# Extract and upload to Neo4j
python main.py --programs ds es --neo4j

# Custom output file
python main.py --programs ds es --output my_text.txt

# Clear Neo4j database before upload
python main.py --programs ds es --neo4j --neo4j-clear
```

### 3. Advanced Usage

```bash
# Custom Neo4j connection
python main.py --programs ds es --neo4j \
  --neo4j-uri neo4j://localhost:7687 \
  --neo4j-username neo4j \
  --neo4j-password mypassword \
  --neo4j-database neo4j

# Verbose output with error details
python main.py --programs ds es --verbose

# Dry run to see what would be processed
python main.py --programs ds es --dry-run
```

## Command Line Options

### Required Arguments
- `--programs`: Programs to process (ds, es, or both)

### Output Options
- `--output`: Output text file name (default: combined_text.txt)
- `--output-dir`: Output directory (default: outputs)

### Neo4j Options
- `--neo4j`: Upload to Neo4j after text extraction
- `--neo4j-uri`: Neo4j URI (default: neo4j://127.0.0.1:7687)
- `--neo4j-username`: Neo4j username (default: neo4j)
- `--neo4j-password`: Neo4j password (default: password)
- `--neo4j-database`: Neo4j database name (default: neo4j)
- `--neo4j-clear`: Clear Neo4j database before uploading

### Processing Options
- `--verbose`: Enable verbose output
- `--dry-run`: Show what would be done without actually doing it

## Output Format

The pipeline generates a combined text file with the following structure:

```
================================================================================
IITM BS Xplore - Combined Text Content
Generated: 2025-01-12 10:30:45
Total URLs: 150
================================================================================

========================================
URL: https://study.iitm.ac.in/ds/academics.html
PROGRAM: DS
TYPE: academics
========================================

[Extracted text content here]

========================================
URL: https://study.iitm.ac.in/ds/course_pages/BSDA1001.html
PROGRAM: DS
TYPE: course
COURSE_ID: BSDA1001
LABEL: Programming for Data Science
LEVEL: foundation
========================================

[Extracted text content here]

... (repeat for all URLs)
```

## Neo4j Data Model

The pipeline creates the following node types in Neo4j:

### Document Nodes
- **Type**: `Document`
- **Properties**:
  - `id`: Unique document identifier
  - `url`: Source URL
  - `textContent`: Extracted text content
  - `program`: Program (DS/ES)
  - `type`: Document type (academics/course)
  - `course_id`: Course ID (for course documents)
  - `label`: Course label (for course documents)
  - `level`: Academic level
  - `word_count`: Number of words
  - `char_count`: Number of characters
  - `uploaded_at`: Upload timestamp

### Program Nodes
- **Type**: `Program`
- **Properties**:
  - `name`: Program name (DS/ES)
  - `type`: Always "Program"
  - `uploaded_at`: Upload timestamp

### Metadata Nodes
- **Type**: `Metadata`
- **Properties**:
  - `type`: Always "TextUpload"
  - `uploaded_at`: Upload timestamp
  - `document_count`: Total number of documents
  - `total_words`: Total word count
  - `total_characters`: Total character count
  - `programs`: List of programs processed

### Relationships
- `Program` -[:HAS_DOCUMENT]-> `Document`
- `Document` -[:HAS_COURSE]-> `Document` (academics to courses)

## Example Neo4j Queries

### Find All Documents
```cypher
MATCH (d:Document) 
RETURN d.url, d.program, d.type, d.word_count 
LIMIT 10
```

### Find Documents by Program
```cypher
MATCH (d:Document) 
WHERE d.program = 'DS' 
RETURN d.url, d.label, d.level 
ORDER BY d.level, d.label
```

### Search Text Content
```cypher
MATCH (d:Document) 
WHERE d.textContent CONTAINS 'machine learning' 
RETURN d.url, d.label, d.program
```

### Find Program Structure
```cypher
MATCH (p:Program)-[:HAS_DOCUMENT]->(d:Document) 
RETURN p.name, d.type, count(d) as doc_count 
ORDER BY p.name, d.type
```

### Find Course Prerequisites
```cypher
MATCH (d:Document) 
WHERE d.type = 'course' AND d.textContent CONTAINS 'prerequisite' 
RETURN d.course_id, d.label, d.textContent
```

### Full-Text Search
```cypher
MATCH (d:Document) 
WHERE d.textContent =~ '.*data science.*' 
RETURN d.url, d.label, d.program
```

## Module Structure

- `main.py` - Main orchestration script with CLI
- `text_extractor.py` - HTML to text extraction
- `url_fetcher.py` - URL fetching and course link extraction
- `text_aggregator.py` - Text combination and file generation
- `text_to_neo4j.py` - Neo4j upload functionality

## Error Handling

The pipeline includes comprehensive error handling:

- **Network errors**: Retries and graceful failure for URL fetching
- **Parsing errors**: Continues processing other URLs if one fails
- **Neo4j errors**: Detailed error messages and connection validation
- **File errors**: Proper file handling and encoding support

## Performance

Typical performance metrics:
- **DS program**: ~50-80 course URLs, ~500KB-1MB text
- **ES program**: ~40-60 course URLs, ~400KB-800KB text
- **Processing time**: 2-5 minutes for both programs
- **Neo4j upload**: 30-60 seconds for full dataset

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running from the `direct/` directory
2. **Neo4j connection**: Verify Neo4j is running and credentials are correct
3. **URL fetching**: Check internet connection and URL accessibility
4. **Memory issues**: Large text files may require sufficient RAM

### Debug Mode

Use `--verbose` for detailed error messages and processing information.

### Dry Run

Use `--dry-run` to see what would be processed without actually doing it.

## Integration with Main Application

This pipeline is designed to work alongside the main IITM BS Xplore application:

- Uses the same URL processing logic
- Compatible with existing Neo4j setup
- Can be run independently or as part of a larger workflow

## Future Enhancements

Potential improvements:
- Parallel processing for faster URL fetching
- Text chunking for very large documents
- Advanced NLP processing before Neo4j upload
- Integration with Neo4j's AI/ML features
- Real-time processing and updates
