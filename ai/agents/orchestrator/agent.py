"""Multi-agent orchestrator for IITM BS queries."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))


def _load_agent_module(alias: str, *relative_parts: str):
    module_path = os.path.join(PROJECT_ROOT, *relative_parts, "agent.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Missing agent module for {alias}: {module_path}")

    spec = importlib.util.spec_from_file_location(f"{alias}_module", module_path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to construct import spec for {alias}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    agent = getattr(module, "root_agent", None)
    if agent is None:
        raise AttributeError(f"Agent module {alias} does not expose root_agent")

    return agent


def _register_sub_agent(
    key: str,
    alias: str,
    relative_parts: tuple[str, ...],
    summary: str,
    app_name: str = "agents",
    required: bool = True,
) -> None:
    """Populate SUB_AGENTS with defensive loading and helpful warnings."""

    try:
        agent = _load_agent_module(alias, *relative_parts)
        available = True
    except Exception as exc:
        if required:
            raise
        print(
            f"Warning: Skipping optional sub-agent '{alias}' because it "
            f"failed to load ({exc})."
        )
        agent = None
        available = False

    SUB_AGENTS[key] = {
        "agent": agent,
        "summary": summary,
        "app_name": app_name,
        "available": available,
    }


async def _invoke_sub_agent(agent_obj: Any, question: str, app_name: str = "agents") -> str:
    """Run a child agent via the in-memory runner and return its reply."""

    runner = InMemoryRunner(agent=agent_obj, app_name=app_name)
    user_id = "orchestrator-user"
    session_id = str(uuid.uuid4())

    session_service = runner.session_service
    if hasattr(session_service, "create_session_sync"):
        session_service.create_session_sync(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
            state={},
        )
    else:
        await session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
            state={},
        )

    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=question)],
    )

    latest_text: Optional[str] = None
    final_text: Optional[str] = None

    try:
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if getattr(event, "author", None) == "user":
                continue
            content = getattr(event, "content", None)
            if not content or not getattr(content, "parts", None):
                continue

            text_parts: List[str] = []
            for part in content.parts:
                if getattr(part, "thought", False):
                    continue
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                    continue
                if getattr(part, "function_response", None):
                    response = part.function_response.response
                    try:
                        text_parts.append(json.dumps(response))
                    except TypeError:
                        text_parts.append(str(response))
                    continue
                if getattr(part, "function_call", None):
                    fc = part.function_call
                    payload = {"function_call": {"name": fc.name, "args": fc.args}}
                    text_parts.append(json.dumps(payload))
                    continue

            if not text_parts:
                continue

            candidate_text = "".join(text_parts).strip()
            if candidate_text:
                latest_text = candidate_text
                if event.is_final_response():
                    final_text = candidate_text
                    break
    finally:
        await runner.close()

    if final_text:
        return final_text
    if latest_text:
        return latest_text
    return "No textual response from delegated agent."


SUB_AGENTS: Dict[str, Dict[str, Any]] = {}

_register_sub_agent(
    "ds_foundation",
    "ds_foundation",
    ("ds", "foundation"),
    "Data Science foundation level agent for programme overview, credits, and prerequisites.",
)
_register_sub_agent(
    "ds_diploma",
    "ds_diploma",
    ("ds", "diploma"),
    "Data Science diploma agent (Programming + Data Science diplomas).",
)
_register_sub_agent(
    "ds_degree",
    "ds_degree",
    ("ds", "degree"),
    "Data Science degree agent for advanced BS curriculum and electives.",
)
_register_sub_agent(
    "es_foundation",
    "es_foundation",
    ("es", "foundation"),
    "Electronic Systems foundation agent covering labs, credits, and basic electronics.",
)
_register_sub_agent(
    "es_diploma",
    "es_diploma",
    ("es", "diploma"),
    "Electronic Systems diploma agent for programming/electronics diploma mix.",
)
_register_sub_agent(
    "es_degree",
    "es_degree",
    ("es", "degree"),
    "Electronic Systems degree agent with hardware-heavy curriculum details.",
)

_register_sub_agent(
    "policy_docs",
    "generic_policies",
    ("generic", "policies"),
    "Policy & handbook agent covering IITM BS rules, grading norms, and student lifecycle guidance.",
)

_register_sub_agent(
    "knowledge_graph",
    "kg",
    ("kg",),
    "Neo4j knowledge graph agent for structured prerequisite/path queries.",
    required=bool(os.getenv("NEO4J_URI")),
)

AVAILABLE_AGENT_KEYS = tuple(sorted(SUB_AGENTS.keys()))
KG_AVAILABLE = SUB_AGENTS.get("knowledge_graph", {}).get("available", False)
AVAILABLE_AGENT_LIST = ", ".join(AVAILABLE_AGENT_KEYS) if AVAILABLE_AGENT_KEYS else "None"
KG_AGENT_INSTRUCTION = (
    "- knowledge_graph for prerequisites, level progression, and other relationship questions"
    if KG_AVAILABLE
    else (
        "- knowledge_graph agent is currently unavailable (Neo4j credentials missing). "
        "When a user explicitly requests KG data, explain the limitation instead of delegating."
    )
)

PROGRAM_HINTS = {
    "ds": [
        "data science",
        "ml",
        "machine learning",
        "statistics",
        "ds ",
        " ds",
    ],
    "es": [
        "electronic systems",
        "electronics",
        "circuits",
        "hardware",
        "embedded",
        "signals",
        "vlsi",
        "es ",
        " es",
    ],
}

LEVEL_HINTS = {
    "foundation": ["foundation", "foundational"],
    "diploma": ["diploma"],
    "degree": ["degree", "bs degree", "bsc degree"],
}

RELATIONSHIP_TERMS = [
    "prereq",
    "prerequisite",
    "corequisite",
    "requirement",
    "dependency",
    "path",
    "progression",
    "eligibility",
    "depends on",
]

POLICY_TERMS = [
    "policy",
    "grading",
    "grade",
    "cgpa",
    "gpa",
    "credits",
    "attendance",
    "exam",
    "assessment",
    "fee",
    "refund",
    "registration",
    "deadline",
    "honor code",
]

LEVEL_PRIORITY = ["foundation", "diploma", "degree"]


async def delegate_to_agent(
    agent_key: str,
    question: str,
    extra_context: Optional[str] = None,
) -> Dict[str, str]:
    """Send a rewritten task to a specialised agent.

    Args:
        agent_key: One of "ds_foundation", "ds_diploma", "ds_degree",
            "es_foundation", "es_diploma", "es_degree", or "knowledge_graph".
        question: Targeted question for the delegated agent.
        extra_context: Optional clarifying notes or constraints to include.

    Returns:
        A dictionary with the agent key, prompt that was sent, and the response.
    """

    entry = SUB_AGENTS.get(agent_key)
    if not entry:
        raise ValueError(f"Unsupported agent_key '{agent_key}'.")

    question = question.strip()
    if not question:
        raise ValueError("Question must be non-empty.")

    effective_prompt = question
    if extra_context:
        effective_prompt = f"{question}\n\nAdditional context: {extra_context.strip()}"

    agent_obj = entry.get("agent")
    if agent_obj is None:
        raise RuntimeError(
            f"Agent '{agent_key}' is currently unavailable. Ensure its dependencies are configured."
        )

    response = await _invoke_sub_agent(agent_obj, effective_prompt, entry.get("app_name", "agents"))

    return {
        "agent_key": agent_key,
        "prompt": effective_prompt,
        "response": response,
        "agent_summary": entry.get("summary", ""),
    }


async def delegate_to_agents(
    agent_keys: List[str],
    question: str,
    extra_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Fan out a query to multiple specialised agents concurrently."""

    if not agent_keys:
        raise ValueError("Provide at least one agent key to delegate to.")

    # Deduplicate while preserving order
    seen = set()
    ordered_keys: List[str] = []
    for key in agent_keys:
        if key in seen:
            continue
        if key not in SUB_AGENTS:
            raise ValueError(f"Unsupported agent_key '{key}'.")
        seen.add(key)
        ordered_keys.append(key)

    tasks = [
        delegate_to_agent(key, question, extra_context) for key in ordered_keys
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    bundled: List[Dict[str, Any]] = []
    for key, result in zip(ordered_keys, responses):
        if isinstance(result, Exception):
            bundled.append(
                {
                    "agent_key": key,
                    "error": str(result),
                    "agent_summary": SUB_AGENTS[key].get("summary", ""),
                }
            )
            continue
        bundled.append(result)  # type: ignore[arg-type]

    return {"question": question, "results": bundled}


def route_question(question: str) -> Dict[str, Any]:
    """Suggest relevant agent keys for a user query using lightweight heuristics."""

    text = (question or "").strip().lower()
    if not text:
        raise ValueError("Question must be non-empty.")

    programs: List[str] = []
    for key, hints in PROGRAM_HINTS.items():
        if any(hint in text for hint in hints):
            programs.append(key)
    if not programs:
        programs = ["ds", "es"]

    level_hits: List[str] = []
    for level, hints in LEVEL_HINTS.items():
        if any(hint in text for hint in hints):
            level_hits.append(level)
    if not level_hits:
        level_hits = ["degree"]

    # Preserve the canonical level order and de-duplicate
    ordered_levels: List[str] = []
    seen_levels = set()
    for level in LEVEL_PRIORITY:
        if level in level_hits and level not in seen_levels:
            ordered_levels.append(level)
            seen_levels.add(level)

    agent_keys: List[str] = []
    rationale: List[str] = []

    for program in programs:
        for level in ordered_levels:
            key = f"{program}_{level}"
            if key in SUB_AGENTS:
                agent_keys.append(key)
    if not agent_keys:
        rationale.append("No programme/level detected; defaulting to degree agents.")
        if "ds_degree" in SUB_AGENTS:
            agent_keys.append("ds_degree")
        if "es_degree" in SUB_AGENTS:
            agent_keys.append("es_degree")

    relationship_needed = any(term in text for term in RELATIONSHIP_TERMS)
    if relationship_needed and KG_AVAILABLE:
        agent_keys.append("knowledge_graph")
        rationale.append("Added knowledge_graph for prerequisite/progression context.")
    elif relationship_needed and not KG_AVAILABLE:
        rationale.append("KG unavailable; cannot auto-answer prerequisites/progression.")

    policy_needed = any(term in text for term in POLICY_TERMS)
    if policy_needed and "policy_docs" in SUB_AGENTS:
        agent_keys.append("policy_docs")
        rationale.append("Added policy_docs for policy/handbook guidance.")

    # Remove duplicates while preserving order
    seen_keys = set()
    deduped_keys: List[str] = []
    for key in agent_keys:
        if key not in seen_keys:
            deduped_keys.append(key)
            seen_keys.add(key)

    return {
        "agent_keys": deduped_keys,
        "programs": programs,
        "levels": ordered_levels,
        "relationship_needed": relationship_needed,
        "policy_needed": policy_needed,
        "rationale": rationale,
    }


async def delegate_with_routing(
    question: str, extra_context: Optional[str] = None
) -> Dict[str, Any]:
    """Automatically route a question to suggested agents and collect responses."""

    routing = route_question(question)
    keys = routing.get("agent_keys", [])
    if not keys:
        raise RuntimeError("Routing produced no agent keys.")

    results = await delegate_to_agents(keys, question, extra_context)
    results["routing"] = routing
    return results


GEMINI_MODEL = "gemini-2.5-flash-lite"

SYSTEM_INSTRUCTION = f"""
You are the IITM BS Programme Orchestrator Agent.

Available sub-agents: {AVAILABLE_AGENT_LIST}

Responsibilities:
1. Call route_question to identify the relevant sub-agents based on programme/level hints and whether policy or relationship information is needed:
   - Default to degree agents (ds_degree / es_degree) when no level is stated.
   - Include foundation/diploma agents only when the query mentions those levels explicitly or spans the full journey.
   - Add policy_docs for handbook, grading, eligibility, or process clarifications.
   {KG_AGENT_INSTRUCTION}
2. Delegate using delegate_with_routing (auto) or delegate_to_agents (manual) with the selected agent keys so each agent receives the full user wording plus any clarifications you add.
3. When ambiguity exists between DS and ES or the user asks multi-programme questions, include both relevant agents.
4. For relationship-heavy questions (prerequisites, dependencies, progression), always include the knowledge_graph agent and merge its structured output with narrative details from the level agents.
5. Synthesize a single, concise answer that cites which agent(s) informed each point. If an agent is unavailable, note it briefly and continue with other signals.
6. If needed information is missing or conflicting, ask for clarification instead of guessing.

Workflow:
- Use route_question → delegate_with_routing (preferred) or route_question → delegate_to_agents.
- Merge the returned responses into a unified answer grounded in those results.
- Prefer clear bullet points that highlight level/program distinctions, prerequisites, and next steps for the learner.
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_BS_Orchestrator",
    description="Routes IITM BS queries to DS/ES/KG sub-agents and synthesizes grounded answers.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[route_question, delegate_with_routing, delegate_to_agent, delegate_to_agents],
)
