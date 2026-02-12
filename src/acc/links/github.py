"""GitHub link plugins — PR and Issue detection."""

from __future__ import annotations

import re

from acc.links.base import LinkPlugin


class GitHubPRPlugin(LinkPlugin):
    """Detect GitHub pull request URLs."""

    def __init__(self) -> None:
        super().__init__(
            name="github-pr",
            icon="🔗",
            pattern=r"https://github\.com/[^\s]+/pull/(\d+)",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        return f"PR #{match.group(1)}"


class GitHubIssuePlugin(LinkPlugin):
    """Detect GitHub issue URLs."""

    def __init__(self) -> None:
        super().__init__(
            name="github-issue",
            icon="🔗",
            pattern=r"https://github\.com/[^\s]+/issues/(\d+)",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        return f"Issue #{match.group(1)}"


class GitHubRepoPlugin(LinkPlugin):
    """Detect any GitHub URL (repos, pages, etc.)."""

    def __init__(self) -> None:
        super().__init__(
            name="github",
            icon="🔗",
            pattern=r"https://github\.com/[^\s\"')\]>]+",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        url = match.group(0)
        # Extract meaningful path: github.com/owner/repo/...
        path = url.replace("https://github.com/", "").rstrip("/")
        if path:
            parts = path.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
            return parts[0]
        return "GitHub"

