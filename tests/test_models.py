from offerpilot.crew import missing_api_key


def test_gemini_needs_a_google_key(monkeypatch):
    monkeypatch.setenv("OFFERPILOT_MODEL", "gemini/gemini-flash-latest")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert missing_api_key() == "GEMINI_API_KEY"
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    assert missing_api_key() is None


def test_ollama_needs_no_key(monkeypatch):
    monkeypatch.setenv("OFFERPILOT_MODEL", "ollama/qwen3:8b")
    assert missing_api_key() is None


def test_default_is_anthropic(monkeypatch):
    monkeypatch.delenv("OFFERPILOT_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert missing_api_key() == "ANTHROPIC_API_KEY"
