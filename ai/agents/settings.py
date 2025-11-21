"""Shared settings for agents that pull from the central RAG config."""

import sys
from pathlib import Path

# Ensure project root is on sys.path when imported via ADK
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.rag_config import load_rag_config  # type: ignore

RAG_SETTINGS = load_rag_config()
DEFAULT_TOP_K = RAG_SETTINGS.retrieval.top_k
DEFAULT_SCORE_THRESHOLD = RAG_SETTINGS.retrieval.score_threshold
