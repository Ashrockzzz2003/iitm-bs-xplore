"""Shared settings for agents that pull from the central RAG config."""

from __future__ import annotations

from ai.rag_config import load_rag_config

RAG_SETTINGS = load_rag_config()
DEFAULT_TOP_K = RAG_SETTINGS.retrieval.top_k
DEFAULT_SCORE_THRESHOLD = RAG_SETTINGS.retrieval.score_threshold
