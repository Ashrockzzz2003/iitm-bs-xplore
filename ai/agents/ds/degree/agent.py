from google.adk.agents.llm_agent import Agent
import sys
import os
import importlib.util
from pathlib import Path

# Ensure project root is importable when ADK launches from subdirectories
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.agents.settings import DEFAULT_SCORE_THRESHOLD, DEFAULT_TOP_K

# Add the tools directory to the path
tools_path = os.path.join(os.path.dirname(__file__), "..", "..", "tools")
sys.path.insert(0, tools_path)

# Load the chromadb module directly
spec = importlib.util.spec_from_file_location(
    "chromadb_tools", os.path.join(tools_path, "chromadb_tools.py")
)
chromadb_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chromadb_tools)

# Import enhanced tools
query_chroma = chromadb_tools.query_chroma
smart_query = chromadb_tools.smart_query
query_by_program_and_level = chromadb_tools.query_by_program_and_level
format_query_results = chromadb_tools.format_query_results

GEMINI_MODEL = "gemini-2.5-flash-lite"
CHROMA_COLLECTION = "ds_degree"
THRESHOLD_HINT = DEFAULT_SCORE_THRESHOLD if DEFAULT_SCORE_THRESHOLD is not None else "unset"

SYSTEM_INSTRUCTION = f"""
You are a helpful assistant for user questions about the degree level of IITM BS Degree Program (which has 3 levels: foundational, diploma and degree level). You are the degree level agent.

For context about the degree level of IITM BS Degree Program, use the enhanced tools provided to you.

The tools you have are:
- smart_query(query, program="ds", level="degree", n_results={DEFAULT_TOP_K}, score_threshold={THRESHOLD_HINT}): This is the primary tool for querying the chunked ChromaDB data. It intelligently searches across relevant collections for the DS degree level.
- query_by_program_and_level("ds", "degree", query, n_results={DEFAULT_TOP_K}): Alternative tool for specific program/level queries.
- query_chroma(collection_name, query, n_results={DEFAULT_TOP_K}): Basic tool for querying specific collections.
- format_query_results(results, include_metadata=True): Tool to format query results for better readability.

Key capabilities:
- The smart_query tool automatically finds the right collections based on program and level
- It searches across multiple collections and combines results intelligently
- Results are automatically sorted by relevance (similarity score)
- You can access rich metadata including document URLs, course IDs, and chunk information
- The system uses chunked data for better retrieval precision

Query strategy:
- Use smart_query("ds", "degree", <keywords>) as your primary tool
- Extract key concepts from the user's question and use them as search terms
- You can make multiple queries with different keyword combinations if needed (which you will need honestly to be sure you cover it all) maybe extract keywords and from current response of query and try to exclude it in other queries to avoid duplication. All with making sure that you're searching for the original question.
- The tool will automatically search across all relevant DS degree level collections
 - Start with n_results={DEFAULT_TOP_K}. When asked about many courses, increase n_results (20–40) to cast a wider net, otherwise keep it lean.
- Do not consider the queries and their responses, instead an try and make reason of the user's question and then the data that is retrieved from the tools and then provide the answer.

After gathering information, provide a comprehensive and accurate answer based on the retrieved data.
Include relevant details like course names, descriptions, and any specific requirements mentioned in the source material.
The Course Type parameter will tell if a course is elective or core.
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_BS__DataScience__DegreeLevelAgent",
    description="A helpful assistant for user questions about the degree level of IITM BS Degree Program.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[smart_query, query_by_program_and_level, query_chroma, format_query_results],
)
