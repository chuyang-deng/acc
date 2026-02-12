"""LLM summarization — use Anthropic API to summarize session content."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_SUMMARIZE_PROMPT = """\
You are summarizing a terminal session running Claude Code (an AI coding assistant).
Given the terminal output below, extract:
1. **Goal**: The original task or goal (one short line)
2. **Progress**: Current progress or state (one short line)
3. **Needs user**: Is Claude waiting for user input? (yes/no)

Respond in exactly this format:
Goal: <goal>
Progress: <progress>
Needs user: <yes or no>

Terminal output:
{content}
"""


@dataclass
class SessionSummary:
    """Summarized session information."""

    goal: str
    progress: str
    needs_user: bool
    timestamp: float


class Summarizer:
    """Summarizes pane content using the Anthropic API."""

    def __init__(self, model: str = "claude-haiku-4-20250414", interval: int = 60) -> None:
        self.model = model
        self.interval = interval
        self._cache: dict[str, SessionSummary] = {}
        self._client = None

    def _get_client(self):
        """Lazy-init the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client: %s", e)
                return None
        return self._client

    def should_refresh(self, pane_id: str) -> bool:
        """Check if a summary needs refreshing based on the interval."""
        cached = self._cache.get(pane_id)
        if cached is None:
            return True
        return (time.time() - cached.timestamp) >= self.interval

    def get_cached(self, pane_id: str) -> SessionSummary | None:
        """Get the cached summary for a pane, if available."""
        return self._cache.get(pane_id)

    def summarize(self, pane_id: str, content: str, force: bool = False) -> SessionSummary | None:
        """Summarize pane content using the LLM.

        Returns cached summary if within interval, unless force=True.
        Returns None if summarization fails.
        """
        if not force and not self.should_refresh(pane_id):
            return self._cache.get(pane_id)

        client = self._get_client()
        if client is None:
            return self._cache.get(pane_id)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": _SUMMARIZE_PROMPT.format(content=content[-3000:]),
                }],
            )

            text = response.content[0].text
            summary = self._parse_response(text)
            summary.timestamp = time.time()
            self._cache[pane_id] = summary
            return summary

        except Exception as e:
            logger.warning("Summarization failed for %s: %s", pane_id, e)
            return self._cache.get(pane_id)

    def invalidate(self, pane_id: str) -> None:
        """Remove cached summary for a pane."""
        self._cache.pop(pane_id, None)

    @staticmethod
    def _parse_response(text: str) -> SessionSummary:
        """Parse the structured LLM response into a SessionSummary."""
        goal = ""
        progress = ""
        needs_user = False

        for line in text.strip().splitlines():
            line = line.strip()
            if line.lower().startswith("goal:"):
                goal = line.split(":", 1)[1].strip()
            elif line.lower().startswith("progress:"):
                progress = line.split(":", 1)[1].strip()
            elif line.lower().startswith("needs user:"):
                val = line.split(":", 1)[1].strip().lower()
                needs_user = val in ("yes", "true", "y")

        return SessionSummary(
            goal=goal or "Unknown",
            progress=progress or "Unknown",
            needs_user=needs_user,
            timestamp=0,
        )
