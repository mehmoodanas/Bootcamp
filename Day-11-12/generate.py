"""Generation: send the retrieved chunks and the question to the local LLM.

Every chat call has the same shape (reasoning_effort and the token cap come from config),
so Day 12 can swap to the cloud model by changing environment variables only.
"""
import time

from openai import OpenAI

import config

_llm_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def build_context(chunks: list[dict]) -> str:
    """Step 6 Prompt: label every chunk with its source and page, so the model can cite it."""
    parts = []
    for number, chunk in enumerate(chunks, start=1):
        parts.append(f"[{number}] (source: {chunk['source']}, page {chunk['page']})\n{chunk['content']}")
    return "\n\n".join(parts)


def generate_answer(query: str, chunks: list[dict]) -> dict:
    """Ask the LLM to answer only from the chunks. Returns the answer and what the model saw."""
    context = build_context(chunks)
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": query},
    ]

    start = time.time()
    response = _llm_client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=config.TEMPERATURE,
        reasoning_effort=config.REASONING_EFFORT,
        **{config.TOKEN_LIMIT_PARAM: config.MAX_TOKENS},
    )
    elapsed_ms = round((time.time() - start) * 1000)

    choice = response.choices[0]
    usage = response.usage
    answer = choice.message.content or ""

    # An empty answer saved silently is the most expensive bug of this capstone
    if not answer.strip():
        print(f"   WARNING: empty answer for '{query[:50]}', finish_reason={choice.finish_reason}")

    return {
        "query": query,
        "answer": answer,
        "context_used": context,
        "model": config.LLM_MODEL,
        "thinking": config.REASONING_EFFORT != "none",
        "finish_reason": choice.finish_reason,
        "generation_time_ms": elapsed_ms,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "tokens_generated": usage.completion_tokens if usage else None,
    }
