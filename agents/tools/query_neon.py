"""Tool for querying the IITM course knowledge database (Neon PostgreSQL)."""

import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import psycopg
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
            "to connect to the IITM course knowledge database."
        )
    return _fix_neon_connection_string(raw_conn_str)


def query_iitm_course_knowledge_db(
    query: str,
    params: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    Execute a SELECT query on the IITM course knowledge database (Neon PostgreSQL).
    
    This database contains course information including course codes, titles, descriptions,
    instructors, syllabus, and other course-related data from IITM's course catalog.
    
    Args:
        query: SQL SELECT query to execute. Only SELECT queries are allowed for safety.
              Common tables: 'courses', 'file_search_store_mappings'
        params: Optional tuple of parameters for parameterized queries (prevents SQL injection).
    
    Returns:
        dict: Contains 'rows' (list of dicts with column names as keys), 
              'row_count' (number of rows returned), 
              'columns' (list of column names),
              and 'query' (the executed query).
    
    Raises:
        ValueError: If query is not a SELECT statement or if connection fails.
        Exception: If the query execution fails.
    """
    # Basic safety check: only allow SELECT queries
    query_stripped = query.strip().upper()
    if not query_stripped.startswith("SELECT"):
        raise ValueError(
            "Only SELECT queries are allowed for safety. "
            "Modification queries (INSERT, UPDATE, DELETE, etc.) are not permitted."
        )
    
    try:
        db_conn_str = _get_db_connection_string()
        with psycopg.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                # Execute query with optional parameters
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                
                # Get column names
                columns = [desc[0] for desc in cur.description] if cur.description else []
                
                # Fetch all results
                rows = cur.fetchall()
                
                # Convert rows to list of dictionaries
                rows_dict = [
                    {col: val for col, val in zip(columns, row)}
                    for row in rows
                ]
                
                return {
                    "rows": rows_dict,
                    "row_count": len(rows_dict),
                    "columns": columns,
                    "query": query
                }
    except psycopg.Error as e:
        raise Exception(f"Database query failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to execute query: {str(e)}")

