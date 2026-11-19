# Day 11 and 12: Local Document Q&A (RAG) on Local Models

A RAG pipeline that answers questions about five internal PDF documents of a fictional
company (NovaTech Solutions). Everything runs locally with Ollama, because the client
works in a regulated industry and cannot send data to a cloud AI service.

## Where things are

| File | Purpose |
|---|---|
| `config.py` | All settings in one place (models, URLs, chunk size, top_k, prompt, token cap name) |
| `parse_check.py` | Step 1 check: compares pypdf default vs layout mode on a page with a table |
| `ingest.py` | Load PDFs, chunk, embed, store in ChromaDB |
| `retrieve.py` | Embed the question, return the top_k chunks with source, page and score |
| `generate.py` | Send labelled chunks and the question to the local LLM |
| `pipeline.py` | End to end: question, retrieve, generate, answer |
| `benchmark.py` | Exercise 1: compares local models on speed and quality |
| `test_questions.json` | 18 test questions with expected answers |
| `benchmark_results.json` | Exercise 1 results with hand-filled quality ratings |
| `pipeline_outputs.json` | The pipeline run over all test questions (evaluated on Day 12) |
| `Day-11/decision_log.md` | Day 11 decision log (written by hand) |
| `Day-12/` | Day 12 evaluation report |
| `AGENTS.md` | Instructions for the AI coding assistant |
| `documents/` | The five PDFs |

Note: the decision log is in `Day-11/decision_log.md`, not in the project root.

## Setup (Windows)

1. Install Ollama natively (not in WSL) from https://ollama.com/download.
2. Set the context window to 8192 and restart Ollama:
   ```powershell
   [Environment]::SetEnvironmentVariable("OLLAMA_CONTEXT_LENGTH", "8192", "User")
   ```
3. Pull the models:
   ```powershell
   ollama pull qwen3.5:4b-q4_K_M
   ollama pull nomic-embed-text
   ollama pull qwen3.5:2b-q4_K_M
   ```
4. Install uv, then the Python environment:
   ```powershell
   uv sync
   ```
5. Check the connection: `uv run python test_api.py` should print one sentence and `stop`,
   and `ollama ps` should show CONTEXT 8192.

`grpcio` is pinned to 1.71.0 because Windows Smart App Control blocked the DLL of grpcio 1.85.3,
which ChromaDB imports.

## How to run

```powershell
uv run python ingest.py                       # rebuilds chroma_db/ (not committed)
uv run python pipeline.py "your question"     # ask one question
uv run python pipeline.py                     # run all test questions, writes pipeline_outputs.json
uv run python benchmark.py                    # Exercise 1, writes benchmark_results.json
```

`chroma_db/` is not in the repository. `uv run python ingest.py` rebuilds it from the PDFs.

## Switching to the cloud model (Day 12)

No code change, only environment variables (PowerShell):

```powershell
$env:LLM_BASE_URL = "https://<resource>.openai.azure.com/openai/v1/"
$env:LLM_API_KEY = $env:AZURE_OPENAI_API_KEY
$env:LLM_MODEL = "gpt-5.6-luna"
$env:TOKEN_LIMIT_PARAM = "max_completion_tokens"
```

Embeddings stay local, so the same `chroma_db/` serves both runs.

## Configuration used

- LLM: `qwen3.5:4b-q4_K_M`, thinking off (`reasoning_effort="none"`), temperature 0.3, max 1024 tokens
- Embeddings: `nomic-embed-text` (768 dimensions), cosine distance
- Parsing: pypdf with `extraction_mode="layout"`
- Chunking: 512 characters, 50 characters overlap (RecursiveCharacterTextSplitter, per page)
- Retrieval: top_k = 5
- Context window: 8192 tokens

## AI assistant used

Claude (Anthropic, Claude Opus 5.5) helped write the code and check the benchmark answers.
The pipeline model itself is local. I reviewed the ratings, and the decision log is written by me.
