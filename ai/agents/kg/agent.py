from google.adk.agents.llm_agent import Agent
import importlib.util, os, sys

# Load kg-tools
tools_path = os.path.join(os.path.dirname(__file__), "..", "tools")
sys.path.insert(0, tools_path)

spec = importlib.util.spec_from_file_location(
    "kg_tools", os.path.join(tools_path, "kg_tools.py")
)
kg_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kg_tools)

# Extract tools
fuzzy_search_courses = kg_tools.fuzzy_search_courses
fuzzy_search_levels = kg_tools.fuzzy_search_levels
run_cypher = kg_tools.run_cypher_query

GEMINI_MODEL = "gemini-2.5-flash-lite"

SYSTEM_INSTRUCTION = """
You are the IITM Knowledge Graph Agent.

Graph schema:
(:Level {name, credits_required})
(:Course {code, name, credits, details_link, meta_data})
Relationships:
  (Level)-[:HAS_COURSE {mandatory, path}]->(Course)
  (Course)-[:HAS_PREREQUISITE]->(Course)
  (Course)-[:HAS_COREQUISITE]->(Course)
  (Level)-[:PROGRESS_TO]->(Level)

You can use these tools:
- fuzzy_search_courses(course_name, limit=5): to resolve ambiguous course names into official codes.
- fuzzy_search_levels(level_name, limit=5): to resolve ambiguous level names into official codes.
- run_cypher_query(cypher): to execute Cypher queries on the IITM Neo4j Knowledge Graph.

Guidelines:
1. Always first use fuzzy_search_courses, to find the exact course code rather then what user has provided.
2. Always first use fuzzy_search_levels, to find the exact level name rather then what user has provided.
3. Then build an appropriate Cypher query (like prerequisites, corequisites, or level mappings) and run it using run_cypher_query.
4. Return a natural-language answer summarizing the result.
5. meta_data in Course can have type or tag related to course like Project, Option, Core Course, Mandatory Course, Elective Course
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_KnowledgeGraph_Agent",
    description="Agent that queries the IITM Online Degree Knowledge Graph via Neo4j.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[fuzzy_search_courses, fuzzy_search_levels, run_cypher],
)
