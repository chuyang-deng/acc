"""Generic URL plugin — catches any http/https URL."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from acc.links.base import LinkPlugin


class GenericURLPlugin(LinkPlugin):
    """Catch-all detector for any http/https URL."""

    def __init__(self) -> None:
        super().__init__(
            name="url",
            icon="🌐",
            pattern=r"https?://[^\s\"')\]>|│]+",
            label_fn=self._label,
        )

    @staticmethod
    def _label(match: re.Match) -> str:
        url = match.group(0).rstrip(".,;:!?")
        try:
            parsed = urlparse(url)
            host = parsed.hostname or url
            # Strip www. prefix
            if host.startswith("www."):
                host = host[4:]
            path = parsed.path.rstrip("/")
            if path and path != "/":
                # Show host + first meaningful path segment
                parts = [p for p in path.split("/") if p]
                if parts:
                    return f"{host}/{'…' if len(parts) > 1 else ''}{parts[-1]}"
            return host
        except Exception:
            return url
