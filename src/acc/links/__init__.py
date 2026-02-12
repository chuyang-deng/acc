"""Link plugin system — detect URLs and references in pane output."""

from __future__ import annotations

from acc.links.base import DetectedLink, LinkPlugin
from acc.links.github import GitHubIssuePlugin, GitHubPRPlugin, GitHubRepoPlugin
from acc.links.linear import LinearPlugin
from acc.links.localhost import LocalhostPlugin
from acc.links.generic import GenericURLPlugin
from acc.links.custom import load_custom_plugins


class LinkRegistry:
    """Aggregates all built-in and custom link plugins."""

    def __init__(self, custom_link_configs: list[dict] | None = None) -> None:
        self.plugins: list[LinkPlugin] = [
            GitHubPRPlugin(),
            GitHubIssuePlugin(),
            GitHubRepoPlugin(),
            LinearPlugin(),
            LocalhostPlugin(),
        ]
        # Custom plugins go before the generic catch-all
        if custom_link_configs:
            self.plugins.extend(load_custom_plugins(custom_link_configs))
        # Generic URL catch-all must be last
        self.plugins.append(GenericURLPlugin())

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
