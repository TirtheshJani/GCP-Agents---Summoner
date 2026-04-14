"""Tests for configuration loading."""

from __future__ import annotations

import textwrap

from config import Settings, load_config, _resolve_env_vars


class TestResolveEnvVars:
    def test_simple_substitution(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "hello")
        assert _resolve_env_vars("${MY_VAR}") == "hello"

    def test_default_value(self):
        result = _resolve_env_vars("${NONEXISTENT_VAR_12345:fallback}")
        assert result == "fallback"

    def test_missing_without_default(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_VAR_12345", raising=False)
        assert _resolve_env_vars("${NONEXISTENT_VAR_12345}") == ""

    def test_nested_dict(self, monkeypatch):
        monkeypatch.setenv("X", "val")
        data = {"outer": {"inner": "${X}"}}
        assert _resolve_env_vars(data) == {"outer": {"inner": "val"}}

    def test_list(self, monkeypatch):
        monkeypatch.setenv("Y", "item")
        data = ["${Y}", "literal"]
        assert _resolve_env_vars(data) == ["item", "literal"]

    def test_non_string_passthrough(self):
        assert _resolve_env_vars(42) == 42
        assert _resolve_env_vars(None) is None


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.gcp.region == "us-central1"
        assert s.vertex_ai.model_name == "gemini-1.5-flash"
        assert s.agent.max_retries == 3

    def test_override(self):
        s = Settings(agent={"max_retries": 5, "timeout_seconds": 60})
        assert s.agent.max_retries == 5
        assert s.agent.timeout_seconds == 60


class TestLoadConfig:
    def test_load_from_default_path(self):
        settings = load_config()
        assert isinstance(settings, Settings)
        assert settings.vertex_ai.model_name == "gemini-1.5-flash"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        settings = load_config(tmp_path / "does_not_exist.yaml")
        assert isinstance(settings, Settings)
        assert settings.gcp.region == "us-central1"

    def test_load_custom_file(self, tmp_path):
        cfg_file = tmp_path / "test_config.yaml"
        cfg_file.write_text(
            textwrap.dedent("""\
                gcp:
                  project_id: "test-project"
                  region: "europe-west1"
                vertex_ai:
                  model_name: "gemini-1.5-pro"
                  temperature: 0.3
            """)
        )
        settings = load_config(cfg_file)
        assert settings.gcp.project_id == "test-project"
        assert settings.gcp.region == "europe-west1"
        assert settings.vertex_ai.model_name == "gemini-1.5-pro"
        assert settings.vertex_ai.temperature == 0.3
