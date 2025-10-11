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

## 🚀 Parser & Knowledge Graph

Parser component that extracts program sections, rules, and course information from HTML pages into structured knowledge graph JSON.

## 🏗️ Architecture

```
src/
├── processors/          # URL & file processing
├── visualizers/         # Graph visualization
├── utils/              # CLI & output handling
└── xplore/             # Core parsing modules
```

**Key Features**: Modular design, automatic parser detection, knowledge graph visualization

## 🚀 Quick Start

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Parse single URLs (auto-generates filename in outputs/kg/)
python app.py --url https://study.iitm.ac.in/ds/academics.html
python app.py --url https://study.iitm.ac.in/es/academics.html
python app.py --url https://study.iitm.ac.in/ds/course_pages/BSDA1001.html --output kg_course.json
python app.py --url https://study.iitm.ac.in/es/course_pages/BSEE1001.html --output kg_course.json

# Parse multiple data sources with unified hierarchy
python app.py --data-sources https://study.iitm.ac.in/ds/academics.html https://study.iitm.ac.in/es/academics.html --neo4j

# Parse local files
python app.py --academics test/data/academics.html --output kg_academics.json

# Generate outline
python app.py --url https://study.iitm.ac.in/ds/academics.html --outline-summary
```

## 🔧 How It Works

1. **Outline Detection**: Extracts headings (`h1`-`h6`) and builds hierarchical structure
2. **Knowledge Graph**: Creates `Section` nodes with `HAS_SECTION` relationships
3. **Level Detection**: Classifies content into levels (Foundation, Diploma, BSc, BS)
4. **Content Extraction**: Captures bullets, paragraphs, and labeled fields
5. **Course Parsing**: Groups courses into collections with prerequisite relationships

**Auto-detection**: IITM pages (both /ds/ and /es/) → specialized parsers, other URLs → generic parser

### Unified Program Hierarchy

When using `--data-sources`, the system creates a proper hierarchy:
- **IITM BS** (main program) → **DS** (Data Science sub-program) → courses, levels, sections
- **IITM BS** (main program) → **ES** (Electronics Systems sub-program) → courses, levels, sections

This allows querying across both programs while maintaining clear separation and relationships.

## 📊 Visualization

```bash
# Install Graphviz
brew install graphviz  # macOS
sudo apt-get install graphviz  # Ubuntu

# Generate all visualizations
python visualize_kg.py outputs/kg/production_full_courses.json

# Specific layouts
python visualize_kg.py outputs/kg/production_full_courses.json --layout hierarchical
python visualize_kg.py outputs/kg/production_full_courses.json --layout network --node-types Course
```

**Output**: PNG files in `outputs/viz/` showing program structure, course relationships, and network layouts

## 📋 Output Format

- **Nodes**: `Program`, `Section`, `Collection`, `Course`, `Level`
- **Edges**: `HAS_SECTION`, `HAS`, `REQUIRES` (prerequisites), `HAS_LEVEL`
- **Metadata**: Outline summary in `meta.outlineSummary`

## 🎯 Use Cases

- **Academic Planning**: Course recommendation and prerequisite validation
- **Data Extraction**: Convert unstructured course websites to structured data
- **Research**: Study course prerequisites and program structures
- **Integration**: Build educational platforms and planning tools

## 🚀 Next Steps

This parser enables building:
- Intelligent course recommendation systems
- Academic planning assistants
- Prerequisite validation tools
- Curriculum analysis dashboards
- Multi-agent educational platforms