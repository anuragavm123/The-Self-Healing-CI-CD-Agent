from self_healing_agent.llm_client import (
    _ollama_native_chat_url,
    get_llm_runtime_info,
    load_llm_config,
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
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-coder")

    info = get_llm_runtime_info()

    assert info["provider"] == "deepseek"
    assert info["configured"] is True
    assert info["model"] == "deepseek-coder"
    assert info["base_url"] == "https://api.deepseek.com"
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
