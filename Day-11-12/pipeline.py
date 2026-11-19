"""End-to-end pipeline: question -> retrieve -> generate -> answer.

Ask one question:          uv run python pipeline.py "How many PTO days do employees get?"
Run all test questions:    uv run python pipeline.py
The second form writes pipeline_outputs.json (Day 12 evaluates this file).
"""
import json
import sys
import time

import config
from generate import generate_answer
from retrieve import retrieve_chunks

TEST_FILE = "test_questions.json"
OUTPUT_FILE = "pipeline_outputs.json"


def answer_question(query: str) -> dict:
    """Retrieve chunks for the question, then generate the answer from them."""
    retrieval_result = retrieve_chunks(query)
    generation_result = generate_answer(query=query, chunks=retrieval_result["retrieved_chunks"])
    return {**generation_result, "retrieval": retrieval_result}


def build_row(item: dict, result: dict) -> dict:
    """One row of pipeline_outputs.json in the format from the brief."""
    chunks = result["retrieval"]["retrieved_chunks"]
    return {
        "id": item["id"],
        "question": item["question"],
        "expected_answer": item["expected_answer"],
        "actual_answer": result["answer"],
        "retrieved_context": [c["content"] for c in chunks],
        "context_sources": [{"source": c["source"], "page": c["page"], "score": c["relevance_score"]}
                            for c in chunks],
        "context_used": result["context_used"],
        "model": result["model"],
        "thinking": result["thinking"],
        "finish_reason": result["finish_reason"],
        "embedding_model": result["retrieval"]["embedding_model"],
        "top_k": result["retrieval"]["top_k"],
        "chunk_size_chars": config.CHUNK_SIZE,
        "prompt_tokens": result["prompt_tokens"],
        "tokens_generated": result["tokens_generated"],
        "retrieval_time_ms": result["retrieval"]["retrieval_time_ms"],
        "generation_time_ms": result["generation_time_ms"],
        "source_document": item.get("source_document"),
        "difficulty": item.get("difficulty"),
        "type": item.get("type"),
        "error": None,
        "passed": None,
        "rating_note": "",
    }


def error_row(item: dict, error: Exception) -> dict:
    """If one question fails (for example Ollama is not running), keep going and record the error."""
    return {
        "id": item["id"], "question": item["question"], "expected_answer": item["expected_answer"],
        "actual_answer": "", "retrieved_context": [], "context_sources": [], "context_used": "",
        "model": config.LLM_MODEL, "thinking": config.REASONING_EFFORT != "none",
        "finish_reason": None, "embedding_model": config.EMBEDDING_MODEL, "top_k": config.TOP_K,
        "chunk_size_chars": config.CHUNK_SIZE, "prompt_tokens": None, "tokens_generated": None,
        "retrieval_time_ms": None, "generation_time_ms": None,
        "source_document": item.get("source_document"), "difficulty": item.get("difficulty"),
        "type": item.get("type"), "error": f"{type(error).__name__}: {error}",
        "passed": None, "rating_note": "",
    }


def run_all() -> None:
    with open(TEST_FILE, encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Model: {config.LLM_MODEL} | top_k={config.TOP_K} | "
          f"chunk_size={config.CHUNK_SIZE} characters | {len(questions)} questions\n")
    rows = []
    start = time.time()
    for i, item in enumerate(questions, start=1):
        print(f"[{i}/{len(questions)}] {item['id']}: {item['question'][:70]}")
        try:
            row = build_row(item, answer_question(item["question"]))
            print(f"   {row['generation_time_ms'] / 1000:.1f} s, prompt_tokens={row['prompt_tokens']}, "
                  f"finish={row['finish_reason']}")
            print(f"   ANSWER: {row['actual_answer'][:150].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"   ERROR: {e}")
            row = error_row(item, e)
        rows.append(row)
        # save after every question, so a crash halfway does not lose the finished rows
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(rows)} rows to {OUTPUT_FILE} in {(time.time() - start) / 60:.1f} minutes.")
    print('Now read each answer and fill in "passed" (true/false) and "rating_note" by hand.')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = answer_question(" ".join(sys.argv[1:]))
        print(result["answer"])
        print(f"\nfinish_reason={result['finish_reason']}, prompt_tokens={result['prompt_tokens']}")
        for c in result["retrieval"]["retrieved_chunks"]:
            print(f"  {c['relevance_score']:.3f}  {c['source']} p{c['page']}")
    else:
        run_all()
