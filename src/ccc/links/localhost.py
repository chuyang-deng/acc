"""Localhost dev server link plugin."""

from __future__ import annotations

import re

from ccc.links.base import LinkPlugin


class LocalhostPlugin(LinkPlugin):
    """Detect localhost URLs with port numbers (e.g. http://localhost:5173)."""

    def __init__(self) -> None:
        super().__init__(
            name="localhost",
            icon="🌐",
            pattern=r"https?://localhost:\d+[^\s]*",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        url = match.group(0)
        # Extract just the host:port part
        parts = url.split("//", 1)
        if len(parts) > 1:
            host_port = parts[1].split("/")[0]
            return host_port
        return url
