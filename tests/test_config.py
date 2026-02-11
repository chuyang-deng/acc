"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import yaml

from ccc.config import CCCConfig


class TestCCCConfig:
    def test_defaults(self):
        config = CCCConfig()
        assert config.claude_path == "claude"
        assert config.tmux_session == "ccc"
        assert config.refresh_interval == 3
        assert config.summary_interval == 60
        assert config.summary_model == "haiku"

    def test_load_from_yaml(self, tmp_path):
        config_data = {
            "claude_path": "/usr/local/bin/claude",
            "tmux_session": "my-claude",
            "refresh_interval": 5,
            "summary_interval": 120,
            "summary_model": "sonnet",
            "links": [
                {"name": "jira", "pattern": r"JIRA-\d+", "icon": "🎫", "label": "Jira"}
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = CCCConfig.load(config_file)
        assert config.claude_path == "/usr/local/bin/claude"
        assert config.tmux_session == "my-claude"
        assert config.refresh_interval == 5
        assert config.summary_interval == 120
        assert config.summary_model == "sonnet"
        assert len(config.links) == 1

    def test_env_var_override(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"claude_path": "from-yaml"}, f)

        monkeypatch.setenv("CLAUDE_PATH", "/env/claude")
        monkeypatch.setenv("CCC_TMUX_SESSION", "env-session")
        monkeypatch.setenv("CCC_REFRESH_INTERVAL", "10")

        config = CCCConfig.load(config_file)
        assert config.claude_path == "/env/claude"
        assert config.tmux_session == "env-session"
        assert config.refresh_interval == 10

    def test_missing_file_uses_defaults(self):
        config = CCCConfig.load(Path("/nonexistent/path/config.yaml"))
        assert config.claude_path == "claude"
        assert config.tmux_session == "ccc"
