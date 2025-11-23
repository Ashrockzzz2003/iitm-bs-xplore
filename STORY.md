# The Evolution of IITM BS Xplore: A Story of Pivoting to Clarity

## v1.0: The RAG & Knowledge Graph Attempt (The "Dead End")

Our initial approach (visible in the [`v1.0.0` branch](https://github.com/Ashrockzzz2003/iitm-bs-xplore/tree/v1.0.0)) followed the standard industry trend for LLM applications: **Retrieval Augmented Generation (RAG)** on everything.

### The Architecture

-   **Scraper**: We scraped 127+ pages (Academics, Course Pages).
-   **Storage**: We chunked everything (7+ lakh characters) into **ChromaDB** vector stores.
-   **Logic**: We attempted to build a **Knowledge Graph (KG)** to map prerequisites and levels.
-   **Agents**: A complex multi-agent orchestration (Foundation Agent, Diploma Agent, etc.) using Google ADK.

### The Problem

Despite the sophistication, the results were mediocre.

-   **Confidence**: ~60% accuracy on course-specific queries.
-   **Hallucinations**: The model struggled to distinguish between similar courses in the vector space.
-   **Complexity**: Maintaining a KG and vector store for structured data (like credits, prerequisites) felt inefficient. "What is the credit count for X?" is a database query, not a semantic search guess.

## The Realization

We took a step back and looked at our data. The course pages on the IITM website are **structured HTML**. They always have a title, a credit count, a syllabus table, and an instructor list.

**Why were we treating structured data as unstructured text?**

This led to the pivotal question:

> _"Can we use AI to structure the individual course page content into a JSON object, make it a row in a traditional SQL database, and give the Agent a tool to query it?"_

## v2.0: The Hybrid Solution (The "99% Winner")

We completely dismantled the ChromaDB/KG pipeline and built a **Hybrid Architecture**.

### 1. Structured Data for Courses (SQL)

-   **Ingestion**: We use **Gemini 3 Pro** to parse raw HTML course pages into a strict JSON schema.
-   **Storage**: This data goes into a **PostgreSQL (Neon)** database.
-   **Retrieval**: The agent uses a `query_course_database` tool (SELECT queries) to get exact facts.
-   **Result**: **99% Accuracy** on course queries. Zero hallucinations on credits, prerequisites, or syllabus details.

### 2. Unstructured Data for Policies (GenAI File Search)

-   **Docs**: Student Handbooks and Grading Policies remain unstructured PDFs.
-   **Storage**: We use **Google GenAI File Search** (managed RAG) for these documents.
-   **Retrieval**: The agent uses `search_handbook_policy` and `search_grading_policy` tools.
-   **Result**: High-quality answers with citations/grounding for rules and regulations.

## Conclusion

By treating **structured data as data** and **unstructured data as text**, we achieved a system that is:

1.  **Faster**: SQL queries are millisecond-fast compared to vector search + reranking.
2.  **More Accurate**: Facts are retrieved, not hallucinated.
3.  **Simpler**: No complex vector DB management or KG maintenance.

This hybrid approach eliminates the noise of RAG for factual data while preserving the flexibility of LLMs for policy interpretation.
