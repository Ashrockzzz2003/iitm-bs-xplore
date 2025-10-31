"""Run ragas (or fallback) evaluations for IITM BS/ES agents."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import re
import sys
import uuid
import warnings
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

CURRENT_DIR = Path(__file__).resolve().parent

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(CURRENT_DIR.parents[1]))
    from ai.evaluations.datasets import (  # type: ignore
        AGENT_REGISTRY,
        EVALUATION_DATA,
        EvaluationCase,
        PROJECT_ROOT,
    )
else:  # pragma: no cover
    from .datasets import AGENT_REGISTRY, EVALUATION_DATA, EvaluationCase, PROJECT_ROOT

for _logger_name in (
    "google",
    "google.genai",
    "google_adk",
    "google_adk.google.adk.tools._function_parameter_parse_util",
):
    logger = logging.getLogger(_logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False

warnings.filterwarnings(
    "ignore", message="Default value is not supported in function declaration schema for Google AI."
)
warnings.filterwarnings("ignore", message="Warning: there are non-text parts in the response.*")
warnings.filterwarnings("ignore", message="App name mismatch detected.*")
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed client session")

_original_showwarning = warnings.showwarning


def _squelch_specific_warnings(message, category, filename, lineno, file=None, line=None):
    text = str(message)
    if text.startswith("Warning: there are non-text parts in the response"):
        return
    if "Default value is not supported in function declaration schema for Google AI." in text:
        return
    _original_showwarning(message, category, filename, lineno, file=file, line=line)


warnings.showwarning = _squelch_specific_warnings


class _SuppressGoogleLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if msg.startswith("Warning: there are non-text parts in the response"):
            return False
        if "Default value is not supported in function declaration schema for Google AI." in msg:
            return False
        return True


for _logger_name in (
    "google",
    "google.genai",
    "google_adk",
    "google_adk.tools",
):
    logging.getLogger(_logger_name).addFilter(_SuppressGoogleLogs())

try:
    from datasets import Dataset as HFDataset  # type: ignore
    from ragas import evaluate as ragas_evaluate  # type: ignore
    from ragas.metrics import (  # type: ignore
        answer_relevancy as ragas_answer_relevancy,
        context_precision as ragas_context_precision,
        context_recall as ragas_context_recall,
        faithfulness as ragas_faithfulness,
    )

    RAGAS_AVAILABLE = True
except Exception:  # pragma: no cover - ragas not always installed locally
    RAGAS_AVAILABLE = False

METRIC_NAMES = (
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "faithfulness",
)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1_score(reference_tokens: Sequence[str], prediction_tokens: Sequence[str]) -> float:
    reference_set = set(reference_tokens)
    prediction_set = set(prediction_tokens)

    if not reference_set or not prediction_set:
        return 0.0

    overlap = reference_set & prediction_set
    precision = _safe_divide(len(overlap), len(prediction_set))
    recall = _safe_divide(len(overlap), len(reference_set))

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


def _fallback_metrics(case: EvaluationCase, answer: str) -> Dict[str, float]:
    """Compute lightweight lexical metrics when ragas is unavailable."""

    answer_tokens = _tokenize(answer)
    ground_tokens = _tokenize(case.ground_truth)
    context_token_lists = [_tokenize(ctx) for ctx in case.contexts]
    context_union = set().union(*context_token_lists) if context_token_lists else set()

    answer_relevancy = _f1_score(ground_tokens, answer_tokens)
    context_recall = _safe_divide(len(set(ground_tokens) & context_union), len(set(ground_tokens)))
    context_precision = _safe_divide(len(set(answer_tokens) & context_union), len(set(answer_tokens)))
    faithfulness = _safe_divide(len(set(answer_tokens) & context_union), len(set(answer_tokens)))

    return {
        "answer_relevancy": round(answer_relevancy, 4),
        "context_precision": round(context_precision, 4),
        "context_recall": round(context_recall, 4),
        "faithfulness": round(faithfulness, 4),
    }


def _ragas_metrics(case: EvaluationCase, answer: str) -> Dict[str, float]:
    if not RAGAS_AVAILABLE:
        return {}

    dataset = HFDataset.from_dict(
        {
            "question": [case.question],
            "answer": [answer],
            "contexts": [list(case.contexts)],
            "ground_truth": [[case.ground_truth]],
        }
    )

    metrics = (
        ragas_answer_relevancy,
        ragas_context_precision,
        ragas_context_recall,
        ragas_faithfulness,
    )

    result = ragas_evaluate(dataset, metrics=list(metrics))

    score_dict: Dict[str, float] = {}

    if hasattr(result, "scores"):
        score_source: Mapping[str, Any] = getattr(result, "scores")
        score_dict = {name: float(score_source.get(name, 0.0)) for name in METRIC_NAMES}
    elif isinstance(result, Mapping):
        score_dict = {name: float(result.get(name, 0.0)) for name in METRIC_NAMES}

    return score_dict


def _load_agent(agent_key: str):
    registry_entry = AGENT_REGISTRY[agent_key]
    module_path: Path = registry_entry["module_path"]
    agent_attr: str = registry_entry["agent_attr"]

    spec = importlib.util.spec_from_file_location(f"{agent_key}_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module for agent {agent_key} at {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{agent_key}_module"] = module
    spec.loader.exec_module(module)

    agent = getattr(module, agent_attr)
    return agent


def _invoke_agent(agent_key: str, agent_obj: Any, question: str) -> str:
    """Attempt to run the agent and return its answer."""

    adk_answer = _invoke_google_adk_agent(agent_key, agent_obj, question)
    if adk_answer is not None:
        return adk_answer

    for candidate_method in ("run", "invoke", "chat", "__call__"):
        if hasattr(agent_obj, candidate_method):
            method = getattr(agent_obj, candidate_method)
            try:
                response = method(question)  # type: ignore[call-arg]
                if isinstance(response, str):
                    return response
                if isinstance(response, Mapping) and "output" in response:
                    return str(response["output"])
                if hasattr(response, "content"):
                    return str(response.content)
            except Exception as exc:  # pragma: no cover
                print(f"[warn] Agent invocation via {candidate_method} failed: {exc}", file=sys.stderr)
                continue

    raise RuntimeError("Agent does not expose a callable interface returning text.")


def _run_coroutine(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        if "asyncio.run()" in str(exc):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(coro)
            finally:
                asyncio.set_event_loop(None)
                loop.close()
        raise


def _invoke_google_adk_agent(agent_key: str, agent_obj: Any, question: str) -> Optional[str]:
    """Run Google ADK agents via an in-memory runner if available."""

    try:
        from google.adk.agents.base_agent import BaseAgent  # type: ignore
        from google.adk.runners import InMemoryRunner  # type: ignore
        from google.genai import types as genai_types  # type: ignore
    except Exception:
        return None

    if not isinstance(agent_obj, BaseAgent):
        return None

    runner_app_name = AGENT_REGISTRY.get(agent_key, {}).get("runner_app_name") or "agents"

    runner = InMemoryRunner(agent=agent_obj, app_name=runner_app_name)
    user_id = "eval-user"
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
        _run_coroutine(
            session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id,
                state={},
            )
        )

    user_message = genai_types.Content(
        role="user", parts=[genai_types.Part(text=question)]
    )

    latest_text: Optional[str] = None
    final_text: Optional[str] = None

    try:
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.author == "user":
                continue
            if not event.content or not event.content.parts:
                continue
            text_parts: List[str] = []
            for part in event.content.parts:
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
                    try:
                        text_parts.append(json.dumps(payload))
                    except TypeError:
                        text_parts.append(str(payload))
                    continue
            if not text_parts:
                continue
            candidate_text = "".join(text_parts).strip()
            if candidate_text:
                latest_text = candidate_text
            if event.is_final_response() and candidate_text:
                final_text = candidate_text
                break
    finally:
        _run_coroutine(runner.close())

    if final_text:
        return final_text
    if latest_text:
        return latest_text

    raise RuntimeError("Agent produced no textual response.")

def evaluate_agent(
    agent_key: str,
    *,
    use_recorded: bool,
    prefer_ragas: bool,
) -> Dict[str, Any]:
    """Evaluate a single agent."""

    cases = EVALUATION_DATA[agent_key]
    per_case_results: List[Dict[str, Any]] = []

    agent_obj = None
    load_failure_reason: Optional[str] = None
    if not use_recorded:
        try:
            agent_obj = _load_agent(agent_key)
        except Exception as exc:
            load_failure_reason = f"{type(exc).__name__}: {exc}"
            print(
                f"[warn] Falling back to recorded answers for {agent_key}: {load_failure_reason}",
                file=sys.stderr,
            )
            use_recorded = True

    metrics_source = "ragas" if prefer_ragas and RAGAS_AVAILABLE else "fallback_lexical"

    for case in cases:
        failure_reason: Optional[str] = load_failure_reason if (use_recorded or agent_obj is None) else None
        if use_recorded or agent_obj is None:
            answer = case.reference_answer
            answer_origin = "recorded_reference"
            print(f"[info] Using recorded reference for {agent_key}/{case.id}")
        else:
            try:
                answer = _invoke_agent(agent_key, agent_obj, case.question)
                print(f"[info] Live response captured for {agent_key}/{case.id}")
                answer_origin = "live_agent"
                failure_reason = None
            except Exception as exc:
                failure_reason = f"{type(exc).__name__}: {exc}"
                print(
                    f"[warn] Live run failed for {agent_key}/{case.id}: {failure_reason}",
                    file=sys.stderr,
                )
                answer = case.reference_answer
                answer_origin = "recorded_reference"

        if prefer_ragas and RAGAS_AVAILABLE:
            metrics = _ragas_metrics(case, answer)
        else:
            metrics = {}

        if not metrics:
            metrics = _fallback_metrics(case, answer)
            metrics_source = "fallback_lexical"

        per_case_results.append(
            {
                "case": asdict(case),
                "answer": answer,
                "answer_origin": answer_origin,
                "metrics": metrics,
                "failure_reason": failure_reason,
            }
        )

    aggregated = _aggregate_metrics(per_case_results)

    return {
        "agent_key": agent_key,
        "agent_label": AGENT_REGISTRY[agent_key]["label"],
        "cases_evaluated": len(per_case_results),
        "metrics_source": metrics_source,
        "aggregated_metrics": aggregated,
        "cases": per_case_results,
    }


def _aggregate_metrics(case_results: Iterable[Mapping[str, Any]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}

    for result in case_results:
        metrics = result["metrics"]
        for name, value in metrics.items():
            totals[name] = totals.get(name, 0.0) + float(value)
            counts[name] = counts.get(name, 0) + 1

    averaged = {
        name: round(_safe_divide(total, counts[name]), 4) for name, total in totals.items() if counts.get(name)
    }

    return averaged


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate IITM agents with ragas.")
    parser.add_argument(
        "--agent",
        dest="agent_keys",
        action="append",
        help="Limit evaluation to the given agent key (can be passed multiple times).",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        default=PROJECT_ROOT / "evaluations" / "results" / "first_run_metrics.json",
        help="Where to write the metrics JSON file.",
    )
    parser.add_argument(
        "--live",
        dest="use_recorded",
        action="store_false",
        help="Run the live agent instead of using recorded first-run answers.",
    )
    parser.add_argument(
        "--force-fallback",
        dest="force_fallback",
        action="store_true",
        help="Skip ragas even if it is available (useful for deterministic runs).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    agent_keys = args.agent_keys or tuple(EVALUATION_DATA.keys())

    prefer_ragas = not args.force_fallback
    use_recorded = args.use_recorded

    results = []
    for key in agent_keys:
        if key not in EVALUATION_DATA:
            print(f"[warn] Skipping unknown agent key: {key}", file=sys.stderr)
            continue

        results.append(
            evaluate_agent(
                key,
                use_recorded=use_recorded,
                prefer_ragas=prefer_ragas,
            )
        )

    output_path: Path = args.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        project_root_repr = str(PROJECT_ROOT.relative_to(Path.cwd()))
    except ValueError:
        project_root_repr = str(PROJECT_ROOT)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ragas_available": RAGAS_AVAILABLE and not args.force_fallback,
        "use_recorded_answers": use_recorded,
        "metrics_preference": "ragas" if prefer_ragas and RAGAS_AVAILABLE else "fallback_lexical",
        "project_root": project_root_repr,
    }

    payload = {
        "metadata": metadata,
        "agents": results,
    }

    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=True)

    print(f"Wrote evaluation report to {output_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
