from self_healing_agent.llm_client import (
    _normalize_deepseek_base_url,
    _parse_json_response,
    _ollama_native_chat_url,
    get_llm_runtime_info,
    load_llm_config,
    suggest_fix_from_log_with_meta,
)


def test_ollama_base_url_adds_v1_suffix(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")

    config = load_llm_config()

    assert config is not None
    assert config.base_url == "http://localhost:11434/v1"


def test_ollama_base_url_keeps_existing_v1(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    config = load_llm_config()

    assert config is not None
    assert config.base_url == "http://localhost:11434/v1"


def test_openai_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert load_llm_config() is None

    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    config = load_llm_config()

    assert config is not None
    assert config.base_url is None
    assert config.model == "gpt-4o"


def test_ollama_native_url_from_v1_base() -> None:
    assert _ollama_native_chat_url("http://127.0.0.1:11434/v1") == "http://127.0.0.1:11434/api/chat"


def test_ollama_native_url_from_root_base() -> None:
    assert _ollama_native_chat_url("http://localhost:11434/") == "http://localhost:11434/api/chat"


def test_runtime_info_reports_deepseek_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")

    info = get_llm_runtime_info()

    assert info["provider"] == "deepseek"
    assert info["configured"] is True
    assert info["model"] == "deepseek-chat"
    assert info["base_url"] == "https://api.deepseek.com/v1"
    assert info["api_key_present"] is True


def test_runtime_info_reports_unconfigured_openai(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    info = get_llm_runtime_info()

    assert info["provider"] == "openai"
    assert info["configured"] is False
    assert info["model"] is None
    assert info["base_url"] is None
    assert info["api_key_present"] is False


def test_parse_json_response_handles_markdown_fence() -> None:
    content = """```json
{"reason":"r","file_path":"src/math_utils.py","old_code":"a","new_code":"b"}
```"""
    parsed = _parse_json_response(content)

    assert parsed is not None
    assert parsed["file_path"] == "src/math_utils.py"


def test_parse_json_response_handles_plain_json_text() -> None:
    content = '{"reason":"r","file_path":"src/math_utils.py","old_code":"a","new_code":"b"}'
    parsed = _parse_json_response(content)

    assert parsed is not None
    assert parsed["new_code"] == "b"


def test_normalize_deepseek_base_url_adds_v1() -> None:
    assert _normalize_deepseek_base_url("https://api.deepseek.com") == "https://api.deepseek.com/v1"


def test_normalize_deepseek_base_url_keeps_v1() -> None:
    assert _normalize_deepseek_base_url("https://api.deepseek.com/v1") == "https://api.deepseek.com/v1"


def test_deepseek_defaults_model_and_base_url(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dummy-key")
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)

    config = load_llm_config()

    assert config is not None
    assert config.model == "deepseek-chat"
    assert config.base_url == "https://api.deepseek.com/v1"


def test_suggest_fix_meta_reports_unconfigured() -> None:
    suggestion, meta = suggest_fix_from_log_with_meta("failed log")

    assert suggestion is None
    assert isinstance(meta, str)


def test_apifreellm_provider_config_defaults(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "apifreellm")
    monkeypatch.setenv("APIFREELLM_API_KEY", "dummy-key")
    monkeypatch.delenv("APIFREELLM_MODEL", raising=False)
    monkeypatch.delenv("APIFREELLM_BASE_URL", raising=False)

    config = load_llm_config()

    assert config is not None
    assert config.model == "deepseek-chat"
    assert config.base_url == "https://apifreellm.com/api/v1"


def test_apifreellm_provider_requires_key(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "apifreellm")
    monkeypatch.delenv("APIFREELLM_API_KEY", raising=False)

    assert load_llm_config() is None
