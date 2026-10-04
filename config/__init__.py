"""Configuration loader for GCP Agents - Summoner."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

_ENV_VAR_PATTERN = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<default>[^}]*))?\}"
)


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${VAR:default} placeholders in config values."""
    if isinstance(value, str):

        def _replacer(match: re.Match) -> str:
            name = match.group("name")
            default = match.group("default") or ""
            return os.environ.get(name, default)

        return _ENV_VAR_PATTERN.sub(_replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


class VertexAIConfig(BaseModel):
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.95


class AgentDefaults(BaseModel):
    max_retries: int = 3
    timeout_seconds: int = 120
    memory_backend: str = "in_memory"
    log_level: str = "INFO"


class GCPConfig(BaseModel):
    project_id: str = ""
    region: str = "us-central1"
    credentials_path: str = ""


class StorageConfig(BaseModel):
    bucket: str = ""
    output_prefix: str = "agent-outputs/"


class PubSubConfig(BaseModel):
    task_topic: str = "agent-tasks"
    result_topic: str = "agent-results"


class FirestoreConfig(BaseModel):
    collection: str = "agent_memory"


class LoggingConfig(BaseModel):
    structured: bool = True
    level: str = "INFO"
    cloud_logging: bool = True


class Settings(BaseSettings):
    """Application settings loaded from YAML + environment variables."""

    gcp: GCPConfig = Field(default_factory=GCPConfig)
    vertex_ai: VertexAIConfig = Field(default_factory=VertexAIConfig)
    agent: AgentDefaults = Field(default_factory=AgentDefaults)
    firestore: FirestoreConfig = Field(default_factory=FirestoreConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    pubsub: PubSubConfig = Field(default_factory=PubSubConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: str | Path | None = None) -> Settings:
    """Load configuration from YAML file with environment variable resolution.

    Args:
        config_path: Path to the YAML config file. Defaults to
            ``config/agent_config.yaml`` relative to the project root.

    Returns:
        Populated Settings instance.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "agent_config.yaml"
    else:
        config_path = Path(config_path)

    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}
        resolved = _resolve_env_vars(raw)
        # Remove non-settings keys
        resolved.pop("project", None)
        return Settings(**resolved)

    return Settings()
