import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Google GenAI configuration
GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY", "")
GENAI_MODEL_ID = os.getenv("GENAI_MODEL_ID", "gemini-2.5-flash")


def _fix_neon_connection_string(conn_str: str) -> str:
    """
    Fixes Neon connection string by adding endpoint ID parameter if needed.
    According to Neon docs: https://neon.com/docs/guides/python
    """
    if not conn_str or ".neon.tech" not in conn_str:
        return conn_str

    # Parse the connection string
    parsed = urlparse(conn_str)

    # Extract endpoint ID from hostname (first part before .neon.tech)
    hostname = parsed.hostname or ""
    if ".neon.tech" in hostname:
        endpoint_id = hostname.split(".")[0]

        # Parse existing query parameters
        query_params = parse_qs(parsed.query)

        # Ensure SSL parameters are present (required by Neon)
        if "sslmode" not in query_params:
            query_params["sslmode"] = ["require"]
        if "channel_binding" not in query_params:
            query_params["channel_binding"] = ["require"]

        # Add endpoint ID if not already present
        if "options" not in query_params:
            # Format: options=endpoint%3D<endpoint-id>
            query_params["options"] = [f"endpoint={endpoint_id}"]
        elif not any("endpoint=" in opt for opt in query_params["options"]):
            # Append endpoint to existing options
            query_params["options"][0] += f"&endpoint={endpoint_id}"

        # Reconstruct the connection string
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

    return conn_str


# Get connection string and fix it for Neon if needed
_raw_db_conn_str = os.getenv("DATABASE_URL") or os.getenv(
    "DB_URL", "postgresql://user:pass@localhost:5432/yourdb"
)
DB_CONNECTION_STR = _fix_neon_connection_string(_raw_db_conn_str)

# URLs
COURSE_LISTING_URL = "https://study.iitm.ac.in/ds/academics.html#AC1"
COURSE_PREFIX = "https://study.iitm.ac.in/ds/"
