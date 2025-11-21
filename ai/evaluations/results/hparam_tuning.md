# RAG Hyperparameter Tuning Report
- Generated: 2025-11-21T15:16:46.108564+00:00
- Agents evaluated: ds_foundation, ds_diploma, ds_degree, es_foundation, es_diploma, es_degree
- Ragas available: True
- Answers source: recorded references
- Scoring rule: mean of answer_relevancy, context_precision, context_recall, faithfulness across agents (fallback metrics when ragas unavailable)
- Context mode: live retrieval
- Base config: {'chunk_size': 700, 'chunk_overlap': 120, 'top_k': 4, 'score_threshold': None, 'rerank_top_k': None, 'max_context_chars': 1800, 'prefer_ragas': True, 'ragas_model': 'gemini-1.5-flash', 'embedding_model': 'text-embedding-004', 'use_live_contexts': True}

## Trials
|Trial|Chunk Size|Overlap|Top K|Score Threshold|Score|Metrics source|
|---|---|---|---|---|---|---|
|1|700|120|4|-|0.4094|ragas|
|2|700|120|4|0.35|0.5053|ragas|
|3|700|120|8|-|0.4616|ragas|
|4|700|120|8|0.35|0.5053|ragas|
|5|700|200|4|-|0.4094|ragas|
|6|700|200|4|0.35|0.5053|ragas|
|7|700|200|8|-|0.4602|ragas|
|8|700|200|8|0.35|0.5053|ragas|
|9|1000|120|4|-|0.4094|ragas|
|10|1000|120|4|0.35|0.5053|ragas|
|11|1000|120|8|-|0.4602|ragas|
|12|1000|120|8|0.35|0.5053|ragas|
|13|1000|200|4|-|0.4094|ragas|
|14|1000|200|4|0.35|0.5053|ragas|
|15|1000|200|8|-|0.4602|ragas|
|16|1000|200|8|0.35|0.5053|ragas|

## Best configuration
- Score: 0.5053
- Chunk size / overlap: 700 / 120
- Top K: 4; score_threshold: 0.35
- Metrics source: ragas
- Config summary: {'chunk_size': 700, 'chunk_overlap': 120, 'top_k': 4, 'score_threshold': 0.35, 'rerank_top_k': None, 'max_context_chars': 1800, 'prefer_ragas': True, 'ragas_model': 'gemini-1.5-flash', 'embedding_model': 'text-embedding-004', 'use_live_contexts': True}

### Per-agent metrics (best trial)
- Data Science - Foundation (ds_foundation): answer_relevancy=0.5673, context_precision=0.5384, context_recall=0.607, faithfulness=0.5384
- Data Science - Diploma (ds_diploma): answer_relevancy=0.5929, context_precision=0.4258, context_recall=0.5561, faithfulness=0.4258
- Data Science - Degree (ds_degree): answer_relevancy=0.5819, context_precision=0.492, context_recall=0.5459, faithfulness=0.492
- Electronic Systems - Foundation (es_foundation): answer_relevancy=0.489, context_precision=0.323, context_recall=0.4889, faithfulness=0.323
- Electronic Systems - Diploma (es_diploma): answer_relevancy=0.5925, context_precision=0.4238, context_recall=0.5041, faithfulness=0.4238
- Electronic Systems - Degree (es_degree): answer_relevancy=0.5551, context_precision=0.5149, context_recall=0.6105, faithfulness=0.5149