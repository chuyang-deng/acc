"""Configuration loading — YAML config file + environment variable overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "ccc" / "config.yaml"


@dataclass
class CCCConfig:
    """Application configuration."""

    claude_path: str = "claude"
    tmux_session: str = "ccc"
    refresh_interval: int = 3
    summary_interval: int = 60
    summary_model: str = "haiku"
    default_claude_args: list[str] = field(default_factory=list)
    recent_dirs: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    agents: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: Path | None = None) -> CCCConfig:
        """Load config from YAML file, then overlay environment variables."""
        path = config_path or DEFAULT_CONFIG_PATH
        data: dict = {}

        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f) or {}

        config = cls(
            claude_path=data.get("claude_path", cls.claude_path),
            tmux_session=data.get("tmux_session", cls.tmux_session),
            refresh_interval=data.get("refresh_interval", cls.refresh_interval),
            summary_interval=data.get("summary_interval", cls.summary_interval),
            summary_model=data.get("summary_model", cls.summary_model),
            default_claude_args=data.get("default_claude_args", []),
            recent_dirs=data.get("recent_dirs", []),
            links=data.get("links", []),
            agents=data.get("agents", []),
        )

        # Environment variables override config file values
        if env_claude := os.environ.get("CLAUDE_PATH"):
            config.claude_path = env_claude
        if env_session := os.environ.get("CCC_TMUX_SESSION"):
            config.tmux_session = env_session
        if env_refresh := os.environ.get("CCC_REFRESH_INTERVAL"):
            config.refresh_interval = int(env_refresh)
        if env_summary := os.environ.get("CCC_SUMMARY_INTERVAL"):
            config.summary_interval = int(env_summary)
        if env_model := os.environ.get("CCC_MODEL"):
            config.summary_model = env_model

        return config
