"""GitHub link plugins — PR and Issue detection."""

from __future__ import annotations

import re

from ccc.links.base import LinkPlugin


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
