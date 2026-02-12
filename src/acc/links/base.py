"""Base class and types for link plugins."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class DetectedLink:
    """A link found in pane output."""

    plugin_name: str
    icon: str
    url: str
    label: str


class LinkPlugin:
    """Base class for link detection plugins."""

    def __init__(
        self,
        name: str,
        icon: str,
        pattern: str,
        label_fn: Callable[[re.Match], str] | None = None,
        label: str | None = None,
    ) -> None:
        self.name = name
        self.icon = icon
        self._pattern = re.compile(pattern)
        self._label_fn = label_fn
        self._static_label = label

    def find_links(self, text: str) -> list[DetectedLink]:
        """Find all matching links in the given text."""
        results: list[DetectedLink] = []
        seen: set[str] = set()
        for match in self._pattern.finditer(text):
            url = match.group(0)
            if url in seen:
                continue
            seen.add(url)

            if self._label_fn:
                label = self._label_fn(match)
            elif self._static_label:
                label = self._static_label
            else:
                label = url

            results.append(DetectedLink(
                plugin_name=self.name,
                icon=self.icon,
                url=url,
                label=label,
            ))
        return results
