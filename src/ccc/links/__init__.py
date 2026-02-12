"""Link plugin system — detect URLs and references in pane output."""

from __future__ import annotations

from ccc.links.base import DetectedLink, LinkPlugin
from ccc.links.github import GitHubIssuePlugin, GitHubPRPlugin, GitHubRepoPlugin
from ccc.links.linear import LinearPlugin
from ccc.links.localhost import LocalhostPlugin
from ccc.links.custom import load_custom_plugins


class LinkRegistry:
    """Aggregates all built-in and custom link plugins."""

    def __init__(self, custom_link_configs: list[dict] | None = None) -> None:
        self.plugins: list[LinkPlugin] = [
            GitHubPRPlugin(),
            GitHubIssuePlugin(),
            GitHubRepoPlugin(),  # generic fallback for any github URL
            LinearPlugin(),
            LocalhostPlugin(),
        ]
        if custom_link_configs:
            self.plugins.extend(load_custom_plugins(custom_link_configs))

    def scan(self, text: str) -> list[DetectedLink]:
        """Scan text for all matching links across all plugins."""
        results: list[DetectedLink] = []
        seen_urls: set[str] = set()
        for plugin in self.plugins:
            for link in plugin.find_links(text):
                if link.url not in seen_urls:
                    seen_urls.add(link.url)
                    results.append(link)
        return results


__all__ = [
    "DetectedLink",
    "LinkPlugin",
    "LinkRegistry",
]
