"""Utility module for initializing GenAI file search stores for PDF documents."""

import time
from pathlib import Path
from typing import Optional, Dict
from google import genai
import psycopg
import sys

# Import config from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONNECTION_STR


def get_store_name_for_pdf(pdf_path: Path) -> Optional[str]:
    """
    Get the store name for a PDF file if it exists in the database.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        str: Store name if found, None otherwise.
    """
    # Use just the filename for lookup
    filename = pdf_path.name

    try:
        with psycopg.connect(DB_CONNECTION_STR) as conn:
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


def set_store_name_for_pdf(pdf_path: Path, store_name: str) -> None:
    """
    Save the store name for a PDF file in the database.

    Args:
        pdf_path: Path to the PDF file.
        store_name: Store name to associate with the PDF.
    """
    # Use just the filename for storage
    filename = pdf_path.name

    try:
        with psycopg.connect(DB_CONNECTION_STR) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO file_search_store_mappings (pdf_path, store_name, last_updated)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (pdf_path) 
                    DO UPDATE SET store_name = EXCLUDED.store_name, last_updated = CURRENT_TIMESTAMP
                    """,
                    (filename, store_name),
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving store name to database: {e}")
        raise


def initialize_file_search_store(
    pdf_path: Path, store_name: Optional[str] = None
) -> dict:
    """
    Initialize a file search store and upload a PDF document.
    Checks local mapping first to avoid re-uploading the same document.

    Args:
        pdf_path: Path to the PDF file.
        store_name: Optional name for the file search store. If None, creates a new one.

    Returns:
        dict: Contains 'store_name' and 'status' of the operation.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        Exception: If the upload operation fails.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Check if we already have a store_name for this PDF
    existing_store_name = get_store_name_for_pdf(pdf_path)
    if existing_store_name:
        return {
            "store_name": existing_store_name,
            "status": "existing",
            "pdf_path": str(pdf_path),
            "message": f"Using existing file search store: {existing_store_name}",
        }

    # Initialize client (SDK will automatically pick up GEMINI_API_KEY from env)
    client = genai.Client()

    # Create or get file search store
    if store_name:
        try:
            store = client.file_search_stores.get(store_name)
        except Exception:
            store = client.file_search_stores.create(name=store_name)
    else:
        store = client.file_search_stores.create()

    # Upload PDF to file search store
    upload_op = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=store.name, file=str(pdf_path.absolute())
    )

    # Wait for upload to complete
    max_wait_time = 300  # 5 minutes max
    wait_interval = 5  # Check every 5 seconds
    elapsed_time = 0

    while not upload_op.done:
        if elapsed_time >= max_wait_time:
            raise TimeoutError(
                f"Upload operation timed out after {max_wait_time} seconds"
            )

        time.sleep(wait_interval)
        elapsed_time += wait_interval
        upload_op = client.operations.get(upload_op)

    if upload_op.error:
        raise Exception(f"Upload failed: {upload_op.error}")

    # Save the mapping for future use
    set_store_name_for_pdf(pdf_path, store.name)

    return {
        "store_name": store.name,
        "status": "success",
        "pdf_path": str(pdf_path),
        "message": f"Successfully uploaded PDF to file search store: {store.name}",
    }


def initialize_all_pdfs():
    """
    Initialize file search stores for all required PDF documents.
    Currently initializes:
    - student_handbook.pdf
    - grading_doc.pdf

    Returns:
        dict: Summary of initialization results for each PDF.
    """
    data_dir = Path(__file__).parent.parent
    dump_dir = data_dir / "dump"

    pdfs = [dump_dir / "student_handbook.pdf", dump_dir / "grading_doc.pdf"]

    results = {}

    for pdf_path in pdfs:
        pdf_name = pdf_path.name
        print(f"Initializing file search store for {pdf_name}...")

        try:
            result = initialize_file_search_store(pdf_path)
            results[pdf_name] = result
            print(f"  ✓ {result['message']}")
        except FileNotFoundError:
            print(f"  ⚠ {pdf_name} not found, skipping...")
            results[pdf_name] = {
                "status": "not_found",
                "message": f"PDF file not found: {pdf_path}",
            }
        except Exception as e:
            print(f"  ✗ Error initializing {pdf_name}: {e}")
            results[pdf_name] = {"status": "error", "message": str(e)}

    return results
