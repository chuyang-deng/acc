"""Linear ticket link plugin."""

from __future__ import annotations

import re

from ccc.links.base import LinkPlugin


class LinearPlugin(LinkPlugin):
    """Detect Linear-style ticket identifiers (e.g. ENG-123)."""

    def __init__(self) -> None:
        super().__init__(
            name="linear",
            icon="🎫",
            pattern=r"\b([A-Z]+-\d+)\b",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        return match.group(1)
