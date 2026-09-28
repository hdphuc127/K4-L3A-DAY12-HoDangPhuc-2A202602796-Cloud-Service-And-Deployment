"""Gọi LLM thật qua OpenAI API.

Chỉ dùng khi OPENAI_API_KEY được set trong .env — nếu không, main.py rơi về
utils.mock_llm để không tốn tiền và giữ test ổn định.
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

# Giá theo 1.000 token của gpt-4o-mini (USD), cập nhật nếu đổi model.
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.00060


@lru_cache(maxsize=1)
def _client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def ask_llm(question: str, history: list[dict] | None = None, *, api_key: str, model: str) -> dict:
    """Gọi OpenAI Chat Completions.

    Trả về cùng shape với utils.mock_llm.ask_llm: answer, tokens_in,
    tokens_out, cost_usd — để main.py không cần biết đang dùng mock hay thật.
    """
    history = history or []
    messages = [*history, {"role": "user", "content": question}]

    response = _client(api_key).chat.completions.create(model=model, messages=messages)

    answer = response.choices[0].message.content or ""
    tokens_in = response.usage.prompt_tokens if response.usage else 0
    tokens_out = response.usage.completion_tokens if response.usage else 0
    cost = tokens_in / 1000 * PRICE_INPUT_PER_1K + tokens_out / 1000 * PRICE_OUTPUT_PER_1K

    return {
        "answer": answer,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 8),
    }
