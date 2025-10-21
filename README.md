# IITM BS Xplore

## Problem Statement

-   Students face difficulty planning academic progression (which courses to take according to prerequisite requirements, academic goals, number of terms in which they wish to complete the program).
-   Information is spread across websites, student handbooks, grading documents, and other PDFs.

✦ Similar challenges exist in most universities and online education platforms where course structures are complex and requirements vary.

---

## Target Users

-   Students enrolled in the online program
-   Academic advisors/staff assisting students with course planning
-   Prospective learners exploring program requirements

✦ Can extend to learners across MOOCs, degree programs, or professional certifications.

---

## Feasibility & Data Sources

-   **IITM online degree website**: Academics page, Course pages, NPTEL website for electives
-   **Documents**: Grading document, Student handbook
-   **Control UI**: Allows staff to configure additional URLs/PDFs

✦ Generic sources: University/college/MOOC websites, program brochures, policy handbooks.

### Data Sources List

#### DS

-   [https://study.iitm.ac.in/ds/academics.html\#AC1](https://study.iitm.ac.in/ds/academics.html#AC1)
    -   All course subpages linked in this page
    -   Pattern \- [https://study.iitm.ac.in/ds/course_pages/{course_id}.html](https://study.iitm.ac.in/ds/course_pages/BSSE2001.html)
-   [https://study.iitm.ac.in/ds/admissions.html\#AD0](https://study.iitm.ac.in/ds/admissions.html#AD0)
-   Student Handbook \- link sourced from [acegrade.in](http://acegrade.in)
    -   [https://docs.google.com/document/u/1/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub](https://docs.google.com/document/u/1/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub)
-   Grading Policy \- link sourced from [acegrade.in](http://acegrade.in)
    -   [https://docs.google.com/document/u/1/d/e/2PACX-1vRKOWaLjxsts3qAM4h00EDvlB-GYRSPqqVXTfq3nGWFQBx91roxcU1qGv2ksS7jT4EQPNo8Rmr2zaE9/pub\#h.cbcq4ial1xkk](https://docs.google.com/document/u/1/d/e/2PACX-1vRKOWaLjxsts3qAM4h00EDvlB-GYRSPqqVXTfq3nGWFQBx91roxcU1qGv2ksS7jT4EQPNo8Rmr2zaE9/pub#h.cbcq4ial1xkk)

#### ES

-   [https://study.iitm.ac.in/es/academics.html\#AC1](https://study.iitm.ac.in/es/academics.html#AC1)
    -   All course subpages linked in this page
    -   Pattern \- [https://study.iitm.ac.ine/es/course_pages/{course_id}.html](https://study.iitm.ac.ine/es/course_pages/{course_id}.html)
-   [https://study.iitm.ac.in/es/admissions.html\#AD0](https://study.iitm.ac.in/es/admissions.html#AD0)
-   [https://study.iitm.ac.in/es/inthemedia.html](https://study.iitm.ac.in/es/inthemedia.html)
-   [https://study.iitm.ac.in/es/archive.html](https://study.iitm.ac.in/es/archive.html)
-   [https://study.iitm.ac.in/es/faq.html](https://study.iitm.ac.in/es/faq.html)
-   Similarly other links for ES

#### Anonymous

-   [https://study.iitm.ac.in/ds/student_life.html](https://study.iitm.ac.in/ds/student_life.html)
-   [https://paradox-showcase.web.app/](https://paradox-showcase.web.app/)
-   [https://study.iitm.ac.in/student-achievements/interns](https://study.iitm.ac.in/student-achievements/interns)
-   [https://study.iitm.ac.in/ds/testimonials.html](https://study.iitm.ac.in/ds/testimonials.html)
-   [https://study.iitm.ac.in/student-achievements/toppers](https://study.iitm.ac.in/student-achievements/toppers)
-   [https://study.iitm.ac.in/student-achievements/projects](https://study.iitm.ac.in/student-achievements/projects)
-   Docs listed in
    -   [https://study.iitm.ac.in/ds/archive.html](https://study.iitm.ac.in/ds/archive.html)
-   [https://study.iitm.ac.in/ds/aboutIITM.html](https://study.iitm.ac.in/ds/aboutIITM.html)
-   Future
    -   [https://bsinsider.in/](https://bsinsider.in/)
    -   [https://podgoodies.iitmadrasonline.in/](https://podgoodies.iitmadrasonline.in/)
-   Any Additional PDF docs can be added through Control UI by authorized personnel.

---

## Existing Solutions & Limitations

-   Dedicated sessions for course selection and orientation sessions for different courses
-   Scattered information across websites & documents

✦ Existing university chatbots are often FAQ/rule-based and lack personalization or academic planning capability.

---

## Proposed Solution

A **scraper** to extract structured/unstructured data from websites & documents.

### Approach I: KG + RAG based pipeline

-   **Knowledge Graph (KG)** will store rules: Course prerequisites, Credit requirements for any level, Course mapping to levels, Compulsory courses per level
-   **Retrieval Augmented Generation (RAG)** will store unstructured descriptive context about a course or topic.

### Approach II: Multi-Agent Orchestration

Each agent will have its own responsibility:

-   **Data Agent** – Fetch info about a particular course or topic
-   **Validation Agent** – Check prerequisites for a course
-   **Recommendation Agent** – Suggest courses/paths

### UI for Students

Natural language query interface, e.g.:

-   _"I have completed 2 courses (X & Y) of the diploma level (DS) and plan to complete my diploma in the next 2 terms. Which courses should I take next term that continue from X & Y?"_
-   _"I have already completed the Deep Learning course and want to do some hands-on work. Which elective course would best help me with this?"_

### Control UI for Staff

-   Manage/update data sources dynamically
-   Add new sources (websites, PDFs, brochures)

✦ **Generic applicability**: The same pipeline can be applied to any academic institution or program.

---

## 🚀 Current Implementation Status

### ✅ Completed Features

-   **Daily Data Pipeline**: Automated scraping of 127+ IITM DS/ES pages with 7+ lakh characters of content
-   **Hierarchical Text Organization**: Content organized by program and level (ds/{level}/content.txt, es/{level}/content.txt)
-   **ChromaDB RAG Pipeline**: Vector embeddings using Google Gemini for semantic search across 50k-2L character collections
-   **Multi-Agent AI System**: Google ADK-based agents with ChromaDB integration for RAG capabilities
-   **Complete DS Agent Suite**: All three DS agents implemented (Foundation, Diploma, Degree levels)
-   **Enhanced ChromaDB Tools**: Advanced querying capabilities with smart_query, program/level filtering, and metadata support
-   **Chunked Data Processing**: Improved retrieval precision with chunked content and similarity scoring
-   **Agent Orchestration Framework**: Architecture for sub-agents and orchestrator agent routing

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    IITM BS Xplore Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Text Aggregation │    │  ChromaDB RAG   │
│                 │    │                  │    │                 │
│ • DS Academics  │───▶│ • 127+ pages     │───▶│ • Collections   │
│ • ES Academics  │    │ • 7L+ chars      │    │ • 50k-2L chars  │
│ • Course Pages  │    │ • Hierarchical   │    │ • Gemini Embed  │
│ • Daily Updates │    │ • Chunked Data   │    │ • Vector Search │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Agent System                              │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Enhanced        │    │  DS Agent Suite │    │  Context     │ │
│  │ ChromaDB Tools  │───▶│                 │    │  Agent       │ │
│  │                 │    │ • Foundation    │    │              │ │
│  │ • smart_query   │    │ • Diploma       │    │ • Ask for    │ │
│  │ • Program/Level │    │ • Degree        │    │   Program    │ │
│  │ • Metadata      │    │ • Specialized   │    │ • Clarify    │ │
│  │ • Chunked Data  │    │   Knowledge     │    │   Level      │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface                               │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Web UI         │    │  Natural        │    │  Student     │ │
│  │  (Google ADK)   │    │  Language       │    │  Interface   │ │
│  │                 │    │  Queries        │    │              │ │
│  │ • Chat Interface│    │                 │    │ • Course     │ │
│  │ • Real-time     │    │ • "What courses │    │   Planning   │ │
│  │   Responses     │    │   should I take │    │ • Prereq     │ │
│  │ • Context Aware │    │   next term?"   │    │   Validation │ │
│  │ • Multi-Agent   │    │ • Level-specific│    │ • Academic   │ │
│  │   Routing       │    │   Queries       │    │   Guidance   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 📁 Chunking Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    IITM BS Xplore Chunking Pipeline             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Content   │    │  Text Processing │    │  Chunking Logic │
│                 │    │                  │    │                 │
│ • HTML Pages    │───▶│ • Clean HTML     │───▶│ • Split by Size │
│ • PDF Documents │    │ • Extract Text   │    │ • Split by Topic│
│ • Course Pages  │    │ • Remove Noise   │    │ • Overlap Chunks│
│ • 127+ Sources  │    │ • Normalize Text │    │ • Metadata Tags │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Chunked Content Storage                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Chunk Metadata │    │  Content Chunks │    │  Embeddings  │ │
│  │                 │    │                 │    │              │ │
│  │ • Program (DS/ES)│   │ • 1000-2000     │    │ • Gemini     │ │
│  │ • Level         │    │   characters    │    │   Embeddings │ │
│  │ • Course ID     │    │ • Semantic      │    │ • 768 dims   │ │
│  │ • URL Source    │    │   boundaries    │    │ • Vector DB  │ │
│  │ • Chunk Index   │    │ • Overlap for   │    │ • Similarity │ │
│  │ • Timestamp     │    │   context       │    │   Search     │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChromaDB Collections                         │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  DS Collections │    │  ES Collections │    │  Generic     │ │
│  │                 │    │                 │    │  Collections │ │
│  │ • ds_foundation │    │ • es_foundation │    │ • generic    │ │
│  │ • ds_diploma    │    │ • es_diploma    │    │ • main       │ │
│  │ • ds_degree     │    │ • es_degree     │    │ • shared     │ │
│  │                 │    │                 │    │              │ │
│  │ Each collection:│    │ Each collection:│    │ Cross-program│ │
│  │ • 50k-200k chars│    │ • 50k-200k chars│    │   content    │ │
│  │ • 100-500 chunks│    │ • 100-500 chunks│    │ • Common     │ │
│  │ • Program-specific│  │ • Program-specific│  │   policies   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 📁 Project Structure

```
├── xplorer/               # Data Pipeline & ChromaDB
│   ├── util/
│   │   ├── chromadb/      # ChromaDB upload & query tools
│   │   └── hierarchical_aggregator.py
│   ├── outputs/           # Hierarchical content storage
│   │   ├── ds/            # Data Science program
│   │   │   ├── foundation/content.txt
│   │   │   ├── diploma/content.txt
│   │   │   └── degree/content.txt
│   │   └── es/            # Electronics Systems program
│   │       ├── foundation/content.txt
│   │       ├── diploma/content.txt
│   │       └── degree/content.txt
│   └── app.py             # Main data pipeline
├── ai/                    # Multi-Agent AI System
│   ├── agents/
│   │   ├── ds/            # Data Science Agents (Complete)
│   │   │   ├── foundation/ # DS Foundation Level Agent ✅
│   │   │   ├── diploma/   # DS Diploma Level Agent ✅
│   │   │   └── degree/    # DS Degree Level Agent ✅
│   │   ├── es/            # Electronics Systems Agents (Planned)
│   │   │   ├── foundation/ # ES Foundation Level Agent (planned)
│   │   │   ├── diploma/   # ES Diploma Level Agent (planned)
│   │   │   └── degree/    # ES Degree Level Agent (planned)
│   │   └── tools/         # Enhanced ChromaDB query tools
│   │       └── chromadb_tools.py # Advanced querying capabilities
│   └── requirements.txt
└── kg/                    # Legacy Knowledge Graph (paused)
    └── ...                # Neo4j integration (not actively used)
```

**Key Features**: Daily data pipeline, hierarchical organization, ChromaDB RAG, Google ADK agents, orchestrated sub-agents

## 🚀 Quick Start

### 1. Data Pipeline & ChromaDB Setup

```bash
cd xplorer/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start ChromaDB server (in separate terminal)
chroma run --host localhost --port 8000

# Run daily data pipeline - scrapes 127+ pages and organizes hierarchically
python app.py
```

This will:

-   Scrape IITM DS/ES academics pages and all course pages
-   Parse and organize content into `outputs/ds/{level}/content.txt` and `outputs/es/{level}/content.txt`
-   Generate ChromaDB collections with Gemini embeddings for each content file
-   Process 7+ lakh characters across 127+ pages

### 2. AI Agents Setup

```bash
cd ai/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables in a .env file
echo "CHROMA_HOST=localhost" >> .env
echo "CHROMA_PORT=8000" >> .env
echo "GOOGLE_API_KEY=your_gemini_api_key" >> .env

# Run any of the available DS agents with web UI
cd agents/ds/foundation/  # For Foundation Level Agent
# OR
cd agents/ds/diploma/     # For Diploma Level Agent
# OR
cd agents/ds/degree/      # For Degree Level Agent

adk web
```

This will:

-   Start the selected DS agent (Foundation, Diploma, or Degree level)
-   Launch Google ADK web interface for testing
-   Enable natural language queries about the specific level
-   Provide context-aware responses using enhanced ChromaDB RAG
-   Access specialized knowledge for each academic level

### 3. Legacy Knowledge Graph (Optional)

```bash
cd kg/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Parse single URLs (legacy approach - paused)
python app.py --url https://study.iitm.ac.in/ds/academics.html
```

## 🔧 How It Works

### Daily Data Pipeline

1. **Web Scraping**: Automated scraping of IITM DS/ES academics pages and all course pages
2. **Content Parsing**: Extracts and cleans text content from 127+ pages
3. **Hierarchical Organization**: Organizes content by program and level:
    - `outputs/ds/foundation/content.txt` (Data Science Foundation)
    - `outputs/ds/diploma/content.txt` (Data Science Diploma)
    - `outputs/ds/degree/content.txt` (Data Science Degree)
    - `outputs/es/foundation/content.txt` (Electronics Systems Foundation)
    - `outputs/es/diploma/content.txt` (Electronics Systems Diploma)
    - `outputs/es/degree/content.txt` (Electronics Systems Degree)
4. **Content Processing**: Processes 7+ lakh characters across all levels

### ChromaDB RAG Pipeline

1. **Collection Creation**: Each content.txt file becomes a unique ChromaDB collection
2. **Vector Embeddings**: Uses Google Gemini `gemini-embedding-001` model for embeddings
3. **Collection Management**: Collections range from 50k to 2 lakh characters each
4. **Semantic Search**: Enables natural language queries across all content

### AI Agent System

1. **Sub-Agent Architecture**: Specialized agents for each program-level combination
2. **ChromaDB Integration**: Agents query relevant collections for context
3. **RAG Pipeline**: Retrieval-Augmented Generation for accurate, context-aware responses
4. **Orchestrator Agent**: Routes queries to appropriate sub-agents
5. **Context Agent**: Asks for clarification when program/level is ambiguous
6. **Web UI**: Google ADK provides built-in web interface for testing

### Agent Orchestration Flow

1. **Query Reception**: User asks natural language question
2. **Orchestrator Routing**: Determines which sub-agent can best answer
3. **Context Clarification**: If needed, asks user for program/level specification
4. **Sub-Agent Processing**: Relevant agent queries ChromaDB for context
5. **Response Generation**: Agent provides context-aware answer using RAG
6. **User Interaction**: Response delivered through web UI

## 📊 Data Pipeline Output

### Content Organization

```
outputs/
├── ds/                     # Data Science Program
│   ├── foundation/         # Foundation Level
│   │   └── content.txt     # ~50k-100k characters
│   ├── diploma/            # Diploma Level
│   │   └── content.txt     # ~100k-150k characters
│   └── degree/             # Degree Level
│       └── content.txt     # ~150k-200k characters
└── es/                     # Electronics Systems Program
    ├── foundation/         # Foundation Level
    │   └── content.txt     # ~50k-100k characters
    ├── diploma/            # Diploma Level
    │   └── content.txt     # ~100k-150k characters
    └── degree/             # Degree Level
        └── content.txt     # ~150k-200k characters
```

### ChromaDB Collections

-   **Collection Names**: `{program}_{level}` (e.g., `ds_foundation`, `es_diploma`)
-   **Embeddings**: Google Gemini `gemini-embedding-001` (768 dimensions)
-   **Content Range**: 50k to 2 lakh characters per collection
-   **Total Content**: 7+ lakh characters across all collections

## 🎯 Use Cases

### Current Capabilities

-   **Daily Data Updates**: Automated scraping and processing of 127+ IITM pages
-   **Hierarchical Content Organization**: Structured storage by program and level
-   **Enhanced Semantic Search**: Advanced ChromaDB querying with smart_query, program/level filtering
-   **Complete DS Agent Suite**: All three DS agents (Foundation, Diploma, Degree) fully implemented
-   **Chunked Data Processing**: Improved retrieval precision with similarity scoring
-   **Web Interface**: Google ADK built-in web UI for testing and interaction
-   **Context-Aware Responses**: RAG-powered answers with relevant course information
-   **Metadata-Rich Queries**: Access to course IDs, URLs, and chunk information

### AI Agent Capabilities

-   **DS Foundation Agent**: Specialized knowledge for foundational Data Science concepts and courses
-   **DS Diploma Agent**: Expertise in both Diploma in Programming and Diploma in Data Science tracks
-   **DS Degree Agent**: Advanced knowledge for degree-level Data Science courses and requirements
-   **Enhanced ChromaDB Integration**: Smart querying across multiple collections with automatic routing
-   **Advanced RAG Pipeline**: Context-aware responses using chunked data and similarity scoring
-   **Natural Language Processing**: Understands complex academic queries with level-specific context
-   **Program-Specific Knowledge**: Specialized knowledge for each academic level and program track

### Example Queries

**Foundation Level:**

-   "What courses should I take in my next term for DS foundation level?"
-   "Which foundation courses are most important for data science?"
-   "What are the prerequisites for foundation level courses?"

**Diploma Level:**

-   "What's the difference between Diploma in Programming and Diploma in Data Science?"
-   "Which diploma courses should I take after completing foundation?"
-   "What are the requirements for diploma level courses?"

**Degree Level:**

-   "What are the prerequisites for BSDA1001?"
-   "Which degree level courses are most challenging?"
-   "What's the difference between DS and ES foundation courses?"

## 🚀 Next Steps

### Immediate Development

-   **ES Agent Suite**: Complete Electronics Systems agents (Foundation, Diploma, Degree levels)
-   **Orchestrator Agent**: Central agent to route queries to appropriate sub-agents
-   **Context Agent**: Agent to ask for clarification when program/level is ambiguous
-   **Enhanced Web UI**: Improved user interface for better interaction
-   **Cross-Program Queries**: Agents that can answer questions spanning multiple programs

### Future Enhancements

-   **Advanced Analytics**: Course difficulty analysis and success prediction
-   **Integration APIs**: REST APIs for external system integration
-   **Mobile Interface**: Mobile-optimized student interface
-   **Real-time Updates**: Dynamic data source updates and synchronization
-   **Multi-Program Orchestration**: Unified interface for DS and ES program queries

This system enables building:

-   Intelligent course recommendation systems with AI agents
-   Academic planning assistants with context-aware responses
-   Prerequisite validation tools with semantic search
-   Curriculum analysis dashboards with hierarchical data
-   Multi-agent educational platforms with orchestrated sub-agents
