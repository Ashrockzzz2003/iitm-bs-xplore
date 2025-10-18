# IITM BS Xplore - Direct Text Extraction Pipeline

A production-ready pipeline for extracting text content from HTML pages and organizing it hierarchically.

## Overview

This pipeline provides two storage modes:

### Single File Mode (Legacy)
1. Fetches HTML from multiple parent URLs (DS, ES academics pages) and all linked course pages
2. Extracts plain text content from HTML (removing tags, scripts, styles)
3. Combines all text into a single large txt file with clear URL separators

### Hierarchical Mode (Recommended)
1. Fetches and extracts text content as above
2. Organizes content into hierarchical directory structure:
   - `outputs/generic/content.txt` - Main/academics content from all programs
   - `outputs/ds/{level}/content.txt` - DS program courses by level
   - `outputs/es/{level}/content.txt` - ES program courses by level

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
# Extract text from DS program only (single file mode)
python main.py ds

# Extract text from both DS and ES programs (single file mode)
python main.py ds es

# Extract with hierarchical storage (recommended)
python main.py ds es --hierarchical

# Dry run to see what would be processed
python main.py ds es --hierarchical --dry-run
```

## Command Line Options

### Required Arguments
- `programs`: Programs to process (ds, es, or both) - positional argument

### Optional Flags
- `--hierarchical`: Use hierarchical storage structure (recommended)
- `--dry-run`: Show what would be done without actually doing it

### Configuration
- Output directory: `outputs/` (fixed)
- Single file output: `outputs/combined_text.txt` (fixed)

## Storage Modes

### Single File Mode
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

### Hierarchical Mode (Recommended)
The pipeline generates a hierarchical directory structure:

```
outputs/
├── generic/
│   └── content.txt          # Main/academics content from all programs
├── ds/
│   ├── foundation/
│   │   └── content.txt      # DS foundation level courses
│   ├── diploma/
│   │   └── content.txt      # DS diploma level courses
│   └── degree/
│       └── content.txt      # DS degree level courses
└── es/
    ├── foundation/
    │   └── content.txt      # ES foundation level courses
    ├── diploma/
    │   └── content.txt      # ES diploma level courses
    └── degree/
        └── content.txt      # ES degree level courses
```

Each content file follows the same format as the single file mode, but contains only content for that specific program and level combination.

**Benefits of Hierarchical Mode:**
- Better organization by program and academic level
- Easier to navigate and find specific content
- More scalable for large datasets
- Maintains all metadata and relationships

## Module Structure

- `main.py` - Main orchestration script with CLI
- `hierarchical_aggregator.py` - Hierarchical text organization and storage
- `text_aggregator.py` - Single file text combination (legacy mode)
- `text_extractor.py` - HTML to text extraction
- `url_fetcher.py` - URL fetching and course link extraction
- `setup.py` - Package setup and installation
- `requirements.txt` - Python dependencies

## Error Handling

The pipeline includes comprehensive error handling:

- **Network errors**: Retries and graceful failure for URL fetching
- **Parsing errors**: Continues processing other URLs if one fails
- **File errors**: Proper file handling and encoding support

## Performance

Typical performance metrics:
- **DS program**: ~50-80 course URLs, ~500KB-1MB text
- **ES program**: ~40-60 course URLs, ~400KB-800KB text
- **Processing time**: 2-5 minutes for both programs

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running from the `direct/` directory
2. **URL fetching**: Check internet connection and URL accessibility
3. **Memory issues**: Large text files may require sufficient RAM

### Dry Run

Use `--dry-run` to see what would be processed without actually doing it.

## Integration with Main Application

This pipeline is designed to work alongside the main IITM BS Xplore application:

- Uses the same URL processing logic
- Can be run independently or as part of a larger workflow

## Future Enhancements

Potential improvements:
- Parallel processing for faster URL fetching
- Text chunking for very large documents
- Advanced NLP processing
- Real-time processing and updates
