"""Multi-agent orchestrator for IITM BS queries."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import math
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
TOOLS_PATH = os.path.join(PROJECT_ROOT, "tools")

if TOOLS_PATH not in sys.path:
    sys.path.insert(0, TOOLS_PATH)

chromadb_spec = importlib.util.spec_from_file_location(
    "chromadb_tools", os.path.join(TOOLS_PATH, "chromadb_tools.py")
)
if not chromadb_spec or not chromadb_spec.loader:
    raise ImportError("Unable to import chromadb_tools for orchestrator agent")

chromadb_tools = importlib.util.module_from_spec(chromadb_spec)
chromadb_spec.loader.exec_module(chromadb_tools)  # type: ignore[attr-defined]

get_embeddings = chromadb_tools.get_embeddings


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
    "- knowledge_graph for structured prerequisite / relationship / eligibility questions"
    if KG_AVAILABLE
    else (
        "- knowledge_graph agent is currently unavailable (Neo4j credentials missing). "
        "When a user explicitly requests KG data, explain the limitation instead of delegating."
    )
)


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


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def rerank_documents(
    query: str,
    candidate_documents: List[str],
    candidate_sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Rerank candidate snippets using Gemini embeddings and cosine similarity."""

    query = query.strip()
    if not query:
        raise ValueError("Query must be provided for reranking.")
    if not candidate_documents:
        raise ValueError("candidate_documents must include at least one entry.")

    query_embedding = get_embeddings(query)
    ranked: List[Dict[str, Any]] = []

    for idx, doc in enumerate(candidate_documents):
        doc_text = (doc or "").strip()
        if not doc_text:
            continue
        embedding = get_embeddings(doc_text)
        similarity = _cosine_similarity(query_embedding, embedding)
        ranked.append(
            {
                "rank": idx + 1,
                "similarity": similarity,
                "text": doc_text,
                "source": candidate_sources[idx]
                if candidate_sources and idx < len(candidate_sources)
                else None,
            }
        )

    ranked.sort(key=lambda item: item["similarity"], reverse=True)
    for new_rank, item in enumerate(ranked, start=1):
        item["rank"] = new_rank

    return {
        "query": query,
        "ranked_documents": ranked,
        "top_document": ranked[0] if ranked else None,
    }


GEMINI_MODEL = "gemini-2.5-flash-lite"

SYSTEM_INSTRUCTION = f"""
You are the IITM BS Programme Orchestrator Agent.

Available sub-agents: {AVAILABLE_AGENT_LIST}

Responsibilities:
1. Interpret the user's full query and break it into sub-goals that map to the available specialist agents:
   - ds_foundation / ds_diploma / ds_degree for Data Science level-specific guidance
   - es_foundation / es_diploma / es_degree for Electronic Systems programme details
   {KG_AGENT_INSTRUCTION}
2. Call delegate_to_agent with concise, level-aware prompts. Include the user's wording and any clarifications you derive so the delegated agent receives full context.
3. When questions span multiple programmes or levels, consult every relevant agent so that coverage is complete. For structural or cross-linking needs, combine KG outputs with DS/ES narrative agents.
4. Extract the most salient passages from each delegated response and send them—along with their identifiers—to rerank_documents. Always rerank before finalizing your answer so the most relevant snippets drive the summary.
5. Use the reranking output to ground your final answer. Cite which agent supplied the supporting evidence (e.g., “DS Degree agent” or “knowledge_graph”).
6. If information is missing or conflicting, ask for clarification instead of guessing.

Workflow:
- Plan → delegate to one or more agents → rerank the collected snippets → synthesize a consolidated answer grounded in the highest-ranked evidence.
- Prefer structured bullet summaries that highlight level/program distinctions, prerequisites, and action items for the learner.
"""

root_agent = Agent(
    model=GEMINI_MODEL,
    name="IITM_BS_Orchestrator",
    description="Routes IITM BS queries to DS/ES/KG sub-agents, reranks evidence, and synthesizes final replies.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[delegate_to_agent, rerank_documents],
)
