from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib import error, request
from typing import Any

from openai import OpenAI


@dataclass
class LLMConfig:
    model: str
    api_key: str
    base_url: str | None = None


def get_llm_runtime_info() -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    config = load_llm_config()
    if not config:
        return {
            "provider": provider,
            "configured": False,
            "model": None,
            "base_url": None,
            "api_key_present": False,
        }

    return {
        "provider": provider,
        "configured": True,
        "model": config.model,
        "base_url": config.base_url,
        "api_key_present": bool(config.api_key),
    }


def _normalize_ollama_base_url(raw_base_url: str) -> str:
    base = raw_base_url.strip().rstrip("/")
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def _ollama_native_chat_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/api/chat"


def _suggest_fix_via_ollama_native(log_text: str, config: LLMConfig) -> dict[str, Any] | None:
    if not config.base_url:
        return None

    endpoint = _ollama_native_chat_url(config.base_url)
    system_prompt = (
        "You are a CI self-healing assistant. Return strict JSON only with keys: "
        "reason, file_path, old_code, new_code."
    )
    user_prompt = (
        "Analyze this failing test/lint log and propose a minimal safe code fix. "
        "Only propose one fix.\n\n"
        f"{log_text[:14000]}"
    )

    payload = {
        "model": config.model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    content = body.get("message", {}).get("content")
    if not content:
        return None

    try:
        parsed = _parse_json_response(content)
        if isinstance(parsed, dict):
            return parsed
        return None
    except json.JSONDecodeError:
        return None


def _parse_json_response(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        return None
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(?P<body>\{.*?\})\s*```", content, re.DOTALL)
    if fence_match:
        try:
            parsed = json.loads(fence_match.group("body"))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"\{.*\}", content, re.DOTALL)
    if object_match:
        try:
            parsed = json.loads(object_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return None


def load_llm_config() -> LLMConfig | None:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        base_url = _normalize_ollama_base_url(
            os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
        )
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")
        return LLMConfig(model=model, api_key=api_key, base_url=base_url)

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

    provider = os.getenv("LLM_PROVIDER", "openai").lower()

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

    request_payload: dict[str, Any] = {
        "model": config.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = client.chat.completions.create(**request_payload)
    except Exception as exc:
        # Some Ollama setups expose only native endpoints (/api/*), not /v1.
        if provider == "ollama" and "404" in str(exc):
            return _suggest_fix_via_ollama_native(log_text=log_text, config=config)

        # Some DeepSeek model variants reject response_format; retry with plain text output.
        if provider == "deepseek":
            try:
                relaxed_payload = dict(request_payload)
                relaxed_payload.pop("response_format", None)
                response = client.chat.completions.create(**relaxed_payload)
            except Exception:
                return None
        else:
            return None

    content = response.choices[0].message.content
    if not content:
        return None
    return _parse_json_response(content)
