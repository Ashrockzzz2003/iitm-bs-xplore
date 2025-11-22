"""Tool wrappers for ADK with proper type hints and docstrings.

This module provides wrapped versions of tools with explicit type annotations
and comprehensive docstrings that ADK uses to automatically generate schemas
for the LLM.
"""

from typing import Optional, TypedDict, List, Any, Tuple
from .file_search_query import query_pdf as _query_pdf
from .query_neon import (
    query_iitm_course_knowledge_db as _query_iitm_course_knowledge_db,
)


class PDFSource(TypedDict):
    """A source document reference from PDF query results."""

    title: str
    uri: Optional[str]


class PDFQueryResult(TypedDict):
    """Result from querying a PDF document using GenAI file search."""

    response: str
    sources: List[PDFSource]
    grounding_metadata: Any
    query: str
    model: str
    store_name: str


class DatabaseQueryResult(TypedDict):
    """Result from querying the IITM course knowledge database."""

    rows: List[dict]
    row_count: int
    columns: List[str]
    query: str


def search_handbook_policy(query: str, model: Optional[str] = None) -> PDFQueryResult:
    """Search the IITM BS student handbook for policy and rule information.

    This tool enables semantic search over the IITM BS student handbook PDF using
    Google's GenAI file search capabilities. Use this for queries about:
    - Eligibility criteria and admission requirements (Regular/JEE)
    - Fees, scholarships, and financial information
    - Document verification procedures
    - Program structure and exit options
    - Maximum duration (8 years) and CCC (Credit Clearing Capability)
    - Academic rules and regulations

    Args:
        query: The question or query to ask about the student handbook. This should be
            a natural language question about policies, rules, or procedures.
        model: Optional model name to use for generation. Defaults to
            'gemini-3-pro-preview' if not specified.

    Returns:
        PDFQueryResult: A dictionary containing:
            - response (str): The generated answer to the query
            - sources (List[PDFSource]): List of source documents that were
              referenced, each with 'title' and optional 'uri'
            - grounding_metadata (Any): Full grounding metadata from the API
            - query (str): The original query that was executed
            - model (str): The model that was used for generation
            - store_name (str): The store name that was used

    Raises:
        ValueError: If the student handbook has not been initialized in the
            file search store, or if the store name cannot be found.
        Exception: If the query operation fails or the API call encounters an error.

    Example:
        >>> result = search_handbook_policy(
        ...     "What are the eligibility criteria for the qualifier exam?"
        ... )
        >>> print(result["response"])
        >>> for source in result["sources"]:
        ...     print(f"Source: {source['title']}")
    """
    return _query_pdf(query=query, pdf_path="student_handbook", model=model)


def search_grading_policy(query: str, model: Optional[str] = None) -> PDFQueryResult:
    """Search the IITM BS grading policy document for assessment and grading information.

    This tool enables semantic search over the IITM BS grading policy PDF using
    Google's GenAI file search capabilities. Use this for queries about:
    - Grading scale (S, A, B, C, D, E, U grades)
    - GPA and CGPA calculation methods
    - Assignment weightage and assessment structure
    - "Best of X" rules for assignments/exams
    - Eligibility criteria for End-Term exams
    - Marks distribution and evaluation policies

    Args:
        query: The question or query to ask about the grading policy. This should be
            a natural language question about marks, grades, assessments, or evaluation.
        model: Optional model name to use for generation. Defaults to
            'gemini-3-pro-preview' if not specified.

    Returns:
        PDFQueryResult: A dictionary containing:
            - response (str): The generated answer to the query
            - sources (List[PDFSource]): List of source documents that were
              referenced, each with 'title' and optional 'uri'
            - grounding_metadata (Any): Full grounding metadata from the API
            - query (str): The original query that was executed
            - model (str): The model that was used for generation
            - store_name (str): The store name that was used

    Raises:
        ValueError: If the grading document has not been initialized in the
            file search store, or if the store name cannot be found.
        Exception: If the query operation fails or the API call encounters an error.

    Example:
        >>> result = search_grading_policy(
        ...     "What is the grading scale and how is GPA calculated?"
        ... )
        >>> print(result["response"])
        >>> for source in result["sources"]:
        ...     print(f"Source: {source['title']}")
    """
    return _query_pdf(query=query, pdf_path="grading_doc", model=model)


def query_course_database(
    query: str, params: Optional[Tuple[Any, ...]] = None
) -> DatabaseQueryResult:
    """Query the IITM course knowledge database for structured course information.

    This tool allows querying the Neon PostgreSQL database containing structured
    course information from IITM's course catalog. Only SELECT queries are
    permitted for safety reasons. Use this for queries about:
    - Course specifics: syllabus topics, instructor names, credit count, titles
    - Course lists: "List all Diploma courses", "Show courses with 4 credits"
    - Course details: descriptions, prerequisites, learning outcomes

    The database contains course information including:
    - Course codes, titles, descriptions
    - Credits, academic levels (Foundation Level, Diploma Level, BSc Degree Level, BS Degree Level)
    - Instructors (stored as JSONB)
    - Syllabus (week-by-week, stored as JSONB)
    - Learning outcomes, resources, assessment structure
    - Prerequisites and video links

    Args:
        query: SQL SELECT query to execute. Must start with 'SELECT' (case-insensitive).
            Common tables include:
            - 'courses': Main course information table
            - 'file_search_store_mappings': Maps PDFs to GenAI file search stores
            Use exact level names: "Foundation Level", "Diploma Level", "BSc Degree Level", "BS Degree Level"
            Use ILIKE for case-insensitive matching (e.g., `title ILIKE '%python%'`)
            Example: "SELECT course_code, title, credits FROM courses WHERE level = 'Foundation Level' LIMIT 10"
        params: Optional tuple of parameters for parameterized queries. This helps
            prevent SQL injection. Use %s placeholders in the query for parameters.
            Example: ("Foundation Level",) for query with "WHERE level = %s"

    Returns:
        DatabaseQueryResult: A dictionary containing:
            - rows (List[dict]): List of result rows, where each row is a dictionary
              with column names as keys and values as the corresponding data
            - row_count (int): Number of rows returned
            - columns (List[str]): List of column names in the result set
            - query (str): The SQL query that was executed

    Raises:
        ValueError: If the query is not a SELECT statement (for safety) or if
            the database connection fails.
        Exception: If the query execution fails, including SQL syntax errors or
            database connection issues.

    Example:
        >>> result = query_course_database(
        ...     "SELECT course_code, title, credits FROM courses WHERE level = %s LIMIT 10",
        ...     params=("Foundation Level",)
        ... )
        >>> print(f"Found {result['row_count']} courses")
        >>> for row in result['rows']:
        ...     print(f"{row['course_code']}: {row['title']} ({row['credits']} credits)")
    """
    return _query_iitm_course_knowledge_db(query=query, params=params)
