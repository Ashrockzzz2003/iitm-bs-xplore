"""Tool for querying PDF documents using GenAI file search."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict
from google import genai
from google.genai import types
import psycopg
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()


def _get_db_connection_string() -> str:
    """
    Get and fix database connection string for Neon if needed.
    Returns the connection string from environment variables.
    """

    def _fix_neon_connection_string(conn_str: str) -> str:
        """Fixes Neon connection string by adding endpoint ID parameter if needed."""
        if not conn_str or ".neon.tech" not in conn_str:
            return conn_str

        parsed = urlparse(conn_str)
        hostname = parsed.hostname or ""
        if ".neon.tech" in hostname:
            endpoint_id = hostname.split(".")[0]
            query_params = parse_qs(parsed.query)

            if "sslmode" not in query_params:
                query_params["sslmode"] = ["require"]
            if "channel_binding" not in query_params:
                query_params["channel_binding"] = ["require"]

            if "options" not in query_params:
                query_params["options"] = [f"endpoint={endpoint_id}"]
            elif not any("endpoint=" in opt for opt in query_params["options"]):
                query_params["options"][0] += f"&endpoint={endpoint_id}"

            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            return urlunparse(new_parsed)

        return conn_str

    raw_conn_str = os.getenv("DATABASE_URL") or os.getenv("DB_URL", "")
    if not raw_conn_str:
        raise ValueError(
            "DATABASE_URL or DB_URL environment variable must be set "
            "to connect to the database for file search store mappings."
        )
    return _fix_neon_connection_string(raw_conn_str)


def get_store_name_for_pdf(pdf_path: Path) -> Optional[str]:
    """
    Get the store name for a PDF file from the database.

    Args:
        pdf_path: Path to the PDF file (can be absolute or relative).

    Returns:
        str: Store name if found, None otherwise.
    """
    # Use just the filename for lookup
    filename = pdf_path.name

    try:
        db_conn_str = _get_db_connection_string()
        with psycopg.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT store_name FROM file_search_store_mappings WHERE pdf_path = %s",
                    (filename,),
                )
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        # Log error but don't fail - return None to allow fallback behavior
        print(f"Error querying database for store name: {e}")
        return None


def query_pdf(
    query: str,
    store_name: Optional[str] = None,
    pdf_path: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict:
    """
    Query PDF documents using GenAI file search.
    Supports querying student_handbook.pdf and grading_doc.pdf.

    Args:
        query: The question or query to ask about the document.
        store_name: Name of the file search store. If None, will try to get from mapping.
        pdf_path: Path to the PDF file. Used to look up store_name from mapping if store_name is None.
                  Can be 'student_handbook' or 'grading_doc' for default PDFs.
        model: Model to use for generation. Defaults to gemini-3-pro-preview.

    Returns:
        dict: Contains 'response', 'sources', and 'grounding_metadata'.

    Raises:
        ValueError: If store_name is not provided and cannot be found in mapping.
        Exception: If the query operation fails.
    """
    # Get model
    if model is None:
        model = "gemini-3-pro-preview"

    # Initialize client (SDK will automatically pick up GEMINI_API_KEY from env)
    client = genai.Client()

    # Get or validate store
    if store_name is None:
        # Handle shorthand names for default PDFs
        if pdf_path in ["student_handbook", "grading_doc"]:
            project_root = Path(__file__).parent.parent.parent
            pdf_path = str(project_root / "data" / "dump" / f"{pdf_path}.pdf")

        # Try to get from PDF path mapping (database)
        if pdf_path:
            pdf_path_obj = Path(pdf_path)
            store_name = get_store_name_for_pdf(pdf_path_obj)

        # Try to get from environment
        if not store_name:
            store_name = os.getenv("GENAI_FILE_SEARCH_STORE_NAME")

        # Try default student handbook from database
        if not store_name:
            try:
                db_conn_str = _get_db_connection_string()
                with psycopg.connect(db_conn_str) as conn:
                    with conn.cursor() as cur:
                        # Query for student_handbook.pdf by filename
                        cur.execute(
                            "SELECT store_name FROM file_search_store_mappings WHERE pdf_path = %s",
                            ("student_handbook.pdf",),
                        )
                        result = cur.fetchone()
                        if result:
                            store_name = result[0]
            except Exception:
                pass  # Fall through to error

        if not store_name:
            raise ValueError(
                "store_name must be provided, or the PDF must be initialized first "
                "using data.util.file_search.initialize_file_search_store()."
            )

    # Generate content with file search
    try:
        response = client.models.generate_content(
            model=model,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ]
            ),
        )
    except Exception as e:
        raise Exception(f"Failed to generate content: {str(e)}")

    # Extract response text
    response_text = response.text if hasattr(response, "text") else ""

    # Extract grounding sources
    sources = []
    grounding_metadata = None

    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
            grounding_metadata = candidate.grounding_metadata
            if hasattr(grounding_metadata, "grounding_chunks"):
                sources = [
                    {
                        "title": (
                            chunk.retrieved_context.title
                            if hasattr(chunk.retrieved_context, "title")
                            else "Unknown"
                        ),
                        "uri": (
                            chunk.retrieved_context.uri
                            if hasattr(chunk.retrieved_context, "uri")
                            else None
                        ),
                    }
                    for chunk in grounding_metadata.grounding_chunks
                    if hasattr(chunk, "retrieved_context")
                ]
                # Deduplicate sources by title
                unique_sources = {s["title"]: s for s in sources}.values()
                sources = list(unique_sources)

    return {
        "response": response_text,
        "sources": sources,
        "grounding_metadata": grounding_metadata,
        "query": query,
        "model": model,
        "store_name": store_name,
    }
