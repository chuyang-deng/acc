"""LLM summarization — use Anthropic API to summarize session content."""

from __future__ import annotations

import logging
import time
import subprocess
import platform
import urllib.request
from dataclasses import dataclass
from pathlib import Path

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
    """Summarizes pane content using LLM providers (Anthropic, OpenAI/Ollama, Apple)."""

    def __init__(
        self,
        model: str = "claude-haiku-4-20250414",
        interval: int = 60,
        api_key: str | None = None,
        base_url: str | None = None,
        provider: str = "anthropic",
    ) -> None:
        self.model = model
        self.interval = interval
        self.api_key = api_key
        self.base_url = base_url
        self.provider = provider.lower()
        self._cache: dict[str, SessionSummary] = {}
        self._client = None

    def _resolve_auto_provider(self) -> str:
        """Detect the best available LLM provider."""
        # 1. Check for Apple Intelligence (macOS 15+ / Darwin 24+ ?) 
        # Requirement was "macOS 26+". Assuming this meant Darwin 26 (macOS 17) or year 2026.
        # Let's check Darwin version via platform.release()
        if platform.system() == "Darwin":
            try:
                # platform.release() returns e.g. "24.0.0" for macOS 15
                release = platform.release()
                major = int(release.split(".")[0])
                major = int(release.split(".")[0])
                if major >= 24:
                    script_path = Path(__file__).parent / "scripts" / "afm_wrapper.swift"
                    if script_path.exists():
                        # Validate if the script actually runs (checks imports)
                        try:
                            res = subprocess.run(
                                ["swift", str(script_path), "--check"],
                                capture_output=True,
                                timeout=5
                            )
                            if res.returncode == 0:
                                logger.info("Auto-detected Apple Intelligence (Darwin %s)", release)
                                return "apple"
                        except Exception:
                            pass
            except Exception:
                pass


        # 2. Check for Ollama (localhost:11434)
        try:
            with urllib.request.urlopen("http://localhost:11434/", timeout=0.5):
                logger.info("Auto-detected Ollama running locally")
                return "ollama"
        except Exception:
            pass

        # 3. Check API keys for remote providers
        if self.api_key:
            if self.api_key.startswith("sk-ant-"):
                return "anthropic"
            if self.api_key.startswith("sk-"):
                return "openai"

        # Default fallback
        return "anthropic"

    def _get_client(self):
        """Lazy-init the LLM client based on provider."""
        if self._client is not None:
            return self._client
        
        if self.provider == "auto":
            self.provider = self._resolve_auto_provider()

        try:
            if self.provider == "anthropic":
                import anthropic

                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            elif self.provider in ("openai", "ollama"):
                import openai

                # Default base_url for Ollama if not specified
                base_url = self.base_url
                if self.provider == "ollama" and not base_url:
                    base_url = "http://localhost:11434/v1"

                self._client = openai.OpenAI(
                    api_key=self.api_key or "ollama",  # Ollama doesn't need a real key
                    base_url=base_url,
                )
            elif self.provider == "apple":
                # Apple Intelligence via swift wrapper uses subprocess, no client obj needed
                self._client = "apple"

        except Exception as e:
            logger.warning("Failed to initialize %s client: %s", self.provider, e)
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
        """Summarize pane content using the configured LLM provider."""
        if not force and not self.should_refresh(pane_id):
            return self._cache.get(pane_id)

        client = self._get_client()
        if client is None:
            return self._cache.get(pane_id)

        try:
            prompt = _SUMMARIZE_PROMPT.format(content=content[-3000:])
            text = ""

            if self.provider == "anthropic":
                response = client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.content[0].text

            elif self.provider in ("openai", "ollama"):
                response = client.chat.completions.create(
                    model=self.model,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = response.choices[0].message.content

            elif self.provider == "apple":
                # Use our bundled swift wrapper script
                # Locate the swift script relative to this file
                # src/acc/summarizer.py -> src/acc/scripts/afm_wrapper.swift
                script_path = Path(__file__).parent / "scripts" / "afm_wrapper.swift"
                
                if not script_path.exists():
                     logger.warning("afm_wrapper.swift not found at %s", script_path)
                     return self._cache.get(pane_id)

                # Run swift script: swift src/acc/scripts/afm_wrapper.swift "prompt"
                cmd = ["swift", str(script_path), prompt]
                
                # Timeout increased since local inference can be slow
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    logger.warning("Apple Intelligence failed: %s", result.stderr)
                    return self._cache.get(pane_id)
                text = result.stdout

            summary = self._parse_response(text)
            summary.timestamp = time.time()
            self._cache[pane_id] = summary
            return summary

        except Exception as e:
            logger.warning("Summarization failed for %s (%s): %s", pane_id, self.provider, e)
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
