# AGENTS.md

Instructions for any AI coding assistant working in this folder.

## Project
Local RAG pipeline over the 5 PDFs in `documents/` (Day 11 and Day 12 capstone).

## Rules
- Local models only. The pipeline model runs in Ollama on this machine. No cloud-tagged models.
- Every chat call sets `reasoning_effort="none"` and passes the token cap as `**{config.TOKEN_LIMIT_PARAM: config.MAX_TOKENS}`.
- All settings live in `config.py`. Other files import from it; no hard-coded model names or URLs.
- Numbers come from files. The assistant may write code that measures, never the numbers themselves.
- The decision log is written by hand by the student, not by the assistant.
- Never read or print `.env` or API keys.
- One step at a time: ingest, retrieve, generate, pipeline, benchmark. Run and commit each step before the next.

## How to run
- Install: `uv sync`
- Check Ollama: `uv run python test_api.py` (expect one sentence and `stop`), then `ollama ps` (CONTEXT must be 8192)
- Rebuild the vector DB: `uv run python ingest.py`
- Benchmark: `uv run python benchmark.py`
- Run all test questions: `uv run python pipeline.py`

## Checks
- After ingest: print `collection.count()`; it must not change when ingest runs again.
- After a pipeline run: no empty answers; every row has `finish_reason`, `prompt_tokens`, and retrieved chunks.