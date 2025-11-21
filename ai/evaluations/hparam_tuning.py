"""Hyperparameter tuning for the RAG pipeline using the evaluation fixtures."""

from __future__ import annotations

import argparse
import copy
import itertools
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

CURRENT_DIR = Path(__file__).resolve().parent

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(CURRENT_DIR.parents[1]))
    from ai.evaluations.datasets import EVALUATION_DATA  # type: ignore
    from ai.evaluations.run_ragas import METRIC_NAMES, evaluate_agent  # type: ignore
else:  # pragma: no cover
    from .datasets import EVALUATION_DATA
    from .run_ragas import METRIC_NAMES, evaluate_agent

from ai.rag_config import (
    ChunkingConfig,
    EvaluationConfig,
    RagConfig,
    RetrievalConfig,
    load_rag_config,
    save_rag_config,
    summarize_config,
)


RESULTS_MD = CURRENT_DIR / "results" / "hparam_tuning.md"

# Search space (kept intentionally small for quick iterations)
CHUNK_SIZES = (700, 1000)
CHUNK_OVERLAPS = (120, 200)
TOP_K_VALUES = (4, 8)
SCORE_THRESHOLDS: Tuple[float | None, ...] = (None, 0.35)


def _build_trial_config(
    base: RagConfig, chunk_size: int, chunk_overlap: int, top_k: int, threshold: float | None
) -> RagConfig:
    retrieval = RetrievalConfig(
        top_k=top_k,
        score_threshold=threshold,
        rerank_top_k=base.retrieval.rerank_top_k,
        max_context_chars=base.retrieval.max_context_chars,
    )
    chunking = ChunkingConfig(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    evaluation = EvaluationConfig(
        prefer_ragas=base.evaluation.prefer_ragas,
        ragas_model=base.evaluation.ragas_model,
        embedding_model=base.evaluation.embedding_model,
        use_live_contexts=True,
    )

    cfg = RagConfig(
        chunking=chunking,
        retrieval=retrieval,
        evaluation=evaluation,
        metadata=dict(base.metadata),
    )
    return cfg


def _score_results(agent_results: Iterable[Mapping[str, Any]]) -> float:
    values: List[float] = []
    for result in agent_results:
        agg = result.get("aggregated_metrics", {})  # type: ignore[arg-type]
        for name in METRIC_NAMES:
            if name in agg:
                values.append(float(agg[name]))
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _dominant_metrics_source(agent_results: Iterable[Mapping[str, Any]]) -> str:
    sources = [result.get("metrics_source", "unknown") for result in agent_results]
    if not sources:
        return "unknown"
    return max(set(sources), key=sources.count)


def _write_markdown_report(
    trials: List[Dict[str, Any]],
    best: Dict[str, Any],
    agent_keys: Iterable[str],
    base_config: RagConfig,
    use_recorded: bool,
    ragas_available: bool,
) -> Path:
    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    lines: List[str] = []
    lines.append("# RAG Hyperparameter Tuning Report")
    lines.append(f"- Generated: {timestamp}")
    lines.append(f"- Agents evaluated: {', '.join(agent_keys)}")
    lines.append(f"- Ragas available: {ragas_available}")
    lines.append(f"- Answers source: {'recorded references' if use_recorded else 'live agents (with fallback on failure)'}")
    lines.append(f"- Scoring rule: mean of {', '.join(METRIC_NAMES)} across agents (fallback metrics when ragas unavailable)")
    lines.append(f"- Context mode: {'live retrieval' if best['config'].evaluation.use_live_contexts else 'fixtures'}")
    lines.append(f"- Base config: {summarize_config(base_config)}")
    lines.append("")

    lines.append("## Trials")
    lines.append("|Trial|Chunk Size|Overlap|Top K|Score Threshold|Score|Metrics source|")
    lines.append("|---|---|---|---|---|---|---|")
    for idx, trial in enumerate(trials, start=1):
        cfg = summarize_config(trial["config"])
        threshold = cfg["score_threshold"] if cfg["score_threshold"] is not None else "-"
        lines.append(
            f"|{idx}|{cfg['chunk_size']}|{cfg['chunk_overlap']}|{cfg['top_k']}|{threshold}|{trial['score']:.4f}|{trial['metrics_source']}|"
        )

    lines.append("")
    lines.append("## Best configuration")
    best_cfg = summarize_config(best["config"])
    threshold = best_cfg["score_threshold"] if best_cfg["score_threshold"] is not None else "-"
    lines.append(f"- Score: {best['score']:.4f}")
    lines.append(f"- Chunk size / overlap: {best_cfg['chunk_size']} / {best_cfg['chunk_overlap']}")
    lines.append(f"- Top K: {best_cfg['top_k']}; score_threshold: {threshold}")
    lines.append(f"- Metrics source: {best['metrics_source']}")
    lines.append(f"- Config summary: {best_cfg}")
    lines.append("")
    lines.append("### Per-agent metrics (best trial)")
    for result in best["results"]:
        label = f"{result['agent_label']} ({result['agent_key']})"
        metrics = ", ".join(f"{k}={v}" for k, v in result.get("aggregated_metrics", {}).items())
        lines.append(f"- {label}: {metrics}")

    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")
    return RESULTS_MD


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hyperparameter sweeps on live/recorded agents.")
    parser.add_argument(
        "--agent",
        dest="agent_keys",
        action="append",
        help="Limit evaluation to the given agent key (can be passed multiple times). Defaults to all.",
    )
    parser.add_argument(
        "--recorded",
        dest="use_recorded",
        action="store_true",
        help="Use recorded reference answers instead of invoking live agents.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    base_config = load_rag_config()
    if str(base_config.__class__.__module__).startswith("ai."):
        # Ensure project root is importable for agent loads
        root = CURRENT_DIR.parents[1]
        sys.path.append(str(root)) if str(root) not in sys.path else None
    agent_keys = tuple(args.agent_keys) if args.agent_keys else tuple(EVALUATION_DATA.keys())
    use_recorded = bool(args.use_recorded)

    trials: List[Dict[str, Any]] = []
    for chunk_size, chunk_overlap, top_k, threshold in itertools.product(
        CHUNK_SIZES, CHUNK_OVERLAPS, TOP_K_VALUES, SCORE_THRESHOLDS
    ):
        trial_config = _build_trial_config(base_config, chunk_size, chunk_overlap, top_k, threshold)
        trial_results = []

        for agent_key in agent_keys:
            trial_results.append(
                evaluate_agent(
                    agent_key,
                    use_recorded=use_recorded,
                    prefer_ragas=trial_config.evaluation.prefer_ragas,
                    use_live_contexts=trial_config.evaluation.use_live_contexts,
                    rag_config=trial_config,
                    retrieval_config=trial_config.retrieval,
                    chunking_config=trial_config.chunking,
                )
            )

        trials.append(
            {
                "config": trial_config,
                "results": trial_results,
                "score": _score_results(trial_results),
                "metrics_source": _dominant_metrics_source(trial_results),
            }
        )

    if not trials:
        raise RuntimeError("No trials executed during hyperparameter tuning.")

    ragas_available = any(
        result.get("ragas_runtime", {}).get("enabled") for trial in trials for result in trial.get("results", [])
    )
    best = max(trials, key=lambda trial: trial["score"])
    best_config = copy.deepcopy(best["config"])
    best_config.metadata.update(
        {
            "selected_by": "ai/evaluations/hparam_tuning.py",
            "selected_at": datetime.now(timezone.utc).isoformat(),
            "best_score": best["score"],
        }
    )

    save_path = save_rag_config(best_config)
    report_path = _write_markdown_report(
        trials, best, agent_keys, base_config, use_recorded, bool(ragas_available)
    )

    print(f"Saved best configuration to {save_path}")
    print(f"Wrote tuning report to {report_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
