"""Compare two embedding models on retrieval only (no LLM, no change to the final pipeline).

For each answerable test question: is the expected source document in the top_k chunks,
at which rank, and (for conflict questions with two sources) are BOTH sources found?

Before running, build the second database (same chunking, 1000 characters, overlap 80):
    ollama pull mxbai-embed-large
    $env:EMBEDDING_MODEL = "mxbai-embed-large"; $env:CHROMA_DIR = "chroma_db_mxbai"
    uv run python ingest.py
    Remove-Item Env:EMBEDDING_MODEL, Env:CHROMA_DIR

Run:  uv run python compare_embeddings.py
Writes embedding_comparison.json.
"""
import json
import time

import chromadb
from openai import OpenAI

import config

# (embedding model, database folder built with that model)
MODELS = [
    ("nomic-embed-text", "chroma_db_1000"),
    ("mxbai-embed-large", "chroma_db_mxbai"),
]
TOP_K = config.TOP_K
OUTPUT_FILE = "embedding_comparison.json"

client = OpenAI(base_url=config.EMBEDDING_BASE_URL, api_key=config.EMBEDDING_API_KEY)


def search(model: str, db_dir: str, question: str) -> tuple[list[str], int]:
    """Embed the question with the model and return the sources of the top_k chunks."""
    start = time.time()
    vector = client.embeddings.create(model=model, input=[question]).data[0].embedding
    collection = chromadb.PersistentClient(path=db_dir).get_collection(
        name=config.COLLECTION_NAME, embedding_function=None)
    result = collection.query(query_embeddings=[vector], n_results=TOP_K, include=["metadatas"])
    sources = [m["source"] for m in result["metadatas"][0]]
    return sources, round((time.time() - start) * 1000)


def main() -> None:
    with open("test_questions.json", encoding="utf-8") as f:
        questions = [q for q in json.load(f) if q.get("source_document")]  # skip unanswerable

    rows = []
    summary = {}
    for model, db_dir in MODELS:
        print(f"\n=== {model} ({db_dir}) ===")
        search(model, db_dir, "warm up")  # load the model first, so load time is not counted
        hits, all_found, ranks, times = 0, 0, [], []
        for q in questions:
            expected = [s.strip() for s in q["source_document"].split(";")]
            sources, ms = search(model, db_dir, q["question"])
            first = next((i + 1 for i, s in enumerate(sources) if s in expected), None)
            both = all(e in sources for e in expected)
            hits += first is not None
            all_found += both
            ranks.append(first)
            times.append(ms)
            print(f"  {q['id']}: first expected source at rank {first}, all sources found: {both}")
            rows.append({"embedding_model": model, "id": q["id"], "expected_sources": expected,
                         "retrieved_sources": sources, "first_hit_rank": first,
                         "all_expected_sources_found": both, "retrieval_time_ms": ms})
        n = len(questions)
        found = [r for r in ranks if r]
        summary[model] = {
            "questions": n,
            "expected_source_in_top_k": hits,
            "all_expected_sources_in_top_k": all_found,
            "expected_source_at_rank_1": sum(1 for r in ranks if r == 1),
            "average_rank_when_found": round(sum(found) / len(found), 2) if found else None,
            "median_retrieval_ms": sorted(times)[len(times) // 2],
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"top_k": TOP_K, "chunk_size_chars": config.CHUNK_SIZE,
                   "summary": summary, "rows": rows}, f, indent=2, ensure_ascii=False)

    print(f"\nSummary (top_k={TOP_K}, {len(questions)} answerable questions):")
    for model, s in summary.items():
        print(f"  {model}: source in top {TOP_K}: {s['expected_source_in_top_k']}/{s['questions']}, "
              f"all sources (conflict questions too): {s['all_expected_sources_in_top_k']}/{s['questions']}, "
              f"rank 1: {s['expected_source_at_rank_1']}, avg rank {s['average_rank_when_found']}, "
              f"median {s['median_retrieval_ms']} ms")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
