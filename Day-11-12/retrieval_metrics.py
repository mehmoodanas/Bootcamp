"""Day 12 Exercise 3, Step 4 (optional): retrieval quality without a judge.

Computes Hit@k and MRR from context_sources in the pipeline output files, using the
source_document label of each test question. No API calls, same result every run.
Unanswerable questions (no source_document) are skipped.

Run:  uv run python retrieval_metrics.py
Writes retrieval_metrics.json
"""
import json

# (label, file) pairs: the final run plus the earlier experiments for comparison
RUNS = [
    ("final: 1000 chars, top_k 5", "pipeline_outputs_local.json"),
    ("1000 chars, top_k 8", "pipeline_outputs_4b_c1000_k8.json"),
    ("512 chars, top_k 5", "pipeline_outputs_4b_c512_k5.json"),
]


def score_run(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        rows = [r for r in json.load(f) if r.get("source_document")]

    hits, reciprocal_ranks, per_question = 0, [], []
    for r in rows:
        expected = [s.strip() for s in r["source_document"].split(";")]
        sources = [c["source"] for c in r["context_sources"]]
        # rank of the first retrieved chunk that comes from an expected document
        rank = next((i + 1 for i, s in enumerate(sources) if s in expected), None)
        hits += rank is not None
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        per_question.append({"id": r["id"], "expected": expected, "first_hit_rank": rank,
                             "all_expected_found": all(e in sources for e in expected)})

    n = len(rows)
    return {
        "file": path,
        "top_k": rows[0].get("top_k"),
        "questions": n,
        "hit_at_k": round(hits / n, 3),
        "mrr": round(sum(reciprocal_ranks) / n, 3),
        "all_expected_sources_found": sum(q["all_expected_found"] for q in per_question),
        "per_question": per_question,
    }


def main() -> None:
    results = {label: score_run(path) for label, path in RUNS}
    with open("retrieval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("| Run | top_k | Hit@k | MRR | All sources found (conflict questions too) |")
    print("|---|---|---|---|---|")
    for label, r in results.items():
        print(f"| {label} | {r['top_k']} | {r['hit_at_k']} | {r['mrr']} | "
              f"{r['all_expected_sources_found']}/{r['questions']} |")
    print("\nSaved to retrieval_metrics.json")


if __name__ == "__main__":
    main()
