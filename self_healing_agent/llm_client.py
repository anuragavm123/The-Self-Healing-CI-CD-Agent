from __future__ import annotations

import json
import os
import re
from pathlib import Path
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


def _normalize_deepseek_base_url(raw_base_url: str) -> str:
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


def _suggest_fix_via_deepseek_http(
    log_text: str,
    config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any] | None:
    if not config.base_url:
        return None

    endpoint = f"{config.base_url.rstrip('/')}/chat/completions"
    models_to_try = [config.model]
    if config.model != "deepseek-chat":
        models_to_try.append("deepseek-chat")
    if "deepseek-reasoner" not in models_to_try:
        models_to_try.append("deepseek-reasoner")

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (error.URLError, json.JSONDecodeError, TimeoutError):
            continue

        content = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            continue

        parsed = _parse_json_response(content)
        if isinstance(parsed, dict):
            return parsed

    return None


def _extract_trace_file_line(log_text: str) -> tuple[str, int] | None:
    match = re.search(r"File\s+\"(?P<path>[^\"]+?\.py)\",\s+line\s+(?P<line>\d+)", log_text)
    if not match:
        return None
    return match.group("path"), int(match.group("line"))


def _build_code_context(log_text: str, repo_root: str | Path | None) -> str:
    if repo_root is None:
        return ""

    location = _extract_trace_file_line(log_text)
    if not location:
        return ""

    raw_path, line_number = location
    root = Path(repo_root)
    normalized = raw_path.replace("\\", "/")
    marker = "/src/"
    if normalized.startswith("src/"):
        rel_path = normalized
    elif marker in normalized:
        rel_path = "src/" + normalized.split(marker, 1)[1]
    else:
        rel_path = normalized

    target = root / rel_path
    if not target.exists():
        return ""

    lines = target.read_text(encoding="utf-8").splitlines()
    if not lines:
        return ""

    start = max(1, line_number - 3)
    end = min(len(lines), line_number + 3)
    snippet = "\n".join(f"{idx}: {lines[idx - 1]}" for idx in range(start, end + 1))
    return (
        "\n\nCode context around failing location:\n"
        f"- file: {rel_path}\n"
        f"- line: {line_number}\n"
        "```python\n"
        f"{snippet}\n"
        "```\n"
        "Use exact text from this snippet for old_code/new_code when possible."
    )


def suggest_fix_from_log_with_meta(
    log_text: str,
    repo_root: str | Path | None = None,
) -> tuple[dict[str, Any] | None, str]:
    config = load_llm_config()
    if not config:
        return None, "LLM not configured"

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
        f"{_build_code_context(log_text=log_text, repo_root=repo_root)}"
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

    debug_parts: list[str] = []
    response = None

    try:
        response = client.chat.completions.create(**request_payload)
        debug_parts.append("sdk_json_mode:ok")
    except Exception as exc:
        debug_parts.append(f"sdk_json_mode:err:{type(exc).__name__}")

        # Some Ollama setups expose only native endpoints (/api/*), not /v1.
        if provider == "ollama" and "404" in str(exc):
            native = _suggest_fix_via_ollama_native(log_text=log_text, config=config)
            if native:
                return native, "ollama_native:ok"
            return None, "ollama_native:err"

        # Some DeepSeek model variants reject response_format; retry with plain text output.
        if provider == "deepseek":
            try:
                relaxed_payload = dict(request_payload)
                relaxed_payload.pop("response_format", None)
                response = client.chat.completions.create(**relaxed_payload)
                debug_parts.append("sdk_relaxed_mode:ok")
            except Exception as relaxed_exc:
                debug_parts.append(f"sdk_relaxed_mode:err:{type(relaxed_exc).__name__}")
                http_fix = _suggest_fix_via_deepseek_http(
                    log_text=log_text,
                    config=config,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                if http_fix:
                    return http_fix, "deepseek_http_fallback:ok"
                return None, "; ".join(debug_parts + ["deepseek_http_fallback:err"])
        else:
            return None, "; ".join(debug_parts)

    if response is None:
        return None, "; ".join(debug_parts + ["no_response_object"])

    content = response.choices[0].message.content
    if not content:
        debug_parts.append("empty_content")
        if provider == "deepseek":
            http_fix = _suggest_fix_via_deepseek_http(
                log_text=log_text,
                config=config,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            if http_fix:
                return http_fix, "; ".join(debug_parts + ["deepseek_http_fallback:ok"])
            return None, "; ".join(debug_parts + ["deepseek_http_fallback:err"])
        return None, "; ".join(debug_parts)

    parsed = _parse_json_response(content)
    if parsed is None:
        preview = content[:120].replace("\n", " ")
        return None, "; ".join(debug_parts + [f"json_parse:err:{preview}"])

    return parsed, "; ".join(debug_parts + ["json_parse:ok"])


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
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        base_url = _normalize_deepseek_base_url(os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
        return LLMConfig(model=model, api_key=api_key, base_url=base_url)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    return LLMConfig(model=model, api_key=api_key)


def suggest_fix_from_log(log_text: str, repo_root: str | Path | None = None) -> dict[str, Any] | None:
    suggestion, _meta = suggest_fix_from_log_with_meta(log_text, repo_root=repo_root)
    return suggestion
