"""Exercise 1: compare local models on speed and quality.

Run:  uv run python benchmark.py
Writes benchmark_results.json. Fill in quality_rating and rating_note by hand afterwards.
"""
import json
import os
import subprocess
import time

from openai import OpenAI

import config

# Which models to run. Override to add a model without re-running the others, e.g.
#   $env:BENCH_MODELS = "llama3.2:3b"
MODELS = os.getenv("BENCH_MODELS", "qwen3.5:4b-q4_K_M,qwen3.5:2b-q4_K_M").split(",")
TEMPERATURE = 0.7
MAX_TOKENS = 1024
OUTPUT_FILE = "benchmark_results.json"

PROMPTS = [
    {"category": "factual",
     "prompt": "What causes tides on Earth? Answer in 2-3 sentences."},
    {"category": "reasoning",
     "prompt": "If a train travels 120km in 1.5 hours, and then 80km in 1 hour, "
               "what is the average speed for the entire journey?"},
    {"category": "summarization",
     "prompt": "Summarize the following paragraph in one sentence:\n\n"
               "NovaTech Solutions supports hybrid work arrangements. Employees in eligible roles "
               "may work remotely for up to three days per week, subject to manager approval. "
               "Employees still within their six month probationary period may work remotely for "
               "up to one day per week. Each team must designate at least one mandatory in-office "
               "day per week for collaborative work."},
    {"category": "structured",
     "prompt": 'List 3 European capitals. Respond ONLY with valid JSON: [{"city": ..., "country": ...}]'},
    {"category": "code",
     "prompt": "Write a Python function is_palindrome(text) that returns True if the text reads "
               "the same forwards and backwards, ignoring case and spaces. Only the code, no explanation."},
    {"category": "instruction_following",
     "prompt": "Give exactly 3 tips for writing good test questions for a RAG system. "
               "Use a numbered list, maximum 12 words per tip, and no other text."},
    {"category": "grounded_qa",
     "prompt": "Answer ONLY from the context. If the answer is not in the context, say "
               '"I cannot find this information in the provided documents."\n\n'
               "Context: All full-time employees receive twenty-five (25) days of paid time off per "
               "calendar year. Unused PTO may be carried over up to a maximum of five (5) days.\n\n"
               "Question: How many sick days do employees get per year?"},
]


def run_benchmark(client: OpenAI, model: str, prompt_item: dict) -> dict:
    """Send one prompt to one model and record speed and the answer."""
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt_item["prompt"]}],
        temperature=TEMPERATURE,
        reasoning_effort=config.REASONING_EFFORT,
        **{config.TOKEN_LIMIT_PARAM: MAX_TOKENS},
    )
    elapsed = time.time() - start
    choice = response.choices[0]
    usage = response.usage
    answer = choice.message.content or ""

    # An empty answer is the most expensive silent bug, so make it visible
    if not answer.strip():
        print(f"   WARNING: empty answer, finish_reason={choice.finish_reason}")

    return {
        "model": model,
        "category": prompt_item["category"],
        "prompt": prompt_item["prompt"],
        "response": answer,
        "thinking": config.REASONING_EFFORT != "none",
        "reasoning_effort": config.REASONING_EFFORT,
        "temperature": TEMPERATURE,
        "finish_reason": choice.finish_reason,
        "time_seconds": round(elapsed, 2),
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        # completion tokens divided by the whole call time (includes prompt reading)
        "tokens_per_second": round(usage.completion_tokens / elapsed, 1)
        if usage and usage.completion_tokens else None,
        "quality_rating": None,
        "rating_note": "",
    }


def warm_up(client: OpenAI, model: str) -> None:
    """Load the model into memory first, so load time is not counted in the first prompt."""
    print(f"Loading {model} ...")
    client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Hi"}],
        reasoning_effort=config.REASONING_EFFORT,
        **{config.TOKEN_LIMIT_PARAM: 5},
    )


def main() -> None:
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    results = []

    for model in MODELS:
        warm_up(client, model)
        for i, item in enumerate(PROMPTS, start=1):
            print(f"[{model}] {i}/{len(PROMPTS)} {item['category']}")
            row = run_benchmark(client, model, item)
            print(f"   {row['time_seconds']} s, {row['completion_tokens']} tokens, "
                  f"{row['tokens_per_second']} tok/s, finish={row['finish_reason']}")
            results.append(row)
        # Free the RAM before loading the next model (16 GB laptop)
        subprocess.run(["ollama", "stop", model], check=False)

    # Keep the rows (and hand-filled ratings) of models that were not re-run this time
    old_rows = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            old_rows = [r for r in json.load(f) if r["model"] not in MODELS]
    all_rows = old_rows + results

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} new rows ({len(all_rows)} in total) to {OUTPUT_FILE}")
    print("Now open the file and fill in quality_rating (1-5) and rating_note for every row.")


if __name__ == "__main__":
    main()
