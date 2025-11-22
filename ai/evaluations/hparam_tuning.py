"""Hyperparameter tuning for the RAG pipeline using the evaluation fixtures."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import itertools
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

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

# Expanded search space
CHUNK_SIZES = (500,900, 1300)
CHUNK_OVERLAPS = (60, 200)
TOP_K_VALUES = (3, 5, 8)
SCORE_THRESHOLDS: Tuple[float | None, ...] = (None,0.3, 0.5,0.7)
RERANK_TOP_K_VALUES: Tuple[int | None, ...] = (None, 3, 5)
MAX_CONTEXT_CHARS = (1200, 2400)


def _build_trial_config(
    base: RagConfig,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    threshold: float | None,
    rerank_top_k: int | None,
    max_context_chars: int,
) -> RagConfig:
    retrieval = RetrievalConfig(
        top_k=top_k,
        score_threshold=threshold,
        rerank_top_k=rerank_top_k,
        max_context_chars=max_context_chars,
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


def _evaluate_agent_with_timeout(
    timeout_seconds: Optional[float],
    agent_key: str,
    use_recorded: bool,
    prefer_ragas: bool,
    use_live_contexts: bool,
    rag_config: RagConfig,
    retrieval_config: RetrievalConfig,
    chunking_config: Any,
) -> Dict[str, Any]:
    """Evaluate an agent with an optional timeout."""
    if timeout_seconds is None or timeout_seconds <= 0:
        # No timeout, call directly
        return evaluate_agent(
            agent_key,
            use_recorded=use_recorded,
            prefer_ragas=prefer_ragas,
            use_live_contexts=use_live_contexts,
            rag_config=rag_config,
            retrieval_config=retrieval_config,
            chunking_config=chunking_config,
        )

    def _do_eval():
        return evaluate_agent(
            agent_key,
            use_recorded=use_recorded,
            prefer_ragas=prefer_ragas,
            use_live_contexts=use_live_contexts,
            rag_config=rag_config,
            retrieval_config=retrieval_config,
            chunking_config=chunking_config,
        )

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_eval)
            result = future.result(timeout=timeout_seconds)
            return result
    except concurrent.futures.TimeoutError:
        # Return a timeout result structure
        print(
            f"[warn] Evaluation timeout ({timeout_seconds}s) for agent {agent_key}",
            file=sys.stderr,
        )
        return {
            "agent_key": agent_key,
            "agent_label": agent_key,
            "cases_evaluated": 0,
            "metrics_source": "timeout",
            "ragas_runtime": {"enabled": False, "reason": f"timeout_{timeout_seconds}s"},
            "aggregated_metrics": {name: 0.0 for name in METRIC_NAMES},
            "cases": [],
            "timeout": True,
            "timeout_seconds": timeout_seconds,
        }
    except Exception as exc:
        print(
            f"[error] Evaluation failed for agent {agent_key}: {exc}",
            file=sys.stderr,
        )
        return {
            "agent_key": agent_key,
            "agent_label": agent_key,
            "cases_evaluated": 0,
            "metrics_source": "error",
            "ragas_runtime": {"enabled": False, "reason": f"error: {exc}"},
            "aggregated_metrics": {name: 0.0 for name in METRIC_NAMES},
            "cases": [],
            "error": str(exc),
        }


def _write_markdown_report(
    trials: List[Dict[str, Any]],
    best: Dict[str, Any],
    agent_keys: Iterable[str],
    base_config: RagConfig,
    use_recorded: bool,
    ragas_available: bool,
    max_workers: Optional[int] = None,
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
    if max_workers is not None:
        lines.append(f"- Parallel workers: {max_workers}")
    timeout_info = next(
        (r.get("timeout_seconds") for trial in trials for r in trial.get("results", []) if r.get("timeout")),
        None,
    )
    if timeout_info is not None:
        lines.append(f"- Timeout per step: {timeout_info}s")
    lines.append("")

    lines.append("## Trials")
    lines.append("|Trial|Chunk Size|Overlap|Top K|Score Threshold|Rerank Top K|Max Context Chars|Score|Metrics source|Status|")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for idx, trial in enumerate(trials, start=1):
        cfg = summarize_config(trial["config"])
        threshold = cfg["score_threshold"] if cfg["score_threshold"] is not None else "-"
        rerank_val = cfg["rerank_top_k"] if cfg["rerank_top_k"] is not None else "-"
        # Check if any result had a timeout or error
        status = "ok"
        for result in trial.get("results", []):
            if result.get("timeout"):
                status = "timeout"
                break
            if result.get("error"):
                status = "error"
                break
        lines.append(
            f"|{idx}|{cfg['chunk_size']}|{cfg['chunk_overlap']}|{cfg['top_k']}|{threshold}|{rerank_val}|{cfg['max_context_chars']}|{trial['score']:.4f}|{trial['metrics_source']}|{status}|"
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
        if result.get("timeout"):
            lines.append(f"- {label}: TIMEOUT (after {result.get('timeout_seconds', '?')}s)")
        elif result.get("error"):
            lines.append(f"- {label}: ERROR ({result.get('error', 'unknown')})")
        else:
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
    parser.add_argument(
        "--timeout",
        dest="timeout_seconds",
        type=float,
        default=None,
        help="Timeout in seconds for each evaluation step (agent evaluation). Default: no timeout.",
    )
    parser.add_argument(
        "--workers",
        dest="max_workers",
        type=int,
        default=None,
        help="Maximum number of parallel workers for trials and agent evaluations. Default: number of CPU cores.",
    )
    return parser.parse_args()


def _run_single_trial(
    trial_num: int,
    total_trials: int,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    threshold: float | None,
    rerank_top_k: int | None,
    max_ctx: int,
    base_config: RagConfig,
    agent_keys: Tuple[str, ...],
    use_recorded: bool,
    timeout_seconds: Optional[float],
    max_workers: Optional[int],
) -> Dict[str, Any]:
    """Run a single trial with parallel agent evaluations."""
    print(
        f"[info] Trial {trial_num}/{total_trials}: chunk_size={chunk_size}, overlap={chunk_overlap}, top_k={top_k}, threshold={threshold}, rerank_top_k={rerank_top_k}, max_ctx={max_ctx}",
        file=sys.stderr,
    )
    trial_config = _build_trial_config(
        base_config, chunk_size, chunk_overlap, top_k, threshold, rerank_top_k, max_ctx
    )

    # Parallelize agent evaluations within this trial
    def _evaluate_one_agent(agent_key: str) -> Dict[str, Any]:
        return _evaluate_agent_with_timeout(
            timeout_seconds=timeout_seconds,
            agent_key=agent_key,
            use_recorded=use_recorded,
            prefer_ragas=trial_config.evaluation.prefer_ragas,
            use_live_contexts=trial_config.evaluation.use_live_contexts,
            rag_config=trial_config,
            retrieval_config=trial_config.retrieval,
            chunking_config=trial_config.chunking,
        )

    trial_results: List[Dict[str, Any]] = []
    if max_workers is None or max_workers <= 1 or len(agent_keys) == 1:
        # Sequential execution
        for agent_key in agent_keys:
            trial_results.append(_evaluate_one_agent(agent_key))
    else:
        # Parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_agent = {
                executor.submit(_evaluate_one_agent, agent_key): agent_key
                for agent_key in agent_keys
            }
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_key = future_to_agent[future]
                try:
                    result = future.result()
                    trial_results.append(result)
                except Exception as exc:
                    print(
                        f"[error] Agent {agent_key} evaluation failed: {exc}",
                        file=sys.stderr,
                    )
                    trial_results.append({
                        "agent_key": agent_key,
                        "agent_label": agent_key,
                        "cases_evaluated": 0,
                        "metrics_source": "error",
                        "ragas_runtime": {"enabled": False, "reason": f"error: {exc}"},
                        "aggregated_metrics": {name: 0.0 for name in METRIC_NAMES},
                        "cases": [],
                        "error": str(exc),
                    })

    return {
        "config": trial_config,
        "results": trial_results,
        "score": _score_results(trial_results),
        "metrics_source": _dominant_metrics_source(trial_results),
    }


def main() -> None:
    args = _parse_args()
    base_config = load_rag_config()
    if str(base_config.__class__.__module__).startswith("ai."):
        # Ensure project root is importable for agent loads
        root = CURRENT_DIR.parents[1]
        sys.path.append(str(root)) if str(root) not in sys.path else None
    agent_keys = tuple(args.agent_keys) if args.agent_keys else tuple(EVALUATION_DATA.keys())
    use_recorded = bool(args.use_recorded)
    timeout_seconds: Optional[float] = args.timeout_seconds
    max_workers = args.max_workers
    if max_workers is None:
        max_workers = os.cpu_count() or 4
        print(f"[info] Using {max_workers} parallel workers (auto-detected)", file=sys.stderr)
    else:
        print(f"[info] Using {max_workers} parallel workers", file=sys.stderr)

    if timeout_seconds is not None:
        print(f"[info] Using timeout of {timeout_seconds}s per evaluation step", file=sys.stderr)

    total_trials = (
        len(CHUNK_SIZES)
        * len(CHUNK_OVERLAPS)
        * len(TOP_K_VALUES)
        * len(SCORE_THRESHOLDS)
        * len(RERANK_TOP_K_VALUES)
        * len(MAX_CONTEXT_CHARS)
    )

    # Generate all trial parameters
    trial_params = list(
        itertools.product(
            CHUNK_SIZES, CHUNK_OVERLAPS, TOP_K_VALUES, SCORE_THRESHOLDS, RERANK_TOP_K_VALUES, MAX_CONTEXT_CHARS
        )
    )

    trials: List[Dict[str, Any]] = []

    # Parallelize trials
    if max_workers <= 1 or len(trial_params) == 1:
        # Sequential execution
        for trial_num, (chunk_size, chunk_overlap, top_k, threshold, rerank_top_k, max_ctx) in enumerate(
            trial_params, start=1
        ):
            trial = _run_single_trial(
                trial_num=trial_num,
                total_trials=total_trials,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                top_k=top_k,
                threshold=threshold,
                rerank_top_k=rerank_top_k,
                max_ctx=max_ctx,
                base_config=base_config,
                agent_keys=agent_keys,
                use_recorded=use_recorded,
                timeout_seconds=timeout_seconds,
                max_workers=max_workers,
            )
            trials.append(trial)
    else:
        # Parallel execution of trials
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_trial = {
                executor.submit(
                    _run_single_trial,
                    trial_num=trial_num,
                    total_trials=total_trials,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    top_k=top_k,
                    threshold=threshold,
                    rerank_top_k=rerank_top_k,
                    max_ctx=max_ctx,
                    base_config=base_config,
                    agent_keys=agent_keys,
                    use_recorded=use_recorded,
                    timeout_seconds=timeout_seconds,
                    max_workers=max_workers,
                ): trial_num
                for trial_num, (chunk_size, chunk_overlap, top_k, threshold, rerank_top_k, max_ctx) in enumerate(
                    trial_params, start=1
                )
            }
            completed_trials: Dict[int, Dict[str, Any]] = {}
            for future in concurrent.futures.as_completed(future_to_trial):
                trial_num = future_to_trial[future]
                try:
                    trial = future.result()
                    completed_trials[trial_num] = trial
                    print(f"[info] Completed trial {trial_num}/{total_trials}", file=sys.stderr)
                except Exception as exc:
                    print(
                        f"[error] Trial {trial_num} failed: {exc}",
                        file=sys.stderr,
                    )
            # Sort trials by trial number to maintain order
            trials = [completed_trials[i] for i in sorted(completed_trials.keys())]

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
        trials, best, agent_keys, base_config, use_recorded, bool(ragas_available), max_workers
    )

    print(f"Saved best configuration to {save_path}")
    print(f"Wrote tuning report to {report_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
