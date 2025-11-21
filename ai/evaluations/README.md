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

## Hyperparameter tuning

Use `ai/evaluations/hparam_tuning.py` to search chunking + retrieval settings, log trial scores, and write back the best config. By default it invokes live agents for every trial (falls back to recorded answers only if a live call fails).

### How it works
- Sweeps chunk sizes, overlaps, top_k, and optional score thresholds (see search space in the script).
- Evaluates all agents using recorded answers (no live agent calls) but can pull live contexts from ChromaDB if it is reachable and credentials are set.
- Scores each trial by the mean of ragas metrics (or lexical fallbacks when ragas/LLM is unavailable).
- Writes a Markdown report to `ai/evaluations/results/hparam_tuning.md` and updates `rag_config.json` with the best settings (including metadata about the run).

### Run it
```bash
# Ensure deps installed and GOOGLE_API_KEY is set if you want ragas
# Default: live agents + live contexts (if Chroma reachable)
python ai/evaluations/hparam_tuning.py

# If you want a fast offline sweep that skips live agent calls:
python ai/evaluations/hparam_tuning.py --recorded
```

### Outputs to expect
- Best config persisted: `rag_config.json` (drives chunking, retrieval, and eval defaults).
- Trial report: `ai/evaluations/results/hparam_tuning.md` with trial grid, scores, and per‑agent metrics for the best trial.

### Tips
- Start your ChromaDB service and set `CHROMA_HOST`/`CHROMA_PORT` so live contexts are available; otherwise the tuner falls back to fixture contexts.
- Install `ragas` and `langchain-google-genai` (already listed in `ai/requirements.txt`) and export `GOOGLE_API_KEY` to get non-fallback ragas metrics.
- Re-run tuning whenever you change ingestion, embeddings, or want to refresh the best config.

## Datasets

Evaluation cases live in `ai/evaluations/datasets.py`. Data Science fixtures are copied from the IITM Academics page scraped in the repository; Electronic Systems fixtures are high-level program notes and should be replaced with production data once the Electronic Systems collections land in ChromaDB.

Each case stores the question, ground truth, reference contexts, and the recorded first-run answer. The runner can call the real agent (when `--live` is set) or reuse the recorded answer for deterministic comparisons.
