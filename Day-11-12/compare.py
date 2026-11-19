"""Exercise 4: compare the local and the cloud pipeline.

Reads eval_results_local.json, eval_results_cloud.json, pipeline_outputs_local.json and
pipeline_outputs_cloud.json, prints one markdown table and saves the same text to compare_output.md.

Run:  uv run python compare.py
"""
import json
import statistics

REFUSAL = "cannot find this information"
LINES = []


def out(text: str = "") -> None:
    """Print a line and keep it for compare_output.md."""
    print(text)
    LINES.append(text)


def load(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def mean_2se(values: list) -> tuple:
    """Mean and 2 x standard error (SE = standard deviation / sqrt(n))."""
    n = len(values)
    mean = statistics.mean(values)
    se = statistics.stdev(values) / n ** 0.5 if n > 1 else 0.0
    return mean, 2 * se


def scores_by_id(rows: list, metric: str) -> dict:
    """{question id: score} for one metric, skipping rows where the metric had no score."""
    result = {}
    for row in rows:
        m = row["metrics"].get(metric)
        if m and m["score"] is not None and not m["error"]:
            result[row["id"]] = m["score"]
    return result


def main() -> None:
    eval_local = load("eval_results_local.json")
    eval_cloud = load("eval_results_cloud.json")
    out_local = load("pipeline_outputs_local.json")
    out_cloud = load("pipeline_outputs_cloud.json")

    local_model = out_local[0]["model"]
    cloud_model = out_cloud[0]["model"]
    out(f"## Local ({local_model}) vs cloud ({cloud_model})")
    out()
    out("Source: eval_results_local.json, eval_results_cloud.json (judge "
        f"{eval_local[0]['judge']}). Values are mean ± 2×SE.")
    out()

    # 1. Metric table
    out("| Metric | n | Local | Cloud | Cloud minus local (per question) | Verdict |")
    out("|---|---|---|---|---|---|")
    for metric in eval_local[0]["metrics"]:
        local = scores_by_id(eval_local, metric)
        cloud = scores_by_id(eval_cloud, metric)
        ids = sorted(set(local) & set(cloud))  # questions with a score on both sides
        l_mean, l_err = mean_2se([local[i] for i in ids])
        c_mean, c_err = mean_2se([cloud[i] for i in ids])
        d_mean, d_err = mean_2se([cloud[i] - local[i] for i in ids])
        # if the range of the difference includes zero, we cannot say which side is better
        if d_mean - d_err <= 0 <= d_mean + d_err:
            verdict = "no clear difference"
        elif d_mean > 0:
            verdict = "cloud higher"
        else:
            verdict = "local higher"
        out(f"| {metric} | {len(ids)} | {l_mean:.2f} ± {l_err:.2f} | {c_mean:.2f} ± {c_err:.2f} "
            f"| {d_mean:+.2f} ± {d_err:.2f} | {verdict} |")
    out()

    # 2. Speed, tokens and failures
    out("Source: pipeline_outputs_local.json, pipeline_outputs_cloud.json")
    out()
    out("| Run | Median generation time | Slowest | Avg completion tokens | Empty or failed answers "
        "| Unanswerable refused |")
    out("|---|---|---|---|---|---|")
    for name, rows in [("Local", out_local), ("Cloud", out_cloud)]:
        times = [r["generation_time_ms"] / 1000 for r in rows if r["generation_time_ms"]]
        tokens = [r["tokens_generated"] for r in rows if r["tokens_generated"] is not None]
        empty = sum(1 for r in rows if not r["actual_answer"].strip() or r.get("error"))
        unanswerable = [r for r in rows if r.get("type") == "unanswerable"]
        refused = sum(1 for r in unanswerable if REFUSAL in r["actual_answer"].lower())
        out(f"| {name} | {statistics.median(times):.1f} s | {max(times):.1f} s "
            f"| {statistics.mean(tokens):.0f} | {empty} | {refused} of {len(unanswerable)} |")
    out()
    out("Note: tokens_generated is the API's completion_tokens (includes reasoning tokens where reported).")

    with open("compare_output.md", "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    print("\nSaved to compare_output.md")


if __name__ == "__main__":
    main()
