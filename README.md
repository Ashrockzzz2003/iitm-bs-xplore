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
