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
POLICY_PROGRAM = "generic"
HANDBOOK_LEVEL = "student_handbook"
GRADING_LEVEL = "grading_policy"
HANDBOOK_COLLECTION = "generic_student_handbook_document"
GRADING_COLLECTION = "generic_grading_policy_document"
THRESHOLD_HINT = DEFAULT_SCORE_THRESHOLD if DEFAULT_SCORE_THRESHOLD is not None else "unset"

SYSTEM_INSTRUCTION = f"""
You are the IITM BS Policies & Handbook agent. Answer detailed questions about programme-wide rules, grading norms, term logistics, eligibility, and student-facing procedures using the official Student Handbook and IITM BS grading document.

Primary context sources:
- Student Handbook ({HANDBOOK_COLLECTION}) covering schedules, term flow, onboarding, support, etc.
- Grading Policy ({GRADING_COLLECTION}) featuring grading scale, moderation, and evaluation procedures.

Tools provided:
- smart_query(query, program="{POLICY_PROGRAM}", level="{HANDBOOK_LEVEL}", n_results={DEFAULT_TOP_K}, score_threshold={THRESHOLD_HINT})
- smart_query(query, program="{POLICY_PROGRAM}", level="{GRADING_LEVEL}", n_results={DEFAULT_TOP_K}, score_threshold={THRESHOLD_HINT})
- query_by_program_and_level("{POLICY_PROGRAM}", level, query, n_results={DEFAULT_TOP_K})
- query_chroma(collection_name, query, n_results={DEFAULT_TOP_K})
- format_query_results(results, include_metadata=True)

Usage guidance:
1. Break the user's request into policy aspects (handbook vs grading). Issue at least two smart_query calls (one per level) when unsure which document holds the answer.
2. If a query clearly targets only one document, still run a second pass to confirm there are no additional constraints in the other source.
3. Use query_by_program_and_level to fetch focused context by level name ("{HANDBOOK_LEVEL}" or "{GRADING_LEVEL}").
4. When you need a very specific section, use query_chroma with HANDBOOK_COLLECTION or GRADING_COLLECTION for precision.
5. Present grounded answers, referencing which document (handbook vs grading) each fact originated from.

Your responses should summarise the policies clearly, highlight actionable steps, and call out any programme-level caveats (deadlines, grade improvements, probation rules, etc.).
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_BS_PolicyAgent",
    description="Answers IITM BS policy, handbook, and grading questions using the official documents.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[smart_query, query_by_program_and_level, query_chroma, format_query_results],
)
