"""Shared configuration helpers for RAG chunking, retrieval, and evaluation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


CONFIG_PATH = Path(__file__).resolve().parents[1] / "rag_config.json"


@dataclass
class ChunkingConfig:
    """Chunking knobs used during ingestion and evaluation."""

    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class RetrievalConfig:
    """Vector search parameters shared by agents and evaluation."""

    top_k: int = 5
    score_threshold: Optional[float] = None  # Maximum allowed distance in Chroma
    rerank_top_k: Optional[int] = None  # Optional post-filter top-k after thresholding
    max_context_chars: int = 1800  # Trim oversized contexts before scoring


@dataclass
class EvaluationConfig:
    """Ragas + evaluation pipeline controls."""

    prefer_ragas: bool = True
    ragas_model: str = "gemini-1.5-flash"
    embedding_model: str = "text-embedding-004"
    use_live_contexts: bool = False  # When true, pull contexts from the retriever instead of fixtures


@dataclass
class RagConfig:
    """Top-level config container."""

    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


def _load_chunking(user_dict: Dict[str, Any]) -> ChunkingConfig:
    return ChunkingConfig(
        chunk_size=int(user_dict.get("chunk_size", ChunkingConfig.chunk_size)),
        chunk_overlap=int(user_dict.get("chunk_overlap", ChunkingConfig.chunk_overlap)),
    )


def _load_retrieval(user_dict: Dict[str, Any]) -> RetrievalConfig:
    score_threshold = user_dict.get("score_threshold", RetrievalConfig.score_threshold)
    if score_threshold is not None:
        try:
            score_threshold = float(score_threshold)
        except (TypeError, ValueError):
            score_threshold = RetrievalConfig.score_threshold

    rerank_top_k = user_dict.get("rerank_top_k", RetrievalConfig.rerank_top_k)
    if rerank_top_k is not None:
        try:
            rerank_top_k = int(rerank_top_k)
        except (TypeError, ValueError):
            rerank_top_k = RetrievalConfig.rerank_top_k

    return RetrievalConfig(
        top_k=int(user_dict.get("top_k", RetrievalConfig.top_k)),
        score_threshold=score_threshold,
        rerank_top_k=rerank_top_k,
        max_context_chars=int(user_dict.get("max_context_chars", RetrievalConfig.max_context_chars)),
    )


def _load_evaluation(user_dict: Dict[str, Any]) -> EvaluationConfig:
    prefer_ragas = bool(user_dict.get("prefer_ragas", EvaluationConfig.prefer_ragas))
    use_live_contexts = bool(user_dict.get("use_live_contexts", EvaluationConfig.use_live_contexts))

    return EvaluationConfig(
        prefer_ragas=prefer_ragas,
        ragas_model=str(user_dict.get("ragas_model", EvaluationConfig.ragas_model)),
        embedding_model=str(user_dict.get("embedding_model", EvaluationConfig.embedding_model)),
        use_live_contexts=use_live_contexts,
    )


def load_rag_config(path: Path | str | None = None) -> RagConfig:
    """Load config from disk, falling back to defaults when missing."""

    cfg_path = Path(path) if path else CONFIG_PATH
    if not cfg_path.exists():
        return RagConfig()

    with cfg_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    chunking = _load_chunking(data.get("chunking", {}))
    retrieval = _load_retrieval(data.get("retrieval", {}))
    evaluation = _load_evaluation(data.get("evaluation", {}))
    metadata = data.get("metadata", {})

    return RagConfig(chunking=chunking, retrieval=retrieval, evaluation=evaluation, metadata=metadata)


def save_rag_config(config: RagConfig, path: Path | str | None = None) -> Path:
    """Persist the config to disk."""

    cfg_path = Path(path) if path else CONFIG_PATH
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg_path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2, ensure_ascii=True)
    return cfg_path


def update_rag_config(updates: Dict[str, Any], path: Path | str | None = None) -> RagConfig:
    """Convenience helper to apply partial updates and write them back."""

    current = load_rag_config(path)
    chunking_updates = updates.get("chunking", {})
    retrieval_updates = updates.get("retrieval", {})
    evaluation_updates = updates.get("evaluation", {})

    chunking = ChunkingConfig(
        chunk_size=int(chunking_updates.get("chunk_size", current.chunking.chunk_size)),
        chunk_overlap=int(chunking_updates.get("chunk_overlap", current.chunking.chunk_overlap)),
    )

    score_threshold = retrieval_updates.get("score_threshold", current.retrieval.score_threshold)
    if score_threshold is not None:
        try:
            score_threshold = float(score_threshold)
        except (TypeError, ValueError):
            score_threshold = current.retrieval.score_threshold

    rerank_top_k = retrieval_updates.get("rerank_top_k", current.retrieval.rerank_top_k)
    if rerank_top_k is not None:
        try:
            rerank_top_k = int(rerank_top_k)
        except (TypeError, ValueError):
            rerank_top_k = current.retrieval.rerank_top_k

    retrieval = RetrievalConfig(
        top_k=int(retrieval_updates.get("top_k", current.retrieval.top_k)),
        score_threshold=score_threshold,
        rerank_top_k=rerank_top_k,
        max_context_chars=int(
            retrieval_updates.get("max_context_chars", current.retrieval.max_context_chars)
        ),
    )

    evaluation = EvaluationConfig(
        prefer_ragas=bool(evaluation_updates.get("prefer_ragas", current.evaluation.prefer_ragas)),
        ragas_model=str(evaluation_updates.get("ragas_model", current.evaluation.ragas_model)),
        embedding_model=str(
            evaluation_updates.get("embedding_model", current.evaluation.embedding_model)
        ),
        use_live_contexts=bool(
            evaluation_updates.get("use_live_contexts", current.evaluation.use_live_contexts)
        ),
    )

    merged = RagConfig(chunking=chunking, retrieval=retrieval, evaluation=evaluation, metadata=current.metadata)
    save_rag_config(merged, path)
    return merged


def summarize_config(config: RagConfig) -> Dict[str, Any]:
    """Return a flattened summary for logging."""

    return {
        "chunk_size": config.chunking.chunk_size,
        "chunk_overlap": config.chunking.chunk_overlap,
        "top_k": config.retrieval.top_k,
        "score_threshold": config.retrieval.score_threshold,
        "rerank_top_k": config.retrieval.rerank_top_k,
        "max_context_chars": config.retrieval.max_context_chars,
        "prefer_ragas": config.evaluation.prefer_ragas,
        "ragas_model": config.evaluation.ragas_model,
        "embedding_model": config.evaluation.embedding_model,
        "use_live_contexts": config.evaluation.use_live_contexts,
    }

