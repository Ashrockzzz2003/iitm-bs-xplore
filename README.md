# IITM BS Xplore

## Problem Statement
- Students face difficulty planning academic progression (which courses to take according to prerequisite requirements, academic goals, number of terms in which they wish to complete the program).  
- Information is spread across websites, student handbooks, grading documents, and other PDFs.  

✦ Similar challenges exist in most universities and online education platforms where course structures are complex and requirements vary.

---

## Target Users
- Students enrolled in the online program  
- Academic advisors/staff assisting students with course planning  
- Prospective learners exploring program requirements  

✦ Can extend to learners across MOOCs, degree programs, or professional certifications.

---

## Feasibility & Data Sources
- **IITM online degree website**: Academics page, Course pages, NPTEL website for electives  
- **Documents**: Grading document, Student handbook  
- **Control UI**: Allows staff to configure additional URLs/PDFs  

✦ Generic sources: University/college/MOOC websites, program brochures, policy handbooks.

---

## Existing Solutions & Limitations
- Dedicated sessions for course selection and orientation sessions for different courses  
- Scattered information across websites & documents  

✦ Existing university chatbots are often FAQ/rule-based and lack personalization or academic planning capability.

---

## Proposed Solution
A **scraper** to extract structured/unstructured data from websites & documents.

### Approach I: KG + RAG based pipeline
- **Knowledge Graph (KG)** will store rules: Course prerequisites, Credit requirements for any level, Course mapping to levels, Compulsory courses per level  
- **Retrieval Augmented Generation (RAG)** will store unstructured descriptive context about a course or topic.

### Approach II: Multi-Agent Orchestration
Each agent will have its own responsibility:
- **Data Agent** – Fetch info about a particular course or topic  
- **Validation Agent** – Check prerequisites for a course  
- **Recommendation Agent** – Suggest courses/paths  

### UI for Students
Natural language query interface, e.g.:
- *"I have completed 2 courses (X & Y) of the diploma level (DS) and plan to complete my diploma in the next 2 terms. Which courses should I take next term that continue from X & Y?"*  
- *"I have already completed the Deep Learning course and want to do some hands-on work. Which elective course would best help me with this?"*

### Control UI for Staff
- Manage/update data sources dynamically  
- Add new sources (websites, PDFs, brochures)  

✦ **Generic applicability**: The same pipeline can be applied to any academic institution or program.

---
