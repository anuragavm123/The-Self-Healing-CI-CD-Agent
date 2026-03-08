from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass
class LLMConfig:
    model: str
    api_key: str
    base_url: str | None = None


def load_llm_config() -> LLMConfig | None:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            return None
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-coder")
        return LLMConfig(model=model, api_key=api_key, base_url="https://api.deepseek.com")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    return LLMConfig(model=model, api_key=api_key)


def suggest_fix_from_log(log_text: str) -> dict[str, Any] | None:
    config = load_llm_config()
    if not config:
        return None

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    system_prompt = (
        "You are a CI self-healing assistant. Return strict JSON only with keys: "
        "reason, file_path, old_code, new_code."
    )
    user_prompt = (
        "Analyze this failing test/lint log and propose a minimal safe code fix. "
        "Only propose one fix.\n\n"
        f"{log_text[:14000]}"
    )

    response = client.chat.completions.create(
        model=config.model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    if not content:
        return None
    return json.loads(content)
