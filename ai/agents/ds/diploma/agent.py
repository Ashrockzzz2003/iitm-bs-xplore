from google.adk.agents.llm_agent import Agent
import sys
import os
import importlib.util

# Add the tools directory to the path
tools_path = os.path.join(os.path.dirname(__file__), "..", "..", "tools")
sys.path.insert(0, tools_path)

# Load the chromadb module directly
spec = importlib.util.spec_from_file_location(
    "chromadb_tools", os.path.join(tools_path, "chromadb_tools.py")
)
chromadb_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chromadb_tools)
query_chroma = chromadb_tools.query_chroma

GEMINI_MODEL = "gemini-2.5-flash"
CHROMA_COLLECTION = "ds_diploma"

SYSTEM_INSTRUCTION = f"""
You are a helpful assistant for user questions about the diploma level of IITM BS Degree Program.
For context about the diploma level of IITM BS Degree Program, use the tools provided to you.
The diploma level is split into two parts: Diploma in Programming and Diploma in Data Science.
You can use the tools to get information about the parts. Both the parts are combined in the {CHROMA_COLLECTION} collection.

The tools you have are:
- query_chroma({CHROMA_COLLECTION}, <query>): This tool allows you to query the chroma database for information about the diploma level of IITM BS Degree Program.
- The {CHROMA_COLLECTION} collection is the only collection you can use to answer the user's question.
- Don't directly use the tool with the user's query, instead extract keywords from the user's query and use the tool with one/many combinations of keywords to get the most relevant information and to ensure you get all the information you need to answer the user's question. 
- Usually just one combination of keywords is enough to get the most relevant information.

After you have gathered enough information, answer the user's question based on the information you have gathered.
Summarize the information you have gathered in a concise and clear manner.
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_BS__DataScience__DiplomaLevelAgent",
    description="A helpful assistant for user questions about the diploma level of IITM BS Degree Program.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[query_chroma],
)
