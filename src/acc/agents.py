"""Agent detector registry — pluggable system for identifying coding agents and their states."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


class AgentDetector(Protocol):
    """Protocol for agent-specific detection logic."""

    @property
    def name(self) -> str:
        """Human-readable agent name (e.g. 'Claude', 'OpenCode')."""
        ...

    @property
    def process_names(self) -> list[str]:
        """Process names / binary names to match in the process tree."""
        ...

    @property
    def attention_patterns(self) -> list[re.Pattern]:
        """Regex patterns that indicate the agent needs user input."""
        ...

    @property
    def working_patterns(self) -> list[re.Pattern]:
        """Regex patterns that indicate the agent is actively working."""
        ...


# ──────────────────────────────────────────────────────────────────
# Built-in agent detectors
# ──────────────────────────────────────────────────────────────────


class ClaudeDetector:
    """Detector for Claude Code CLI sessions."""

    name = "Claude"
    process_names = ["claude"]

    attention_patterns = [
        re.compile(r"\?\s*$", re.MULTILINE),
        re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
        re.compile(r"\(Y\)es.*\(N\)o", re.IGNORECASE),
        re.compile(r"^[❯>›]\s*$", re.MULTILINE),
        re.compile(r"Do you want to proceed", re.IGNORECASE),
    ]

    working_patterns = [
        re.compile(r"⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏"),
        re.compile(r"\.{3,}"),
        re.compile(r"█|▓|▒|░"),
    ]


class OpenCodeDetector:
    """Detector for OpenCode sessions."""

    name = "OpenCode"
    process_names = ["opencode"]

    attention_patterns = [
        re.compile(r"\?\s*$", re.MULTILINE),
        re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
        re.compile(r"^[❯>›\$]\s*$", re.MULTILINE),
        re.compile(r"Enter.*to continue", re.IGNORECASE),
        re.compile(r"waiting for input", re.IGNORECASE),
    ]

    working_patterns = [
        re.compile(r"⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏"),
        re.compile(r"thinking|generating|processing", re.IGNORECASE),
        re.compile(r"█|▓|▒|░"),
    ]


class CodexDetector:
    """Detector for OpenAI Codex CLI sessions."""

    name = "Codex"
    process_names = ["codex"]

    attention_patterns = [
        re.compile(r"\?\s*$", re.MULTILINE),
        re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
        re.compile(r"^[❯>›\$]\s*$", re.MULTILINE),
        re.compile(r"approve|reject|deny", re.IGNORECASE),
    ]

    working_patterns = [
        re.compile(r"⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏"),
        re.compile(r"running|executing|reading", re.IGNORECASE),
        re.compile(r"█|▓|▒|░"),
    ]


class AiderDetector:
    """Detector for Aider sessions."""

    name = "Aider"
    process_names = ["aider"]

    attention_patterns = [
        re.compile(r"\?\s*$", re.MULTILINE),
        re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
        re.compile(r"^[❯>›\$]\s*$", re.MULTILINE),
        re.compile(r"^aider>", re.MULTILINE),
    ]

    working_patterns = [
        re.compile(r"⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏"),
        re.compile(r"Tokens:|Model:", re.IGNORECASE),
    ]


class GeminiDetector:
    """Detector for Gemini CLI and Antigravity CLI sessions."""

    name = "Gemini"
    process_names = ["gemini", "antigravity"]

    attention_patterns = [
        re.compile(r"\?\s*$", re.MULTILINE),
        re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
        re.compile(r"^[❯>›\$]\s*$", re.MULTILINE),
        re.compile(r"Do you want to proceed", re.IGNORECASE),
        re.compile(r"waiting for approval", re.IGNORECASE),
    ]

    working_patterns = [
        re.compile(r"⠋|⠙|⠹|⠸|⠼|⠴|⠦|⠧|⠇|⠏"),
        re.compile(r"\.{3,}"),
        re.compile(r"█|▓|▒|░"),
        re.compile(r"Generating|Thinking|Planning", re.IGNORECASE),
    ]


# ──────────────────────────────────────────────────────────────────
# Custom detector from config
# ──────────────────────────────────────────────────────────────────


@dataclass
class CustomAgentDetector:
    """Agent detector built from user config."""

    name: str = "Custom"
    process_names: list[str] = field(default_factory=list)
    attention_patterns: list[re.Pattern] = field(default_factory=list)
    working_patterns: list[re.Pattern] = field(default_factory=list)

    @classmethod
    def from_config(cls, cfg: dict) -> CustomAgentDetector:
        return cls(
            name=cfg.get("name", "Custom"),
            process_names=cfg.get("process_names", []),
            attention_patterns=[
                re.compile(p) for p in cfg.get("attention_patterns", [])
            ],
            working_patterns=[
                re.compile(p) for p in cfg.get("working_patterns", [])
            ],
        )


# ──────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────

# Default set of built-in detectors
BUILTIN_DETECTORS: list[AgentDetector] = [
    ClaudeDetector(),
    OpenCodeDetector(),
    CodexDetector(),
    AiderDetector(),
    GeminiDetector(),
]


class AgentRegistry:
    """Registry of all known agent detectors."""

    def __init__(self, custom_configs: list[dict] | None = None) -> None:
        self.detectors: list[AgentDetector] = list(BUILTIN_DETECTORS)
        if custom_configs:
            for cfg in custom_configs:
                self.detectors.append(CustomAgentDetector.from_config(cfg))

    def all_process_names(self) -> list[str]:
        """Get all process names across all detectors."""
        names = []
        for d in self.detectors:
            names.extend(d.process_names)
        return names

    def find_detector(self, process_name: str) -> AgentDetector | None:
        """Find the detector that matches a given process name."""
        process_name_lower = process_name.lower()
        for d in self.detectors:
            if any(n.lower() in process_name_lower for n in d.process_names):
                return d
        return None

    def get_detector_by_name(self, name: str) -> AgentDetector | None:
        """Get a detector by its agent name."""
        for d in self.detectors:
            if d.name.lower() == name.lower():
                return d
        return None
