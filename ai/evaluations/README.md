# Agent Evaluation

This package records lightweight ragas-style benchmarks for each Google ADK agent that ships in `ai/agents`.

## Quick start

```bash
# (inside the ai virtualenv)
python ai/evaluations/run_ragas.py
```

The command above runs against the recorded first-run answers that live next to the fixtures and writes a report to `ai/evaluations/results/first_run_metrics.json`.

Enable a live end-to-end run once ragas and the Google ADK credentials are configured:

```bash
python ai/evaluations/run_ragas.py --live
```

By default the runner prefers ragas metrics when the library is available. Pass `--force-fallback` to stick with the deterministic lexical heuristics that produced the first-run snapshot.

## Datasets

Evaluation cases live in `ai/evaluations/datasets.py`. Data Science fixtures are copied from the IITM Academics page scraped in the repository; Electronic Systems fixtures are high-level program notes and should be replaced with production data once the Electronic Systems collections land in ChromaDB.

Each case stores the question, ground truth, reference contexts, and the recorded first-run answer. The runner can call the real agent (when `--live` is set) or reuse the recorded answer for deterministic comparisons.
