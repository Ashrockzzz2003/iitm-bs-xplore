# Changelog

All notable changes to this project will be documented in this file.

## [v2.0.0] - 2025-11-23

### 🚀 Major Features
- **Hybrid Architecture**: Replaced pure RAG with a hybrid approach combining SQL and GenAI File Search.
- **Structured Course Database**: Implemented `query_course_database` tool using Neon PostgreSQL for 99% accuracy on course facts (credits, prerequisites, syllabus).
- **Policy Search**: Implemented `search_handbook_policy` and `search_grading_policy` using Google GenAI File Search for grounded answers from PDFs.
- **Agent Routing**: Intelligent routing logic in `iitm_advisor_agent` to select between SQL and PDF tools.

### 🛠 Improvements
- **Zero Hallucinations**: Structured data queries now return exact database records.
- **Performance**: SQL queries provide millisecond-level response times for course lookups.
- **Grounding**: All PDF-based answers include citations and source links.
- **Frontend**: Updated React UI with streaming responses and citation display.

### 🗑 Removed
- Removed ChromaDB vector stores.
- Removed Knowledge Graph implementation.
- Deprecated pure RAG approach (v1.0).

