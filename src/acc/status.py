"""Status detection — determine session state from pane content and process info."""

from __future__ import annotations

import time
from enum import Enum

from acc.agents import AgentDetector


class SessionStatus(Enum):
    """Possible states for a coding agent session."""

    WORKING = "working"
    IDLE = "idle"
    NEEDS_ATTENTION = "needs_attention"
    DONE = "done"
    CRASHED = "crashed"

    @property
    def icon(self) -> str:
        return _STATUS_ICONS[self]

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_ICONS = {
    SessionStatus.WORKING: "🟢",
    SessionStatus.IDLE: "🟡",
    SessionStatus.NEEDS_ATTENTION: "🔴",
    SessionStatus.DONE: "✅",
    SessionStatus.CRASHED: "💀",
}

_STATUS_LABELS = {
    SessionStatus.WORKING: "Working",
    SessionStatus.IDLE: "Idle",
    SessionStatus.NEEDS_ATTENTION: "Input",
    SessionStatus.DONE: "Done",
    SessionStatus.CRASHED: "Crashed",
}

IDLE_TIMEOUT_SECONDS = 30.0


def detect_status(
    pane_content: str,
    agent_running: bool,
    exit_code: int | None,
    last_output_time: float,
    detector: AgentDetector | None = None,
) -> SessionStatus:
    """Determine session status from pane content and process state.

    Args:
        pane_content: Last ~50 lines of pane output.
        agent_running: Whether the agent process is alive.
        exit_code: Process exit code, if exited.
        last_output_time: Timestamp of last detected output change.
        detector: Agent-specific detector for pattern matching.
                  Falls back to generic patterns if None.

    Returns:
        The detected SessionStatus.
    """
    # Process exited
    if not agent_running:
        if exit_code is not None and exit_code != 0:
            return SessionStatus.CRASHED
        return SessionStatus.DONE

    # Process is alive — check content for clues
    lines = pane_content.strip().splitlines()
    tail = "\n".join(lines[-10:]) if lines else ""

    # Use detector patterns if available
    attention_patterns = (
        detector.attention_patterns if detector else _DEFAULT_ATTENTION_PATTERNS
    )
    working_patterns = (
        detector.working_patterns if detector else _DEFAULT_WORKING_PATTERNS
    )

    # Check for active working indicators FIRST — a visible spinner/progress
    # means the agent is busy even if its input prompt is also visible
    # (e.g. Claude always shows ❯ prompt, even while compacting).
    for pat in working_patterns:
        if pat.search(tail):
            return SessionStatus.WORKING

    # Only check attention patterns if no working indicator was found
    for pat in attention_patterns:
        if pat.search(tail):
            return SessionStatus.NEEDS_ATTENTION

    # Check idle timeout
    elapsed = time.time() - last_output_time
    if elapsed > IDLE_TIMEOUT_SECONDS:
        return SessionStatus.IDLE

    # Default: working
    return SessionStatus.WORKING


# Fallback patterns when no detector is available
import re

_DEFAULT_ATTENTION_PATTERNS = [
    re.compile(r"\?\s*$", re.MULTILINE),
    re.compile(r"(?:Y/n|y/N|yes/no)", re.IGNORECASE),
    re.compile(r"\(Y\)es.*\(N\)o", re.IGNORECASE),
    re.compile(r"^[❯>›\$]\s*$", re.MULTILINE),
]

_DEFAULT_WORKING_PATTERNS = [
    re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]"),
    re.compile(r"\.{3,}"),
    re.compile(r"[█▓▒░]"),
]


def content_changed(old_hash: int, new_content: str) -> tuple[bool, int]:
    """Check if pane content has changed. Returns (changed, new_hash)."""
    new_hash = hash(new_content)
    return (old_hash != new_hash, new_hash)
