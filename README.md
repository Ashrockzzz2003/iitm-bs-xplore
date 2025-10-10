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

## 🚀 Parser & Knowledge Graph (Starting Point)

This repository contains the **parser component** - the foundational starting point of the IITM BS Xplore project. The parser extracts program sections, rules, and course information from HTML pages into a structured knowledge graph JSON, featuring automatic parser detection, modular architecture, and advanced visualization capabilities.

## 🏗️ Architecture

### Directory Structure

```
iitm-bs-xplore/
├── app.py                          # Main application entry point
├── visualize_kg.py                 # Visualization CLI entry point
├── requirements.txt                # Dependencies
├── src/                            # Main source code
│   ├── processors/                 # Data processing modules
│   │   ├── url_processor.py        # URL fetching and processing
│   │   └── file_processor.py       # File-based processing
│   ├── visualizers/                # Visualization modules
│   │   ├── kg_visualizer.py        # Core visualization logic
│   │   └── visualization_cli.py    # Visualization CLI
│   ├── utils/                      # Utility modules
│   │   ├── argument_parser.py      # CLI argument parsing
│   │   ├── output_handler.py       # Output file handling
│   │   └── outline_printer.py      # Outline summary printing
│   └── xplore/                     # Core parsing modules
│       ├── academics.py
│       ├── course.py
│       ├── generic.py
│       ├── merge.py
│       ├── outline.py
│       ├── types.py
│       └── utils.py
└── outputs/                        # Generated data files
    ├── *.json                      # Knowledge graph data files
    └── viz/                        # Visualization outputs (PNG, DOT files)
```

### Key Features

1. **Single Responsibility**: Each module has one clear purpose
2. **Clean Separation**: Processing, visualization, and utilities are separate
3. **Maintainable**: Easy to modify individual components
4. **Testable**: Each module can be tested independently
5. **Scalable**: Easy to add new processors or visualizers

## 🚀 Quick Start

### Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Basic Usage

#### Parse from URLs (Recommended)

```bash
# Parse IITM academics page
python app.py --url https://study.iitm.ac.in/ds/academics.html --output kg_academics.json

# Parse a course page
python app.py --url https://study.iitm.ac.in/ds/course_pages/BSDA1001.html --output kg_course.json

# Parse any other website (uses generic parser)
python app.py --url https://example.com/some-page.html --output kg_generic.json
```

#### Parse from Local Files

```bash
python app.py --academics test/data/academics.html --output kg_academics.json
python app.py --course-files test/data/course.html --output kg_course.json
```

#### Generate Outline Summary

```bash
python app.py --url https://study.iitm.ac.in/ds/academics.html --outline-summary
```

## 🎯 Problem Statement

- Students face difficulty planning academic progression (which courses to take according to prerequisite requirements, academic goals, number of terms in which they wish to complete the program)
- Information is spread across websites, student handbooks, grading documents, and other PDFs
- Similar challenges exist in most universities and online education platforms where course structures are complex and requirements vary

## 🔧 How It Works

### Parser Logic

1. **Heading/Outline Detection**
   - Builds an outline from heading tags (`h1`–`h6`) and heading-like elements
   - Each outline node gets: `title`, `level`, `depth`, `anchorId`, and `childCount`
   - Filters low-signal headings and de-duplicates consecutive duplicates

2. **Hierarchy → Knowledge Graph**
   - Creates `Section` nodes for every outline node
   - Hierarchical edges: `HAS_SECTION` from parent to child
   - Sections appear under root `Program` when they have no parent

3. **Level Detection and Grouping**
   - Fuzzy matches classify headings into levels (Foundation, Diploma, BSc, BS)
   - Level nodes linked to program via `HAS_LEVEL`
   - Anchors like `AC11`–`AC16` segment content per level

4. **Content Extraction**
   - Captures bullets, paragraphs, and labeled fields
   - Attaches content to appropriate `Section` nodes

5. **Course Links and Collections**
   - Parses course links from tables and anchors
   - Groups courses into `Collection` nodes
   - Links collections to levels via `HAS` edges

### Automatic Parser Detection

The application automatically detects which parser to use based on the URL:

- **IITM Academics pages** (`study.iitm.ac.in/ds/academics.html`) → `academics` parser
- **IITM Course pages** (`study.iitm.ac.in/ds/course_pages/*.html`) → `course` parser  
- **All other URLs** → `generic` parser

## 📊 Visualization

### Prerequisites

1. **Install Graphviz**:
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

### Generate Visualizations

#### All Visualizations
```bash
python visualize_kg.py outputs/production_full_courses.json
```

This creates four different visualizations in the `outputs/viz/` directory:
- `hierarchical_graph.png` - Shows program structure (Program → Level → Section)
- `course_graph.png` - Focuses on courses and their relationships
- `network_graph.png` - Shows all nodes and relationships in a network layout
- `focused_network.png` - Less cluttered network view with key nodes only

#### Specific Layouts

```bash
# Hierarchical layout (program structure)
python visualize_kg.py outputs/production_full_courses.json --layout hierarchical

# Course-focused layout
python visualize_kg.py outputs/production_full_courses.json --layout network --node-types Course

# Focused network (less cluttered)
python visualize_kg.py outputs/production_full_courses.json --layout focused

# Circular layout
python visualize_kg.py outputs/production_full_courses.json --layout circular
```

#### Filtering Options

```bash
# Limit number of nodes
python visualize_kg.py outputs/production_full_courses.json --max-nodes 50

# Filter by node types
python visualize_kg.py outputs/production_full_courses.json --node-types Program Level Course

# Show statistics
python visualize_kg.py outputs/production_full_courses.json --stats

# Custom output directory
python visualize_kg.py outputs/production_full_courses.json --output-dir my_visualizations
```

### Understanding Visualizations

#### Node Colors
- **Red**: Program nodes
- **Teal**: Level nodes  
- **Blue**: Section nodes
- **Green**: Course nodes
- **Yellow**: Collection nodes
- **Plum**: Other node types

#### Edge Colors
- **Dark Blue**: HAS_LEVEL relationships
- **Dark Gray**: HAS_SECTION relationships
- **Green**: HAS relationships
- **Red**: REQUIRES relationships (prerequisites)
- **Gray**: Other relationships

## 🎯 Parser Target Users

- **Developers** building academic planning tools and course recommendation systems
- **Data Scientists** working with educational data and knowledge graphs
- **Academic Institutions** looking to extract structured data from their course websites
- **Researchers** studying course prerequisites and academic program structures
- **System Integrators** building comprehensive educational platforms

## 📚 Data Sources

### DS (Data Science)
- [Academics page](https://study.iitm.ac.in/ds/academics.html#AC1) - All course subpages
- [Admissions page](https://study.iitm.ac.in/ds/admissions.html#AD0)
- [Student Handbook](https://docs.google.com/document/u/1/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub)
- [Grading Policy](https://docs.google.com/document/u/1/d/e/2PACX-1vRKOWaLjxsts3qAM4h00EDvlB-GYRSPqqVXTfq3nGWFQBx91roxcU1qGv2ksS7jT4EQPNo8Rmr2zaE9/pub#h.cbcq4ial1xkk)

### ES (Electronics Systems)
- [Academics page](https://study.iitm.ac.in/es/academics.html#AC1) - All course subpages
- [Admissions page](https://study.iitm.ac.in/es/admissions.html#AD0)
- Additional pages: inthemedia, archive, faq

### Additional Sources
- Student life pages, testimonials, achievements
- Future sources: bsinsider.in, podgoodies.iitmadrasonline.in
- Any additional PDF docs can be added through Control UI

## 🚀 Proposed Solution

### Approach I: KG + RAG Pipeline
- **Knowledge Graph (KG)** stores rules: Course prerequisites, Credit requirements, Course mapping to levels, Compulsory courses per level
- **Retrieval Augmented Generation (RAG)** stores unstructured descriptive context about courses or topics

### Approach II: Multi-Agent Orchestration
Each agent has specific responsibilities:
- **Data Agent** – Fetch info about courses or topics
- **Validation Agent** – Check prerequisites for courses
- **Recommendation Agent** – Suggest courses/paths

### UI for Students
Natural language query interface:
- _"I have completed 2 courses (X & Y) of the diploma level (DS) and plan to complete my diploma in the next 2 terms. Which courses should I take next term that continue from X & Y?"_
- _"I have already completed the Deep Learning course and want to do some hands-on work. Which elective course would best help me with this?"_

### Control UI for Staff
- Manage/update data sources dynamically
- Add new sources (websites, PDFs, brochures)

## 📋 Output Format

The knowledge graph contains `nodes` and `edges` arrays:

- **Nodes**: `Program`, `Section`, `Collection`, `Course`, `Level`
- **Edges**: `HAS_SECTION`, `HAS`, `REQUIRES` (prerequisites), `HAS_LEVEL`
- **Metadata**: Outline summary embedded in `meta.outlineSummary`

## 🔧 Troubleshooting

### Graphviz Issues
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

## 🎯 Generic Applicability

This parser can be applied to any academic institution or program, making it suitable for:
- **University/college websites** - Extract course structures and prerequisites
- **MOOC platforms** - Parse course catalogs and learning paths
- **Professional certification programs** - Extract certification requirements
- **Program brochures and policy handbooks** - Convert unstructured documents to structured data
- **Educational content management systems** - Integrate with existing platforms

---

## 🚀 Next Steps

This parser serves as the **foundational component** for the broader IITM BS Xplore project. The extracted knowledge graphs can be used to build:

- **Intelligent course recommendation systems**
- **Academic planning assistants** 
- **Prerequisite validation tools**
- **Curriculum analysis dashboards**
- **Multi-agent educational platforms**

This modular, production-ready parser provides the essential data extraction capabilities needed for comprehensive academic course planning and knowledge graph visualization! 🚀