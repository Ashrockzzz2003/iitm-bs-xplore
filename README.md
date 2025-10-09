# IITM BS Xplore

## **Project Objectives and Scope (Problem Definition)**

The core objective of the IITM BS Xplore project is to give students of IITM a tool that will help them choose what courses to take in the next semester, ask questions about the IITM courses in natural language and get **cited** summarised information.

### **1.1 Primary Objective: Personalized Academic Planning**

To provide a natural language interface that allows students to receive validated, optimal, and personalized course recommendations based on four key variables:

1. **Academic Status:** Courses already completed (X & Y).
2. **Prerequisite Compliance:** Strict adherence to all course and level prerequisites.
3. **Program Goal:** The specific degree/diploma the student is pursuing.
4. **Time Constraint:** The number of terms remaining in which the student wishes to complete their goal.

### **1.2 Secondary Objectives (Technical & Utility)**

-   Create a **Knowledge Graph (KG)** powered **Retrieval Augmented Generation (RAG)** system for rich, descriptive context retrieval of the [IITM DS Academics](https://study.iitm.ac.in/ds/academics.html#AC1) and other similar content, orchestrated via a Multi-Agent system.
-   Compare a pure multi-agent system approach vs a normal query vs pure KG RAG

    For KG-RAG:

-   Design and implement a robust **scraper** capable of extracting, cleaning, and structuring data from heterogeneous sources (websites, PDFs, static handbooks).
    For Pure-Agentic:
-   ADK (Google's Agent Development Kit)
-   Thinking if we can combine KG-RAG and Multi-agent - if at all if its beneficial - exploring this.

**End User Tools**

1. Develop a web UI and deploy it to access this app.
2. Develop an intuitive **Control UI** for staff to dynamically manage data sources and update program requirements without requiring developer intervention.

**Stretch Goal** - Create a solution whose architecture is generic and transferable to other complex academic programs.

---

## **Literature Review** Review of Existing Solutions and Baselines

The current landscape for academic advising can be categorized into three major types, each with significant limitations that justify the proposed solution.

### **Manual and Legacy Solutions**

| Solution Type                      | Description                                                      | Limitations                                                                                                                    |
| :--------------------------------- | :--------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **Dedicated Advising Sessions**    | In-person or virtual sessions with academic staff.               | Not scalable; high staff overhead; scheduling conflicts; information consistency depends on the advisor.                       |
| **Scattered Documents & Websites** | Information spread across PDFs, handbooks, and various webpages. | Low accessibility; high cognitive load for students; prone to outdated information; no personalization or planning capability. |

## **Gaps and Opportunities**

The review highlights a critical gap between existing technology and the needs of complex, structured academic programs.

### **Identified Gaps**

1. **The Logic-Context Dichotomy:** No existing standard solution effectively combines the descriptive, nuanced information (best elective for hands-on work—**Context**) with the rigid, non-negotiable rules (prerequisite check—**Logic**) in a single query pipeline.
2. **Lack of Orchestrated Reasoning:** Current systems fail to break down a complex student query (e.g., "Plan my diploma in 2 terms starting from X & Y") into sequential sub-tasks (1. Fetch course details, 2. Validate prerequisites, 3. Recommend optimal path).

### **Opportunities for Proposed Solution**

The proposed **KG + RAG + Multi-Agent Orchestration** architecture is strategically designed to exploit these gaps:

| Component                                | Opportunity Addressed             | Function in Project                                                                                                                                                                      |
| :--------------------------------------- | :-------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Knowledge Graph (KG)**                 | _Overcomes the "Logic" gap._      | Provides a structured repository of rules, enabling fast, deterministic, and verifiable prerequisite checking and credit accumulation validation.                                        |
| **Retrieval Augmented Generation (RAG)** | _Overcomes the "Context" gap._    | Provides the LLM with up-to-date, relevant context (course descriptions, hands-on focus) to generate rich, personalized, and accurate recommendations.                                   |
| **Multi-Agent Orchestration**            | _Overcomes the "Reasoning" gap._  | Breaks down complex planning queries into delegated tasks (Data Agent → Validation Agent → Recommendation Agent), ensuring every output is logically sound and contextually appropriate. |
| **Control UI**                           | _Overcomes the "Dependency" gap._ | Empowers academic staff to update data sources and ensure the system's longevity and accuracy with minimal technical support.                                                            |
| **Generic Data Scraper**                 | _Scalability._                    | Allows the entire solution to be packaged as a service applicable to any university or MOOC with similar structural complexity.                                                          |

By architecting this hybrid solution, IITM BS Xplore will establish a new benchmark for academic planning tools, moving beyond simple Q&A to deliver personalized, rule-compliant, and goal-driven academic guidance.

---

## **Data Sources**

### **DS (Data Science)**

-   [Academics Page](https://study.iitm.ac.in/ds/academics.html#AC1)
    -   All course subpages linked in this page
    -   Pattern: [https://study.iitm.ac.in/ds/course_pages/{course_id}.html](https://study.iitm.ac.in/ds/course_pages/BSSE2001.html)
-   [Admissions Page](https://study.iitm.ac.in/ds/admissions.html#AD0)
-   Student Handbook - [Google Doc](https://docs.google.com/document/u/1/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub)
-   Grading Policy - [Google Doc](https://docs.google.com/document/u/1/d/e/2PACX-1vRKOWaLjxsts3qAM4h00EDvlB-GYRSPqqVXTfq3nGWFQBx91roxcU1qGv2ksS7jT4EQPNo8Rmr2zaE9/pub#h.cbcq4ial1xkk)

### **ES (Electronics Systems)**

-   [Academics Page](https://study.iitm.ac.in/es/academics.html#AC1)
    -   All course subpages linked in this page
    -   Pattern: [https://study.iitm.ac.in/es/course_pages/{course_id}.html](https://study.iitm.ac.in/es/course_pages/{course_id}.html)
-   [Admissions Page](https://study.iitm.ac.in/es/admissions.html#AD0)
-   [In The Media](https://study.iitm.ac.in/es/inthemedia.html)
-   [Archive](https://study.iitm.ac.in/es/archive.html)
-   [FAQ](https://study.iitm.ac.in/es/faq.html)

### **Additional Sources**

-   [Student Life](https://study.iitm.ac.in/ds/student_life.html)
-   [Paradox Showcase](https://paradox-showcase.web.app/)
-   [Student Achievements - Interns](https://study.iitm.ac.in/student-achievements/interns)
-   [Testimonials](https://study.iitm.ac.in/ds/testimonials.html)
-   [Student Achievements - Toppers](https://study.iitm.ac.in/student-achievements/toppers)
-   [Student Achievements - Projects](https://study.iitm.ac.in/student-achievements/projects)
-   [About IITM](https://study.iitm.ac.in/ds/aboutIITM.html)
-   [DS Archive](https://study.iitm.ac.in/ds/archive.html)

### **Future Sources**

-   [BS Insider](https://bsinsider.in/)
-   [Podgoodies](https://podgoodies.iitmadrasonline.in/)
-   Any Additional PDF docs can be added through Control UI by authorized personnel.

---

## **Proposed Solution Architecture**

### **Approach I: KG + RAG Pipeline**

-   **Knowledge Graph (KG)** will store rules: Course prerequisites, Credit requirements for any level, Course mapping to levels, Compulsory courses per level
-   **Retrieval Augmented Generation (RAG)** will store unstructured descriptive context about a course or topic.

### **Approach II: Multi-Agent Orchestration**

Each agent will have its own responsibility:

-   **Data Agent** – Fetch info about a particular course or topic
-   **Validation Agent** – Check prerequisites for a course
-   **Recommendation Agent** – Suggest courses/paths

### **UI for Students**

Natural language query interface, e.g.:

-   _"I have completed 2 courses (X & Y) of the diploma level (DS) and plan to complete my diploma in the next 2 terms. Which courses should I take next term that continue from X & Y?"_
-   _"I have already completed the Deep Learning course and want to do some hands-on work. Which elective course would best help me with this?"_

### **Control UI for Staff**

-   Manage/update data sources dynamically
-   Add new sources (websites, PDFs, brochures)

✦ **Generic applicability**: The same pipeline can be applied to any academic institution or program.

---

## **Repository Access**

-   [GitHub Repository](https://github.com/Ashrockzzz2003/iitm-bs-xplore)
-   [Invite Saranath](https://github.com/Ashrockzzz2003/iitm-bs-xplore/invitations)

---
