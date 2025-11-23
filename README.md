# IITM BS Xplore

> **Current Version: v2.0.0**
> Intelligent querying system for IITM course information and academic documents powered by Google GenAI and Neon PostgreSQL.

![IITM BS Xplore UI](docs/ui.png)

## 🚩 Problem Statement

-   Students face difficulty planning academic progression (which courses to take according to prerequisite requirements, academic goals, number of terms in which they wish to complete the program).
-   Information is spread across websites, student handbooks, grading documents, and other PDFs.

> ✦ Similar challenges exist in most universities and online education platforms where course structures are complex and requirements vary.

## 🎯 Target Users

-   **Students**: Enrolled in the online program needing guidance.
-   **Academic Advisors**: Staff assisting students with course planning.
-   **Prospective Learners**: Exploring program requirements.

## 🧩 Existing Solutions & Limitations

-   Dedicated sessions for course selection and orientation sessions.
-   Scattered information across websites & documents.

## 🏗️ Architecture

```mermaid
graph TD
    Frontend[Frontend Web<br>React + Vite] <-->|REST API| Agent[IITM Advisor Agent<br>Google ADK Agent with Gemini 3 Pro]

    Agent -->|Uses 3 Specialized Tools| HPS[Handbook Policy Search]
    Agent -->|Uses 3 Specialized Tools| GPS[Grading Policy Search]
    Agent -->|Uses 3 Specialized Tools| CDQ[Course Database Query]

    HPS & GPS --> GenAI[Google GenAI File Search API<br>• Semantic search over PDF documents<br>• Returns answers with grounding sources<br>• Model: gemini-3-pro-preview]

    GenAI -->|Queries| SH[student_handbook.pdf]
    GenAI -->|Queries| GD[grading_doc.pdf]

    CDQ --> Neon[Neon PostgreSQL Database<br>• Serverless PostgreSQL hosted at *.neon.tech<br>• Automatic SSL/endpoint configuration]

    Neon --> Courses[courses table<br>• course_code<br>• title<br>• description<br>• credits<br>• level<br>• instructors<br>• syllabus<br>• prerequisites<br>• ...]
    Neon --> Mappings[file_search_store_mappings table<br>• pdf_path<br>• store_name<br>Maps PDFs to GenAI file search stores]
```

### Architecture Components

#### 1. **Frontend Application** (`app/`)

-   **Technology**: React 19, Vite, Tailwind CSS, Lucide React
-   **Features**:
    -   Chat interface with streaming responses
    -   Markdown rendering for rich text answers
    -   Citations and grounding sources display
    -   Responsive design

#### 2. **IITM Advisor Agent** (`agents/iitm_advisor_agent/agent.py`)

-   Built with Google ADK (Agent Development Kit)
-   Uses Gemini 3 Pro Preview model
-   Intelligent tool routing based on query type
-   Synthesizes responses from multiple data sources
-   Exposed as a REST API using FastAPI via `agents/main.py`

#### 3. **Google GenAI File Search**

-   **Purpose**: Semantic search and Q&A over PDF documents
-   **Technology**: Google GenAI SDK (`google-genai`)
-   **Model**: `gemini-3-pro-preview` (default)
-   **Documents**:
    -   `student_handbook.pdf` - Academic policies, eligibility, program structure
    -   `grading_doc.pdf` - Grading policies, assessment structures, GPA calculation
-   **Features**:
    -   Automatic store name lookup from database
    -   Returns answers with grounding sources
    -   Full grounding metadata for traceability

#### 4. **Neon PostgreSQL Database**

-   **Purpose**: Structured course information storage
-   **Technology**: Serverless PostgreSQL via Neon
-   **Connection**: Automatic SSL/endpoint configuration for Neon
-   **Tables**:
    -   `courses` - Comprehensive course catalog data
    -   `file_search_store_mappings` - PDF to GenAI store mappings

### 🧠 Design Philosophy: The Hybrid Approach

Why two different data systems?

-   **Structured Data (SQL)**: Course information (credits, prerequisites, syllabus) is composed of structured facts. Vector search (RAG) often struggles with precise numerical or boolean queries (e.g., "Which courses have exactly 4 credits?"). By extracting this into a Postgres database, we achieve **99% accuracy** on course-related queries.
-   **Unstructured Data (GenAI File Search)**: Policies and handbooks are dense text requiring semantic understanding. Google's GenAI File Search excels here, providing grounded answers with citations.

For the full story of how we evolved from a pure RAG/Knowledge Graph approach ([v1.0](https://github.com/Ashrockzzz2003/iitm-bs-xplore/tree/v1.0.0)) to this hybrid solution, see [STORY.md](STORY.md).

## 📦 Project Structure

```
iitm-bs-xplore/
├── agents/
│   ├── iitm_advisor_agent/
│   │   └── agent.py              # Main ADK agent with routing logic
│   ├── tools/
│   │   ├── __init__.py           # Tool exports
│   │   ├── tools.py              # ADK-compatible tool wrappers
│   │   ├── file_search_query.py  # PDF query implementation
│   │   └── query_neon.py         # Database query implementation
│   ├── main.py                   # FastAPI server entry point
│   └── requirements.txt          # Agent dependencies
├── app/                          # Frontend Application
│   ├── components/               # React UI components
│   ├── services/                 # API integration services
│   ├── constants.ts              # App constants & Config
│   ├── App.tsx                   # Main App component
│   ├── index.html                # Entry HTML
│   └── package.json              # Frontend dependencies
├── data/
│   ├── dump/
│   │   ├── student_handbook.pdf  # Student handbook PDF
│   │   ├── grading_doc.pdf       # Grading document PDF
│   │   └── academics.html        # Course listings HTML
│   ├── util/
│   │   ├── file_search.py        # File search initialization
│   │   ├── course.py             # Course data utilities
│   │   └── academics.py          # Academics page parsing
│   ├── config/                   # Configuration modules
│   ├── setup_db.py               # Database schema setup
│   └── app.py                    # Main application
└── README.md                     # This file
```

## 🛠️ Available Tools

The system provides three specialized tools for the agent:

### 1. `search_handbook_policy(query, model=None)`

Search the IITM BS student handbook for policy and rule information.

**Use for:**

-   Eligibility criteria and admission requirements (Regular/JEE)
-   Fees, scholarships, and financial information
-   Document verification procedures
-   Program structure and exit options
-   Maximum duration (8 years) and CCC (Credit Clearing Capability)
-   Academic rules and regulations

**Returns:**

```python
{
    "response": str,              # Generated answer
    "sources": [                  # Grounding sources
        {"title": str, "uri": str}
    ],
    "grounding_metadata": object, # Full grounding metadata
    "query": str,                 # Original query
    "model": str,                 # Model used
    "store_name": str             # Store name used
}
```

### 2. `search_grading_policy(query, model=None)`

Search the IITM BS grading policy document for assessment and grading information.

**Use for:**

-   Grading scale (S, A, B, C, D, E, U grades)
-   GPA and CGPA calculation methods
-   Assignment weightage and assessment structure
-   "Best of X" rules for assignments/exams
-   Eligibility criteria for End-Term exams
-   Marks distribution and evaluation policies

**Returns:** Same structure as `search_handbook_policy`

### 3. `query_course_database(query, params=None)`

Query the IITM course knowledge database for structured course information.

**Use for:**

-   Course specifics: syllabus topics, instructor names, credit count, titles
-   Course lists: "List all Diploma courses", "Show courses with 4 credits"
-   Course details: descriptions, prerequisites, learning outcomes

**Important Notes:**

-   Only SELECT queries are allowed (read-only for safety)
-   Use exact level names: `"Foundation Level"`, `"Diploma Level"`, `"BSc Degree Level"`, `"BS Degree Level"`
-   Use `ILIKE` for case-insensitive matching (e.g., `title ILIKE '%python%'`)

**Returns:**

```python
{
    "rows": [                     # List of dicts (column names as keys)
        {"course_code": "...", "title": "...", ...}
    ],
    "row_count": int,             # Number of rows returned
    "columns": [str],             # Column names
    "query": str                  # Executed query
}
```

## 🗄️ Database Schema

### `courses` Table

Stores comprehensive course information from IITM's course catalog:

| Column                 | Type         | Description                                                                |
| ---------------------- | ------------ | -------------------------------------------------------------------------- |
| `course_code`          | VARCHAR(50)  | Primary key, e.g., "BSMA1001"                                              |
| `title`                | VARCHAR(500) | Course title                                                               |
| `description`          | TEXT         | Course description                                                         |
| `credits`              | INTEGER      | Number of credits                                                          |
| `level`                | VARCHAR(100) | "Foundation Level", "Diploma Level", "BSc Degree Level", "BS Degree Level" |
| `prerequisites`        | TEXT         | Prerequisite courses/knowledge                                             |
| `video_link`           | VARCHAR(500) | Course introduction video URL                                              |
| `instructors`          | JSONB        | Array of instructor objects                                                |
| `learning_outcomes`    | JSONB        | Array of learning outcomes                                                 |
| `syllabus`             | JSONB        | Array of week-by-week syllabus                                             |
| `resources_and_books`  | JSONB        | Array of books/resources                                                   |
| `assessment_structure` | TEXT         | Grading/assessment description                                             |
| `extra`                | JSONB        | Additional metadata                                                        |
| `source_url`           | VARCHAR(500) | Original course page URL                                                   |
| `status`               | VARCHAR(20)  | 'active' or 'wip' (default: 'active')                                      |
| `created_at`           | TIMESTAMP    | Creation timestamp                                                         |
| `last_updated`         | TIMESTAMP    | Last update timestamp                                                      |

**Indexes:**

-   Primary key on `course_code`
-   Index on `level` for faster filtering

### `file_search_store_mappings` Table

Maps PDF filenames to their Google GenAI file search store names:

| Column         | Type          | Description                                              |
| -------------- | ------------- | -------------------------------------------------------- |
| `pdf_path`     | VARCHAR(1000) | Primary key, PDF filename (e.g., "student_handbook.pdf") |
| `store_name`   | VARCHAR(500)  | GenAI file search store name                             |
| `created_at`   | TIMESTAMP     | Creation timestamp                                       |
| `last_updated` | TIMESTAMP     | Last update timestamp                                    |

**Indexes:**

-   Primary key on `pdf_path`
-   Index on `store_name` for faster lookups

## 🔄 Data Flow

### PDF Query Flow

```
User Query
    ↓
Agent routes to search_handbook_policy or search_grading_policy
    ↓
Tool looks up store_name from file_search_store_mappings table
    ↓
Calls Google GenAI File Search API with store_name
    ↓
GenAI searches PDF chunks semantically
    ↓
Returns answer with grounding sources
    ↓
Agent synthesizes response
```

### Course Database Query Flow

```
User Query
    ↓
Agent routes to query_course_database
    ↓
Tool validates query is SELECT-only
    ↓
Executes parameterized query on Neon PostgreSQL
    ↓
Returns structured course data (rows, columns, count)
    ↓
Agent formats response (tables, lists, etc.)
```

## ⚙️ Setup & Configuration

### Prerequisites

-   Node.js 18+ (for Frontend)
-   Python 3.9+ (for Backend)
-   Google GenAI API key
-   Neon PostgreSQL database

### Backend Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd iitm-bs-xplore
```

2. **Install backend dependencies:**

```bash
# Agent dependencies
pip install -r agents/requirements.txt

# Data processing dependencies (if needed)
pip install -r data/requirements.txt
```

3. **Set up environment variables:**
   Create a `.env` file in the project root:

```env
# Required
GEMINI_API_KEY=your_google_genai_api_key
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname

# Optional
GENAI_FILE_SEARCH_STORE_NAME=default_store_name
GENAI_MODEL_ID=gemini-3-pro-preview
PORT=8080
```

4. **Initialize database:**

```bash
cd data
python setup_db.py
```

5. **Initialize file search stores:**
   Upload PDFs to GenAI file search and store mappings in the database:

```python
from data.util.file_search import initialize_file_search_store

# Initialize student handbook
initialize_file_search_store("data/dump/student_handbook.pdf")

# Initialize grading document
initialize_file_search_store("data/dump/grading_doc.pdf")
```

### Frontend Installation

1. **Install dependencies:**

```bash
cd app
npm install
```

2. **Configuration:**
   The frontend connects to the backend via `API_URL` in `app/constants.ts`.
   By default it points to the deployed production instance.
   For local development, update `app/constants.ts`:

```typescript
export const API_URL = "http://localhost:8080";
```

### Running the Application

1. **Start the Backend Server:**

```bash
# From project root
python agents/main.py
# Server runs at http://localhost:8080
```

2. **Start the Frontend Development Server:**

```bash
# From app/ directory
npm run dev
# App runs at http://localhost:3000
```

## 🚀 Data Pipeline (Training)

The "training" pipeline acts as the data ingestion system that populates the agent's knowledge base. It transforms unstructured web pages and PDF documents into structured database records and semantic search indices.

### Pipeline Overview

```mermaid
graph TD
    A[Start Pipeline] --> B[Parse Course Listings]
    B --> C{Iterate Courses}
    C -->|For each URL| D[Fetch Page HTML]
    D --> E[Convert to Text]
    E --> F[Use Gemini AI to extract course information as structured JSON]
    F -->|Structured JSON| G["Save to Postgres (courses table)"]
    G --> C
    C -->|Done| H["Initialize PDF Stores (grading_doc, student_handbook)"]
    H --> I[Upload PDFs to GenAI]
    I --> J["Map Stores in DB (to use in retrieval)"]
    J --> K[End]
```

### 1. Course Data Ingestion (`data/app.py`)

This process converts raw HTML course pages into a structured SQL database.

1.  **Listing Discovery**: Parses `data/dump/academics.html` to find all course URLs and their academic levels (Foundation, Diploma, Degree).
2.  **AI Extraction**:
    -   Fetches each course page live from the web.
    -   Converts HTML to text using `html2text`.
    -   **Gemini 3 Pro** processes the text to extract a strict JSON schema (`CoursePageSchema`) containing:
        -   Syllabus (week-by-week)
        -   Instructors (names, bios)
        -   Learning Outcomes
        -   Resources & Textbooks
3.  **Database Storage**: Upserts the structured data into the `courses` table in Neon PostgreSQL.

### 2. PDF Knowledge Base (`data/util/file_search.py`)

This process indexes policy documents for semantic search.

1.  **Document Loading**: Reads PDFs from `data/dump/` (e.g., `student_handbook.pdf`).
2.  **GenAI Indexing**: Uploads documents to Google GenAI File Search.
3.  **Store Mapping**:
    -   Creates or reuses a "File Search Store" for each document.
    -   Maps the local filename to the remote Store ID in the `file_search_store_mappings` table.
    -   This allows the agent to dynamically look up the correct knowledge base for different query types.

### Running the Pipeline

To refresh the database and knowledge base:

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Run the ingestion script
python data/app.py

# Optional: Log output to file
LOG_FILE=data/logs/ingestion.log python data/app.py
```

## 🎯 Agent Routing Logic

The IITM Advisor Agent uses intelligent routing to select the appropriate tool:

### Use `query_course_database` (SQL) for:

-   **Course Specifics:** Syllabus topics, instructor names, credit count, titles
-   **Lists:** "List all Diploma courses", "Show courses with 4 credits"
-   **SQL Guidelines:**
    -   Table: `courses` (cols: `course_code`, `title`, `credits`, `level`, `instructors`, `syllabus`)
    -   Use `ILIKE` for case-insensitive matching (e.g., `title ILIKE '%python%'`)
    -   Select specific columns to keep responses concise
    -   Use exact level names: `"Foundation Level"`, `"Diploma Level"`, `"BSc Degree Level"`, `"BS Degree Level"`

### Use `search_handbook_policy` (PDF) for:

-   **Rules:** Eligibility, admission (Regular/JEE), fees, scholarships, document verification
-   **Structure:** Exit options, maximum duration (8 years), CCC (Credit Clearing Capability)

### Use `search_grading_policy` (PDF) for:

-   **Marks:** Grading scale (S, A, B...), GPA/CGPA calculation
-   **Assessments:** Assignment weightage, "Best of X" rules, eligibility for End-Term exams

## 🔒 Security Features

1. **Read-only Database Access**: Only SELECT queries are allowed
2. **Parameterized Queries**: SQL injection prevention via parameterized queries
3. **Neon Connection Security**: Automatic SSL and channel binding configuration
4. **Store Name Validation**: PDF queries validate store names before execution

## 📚 Key Features

1. **Semantic PDF Search**: Natural language queries over student handbooks and grading documents
2. **Structured Course Data**: Comprehensive course information in a queryable database
3. **Automatic Store Management**: File search stores are automatically mapped and reused
4. **Neon Integration**: Handles Neon-specific connection requirements automatically
5. **Intelligent Routing**: Agent automatically selects the best tool for each query type
6. **Grounding Sources**: All PDF queries return source citations for transparency

## 🧪 Usage Example

```python
from agents.iitm_advisor_agent.agent import root_agent

# The agent automatically routes queries to appropriate tools
response = root_agent.send("What are the eligibility criteria for the qualifier exam?")
# Routes to: search_handbook_policy

response = root_agent.send("List all Foundation Level courses with 4 credits")
# Routes to: query_course_database

response = root_agent.send("How is GPA calculated?")
# Routes to: search_grading_policy
```

## 📦 Dependencies

### Agent Dependencies (`agents/requirements.txt`)

-   `psycopg[binary]`: PostgreSQL database connectivity
-   `python-dotenv`: Environment variable management
-   `google-genai`: Google GenAI SDK for file search
-   `google-adk`: Google Agent Development Kit
-   `fastapi`, `uvicorn`: API Server

### Frontend Dependencies (`app/package.json`)

-   `react`, `react-dom`: UI Framework
-   `vite`: Build tool
-   `lucide-react`: Icons
-   `react-markdown`: Markdown rendering
-   `@copilotkit/*`: Copilot integration

### Data Processing Dependencies (`data/requirements.txt`)

-   `requests`: HTTP requests for web scraping
-   `psycopg[binary]`: PostgreSQL connectivity
-   `pydantic`: Data validation
-   `python-dotenv`: Environment variables
-   `beautifulsoup4`: HTML parsing
-   `google-genai`: GenAI SDK
-   `html2text`: HTML to text conversion

## 🤝 Contributing

1. Follow the existing code structure
2. Maintain type hints and docstrings for ADK compatibility
3. Ensure all tools return TypedDict-compatible results
4. Test with both PDF and database queries

---

**Built with ❤️ for IITM BS Data Science students**
