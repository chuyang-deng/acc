"""Custom user-defined link plugins loaded from config."""

from __future__ import annotations

from acc.links.base import LinkPlugin


def load_custom_plugins(link_configs: list[dict]) -> list[LinkPlugin]:
    """Create LinkPlugin instances from user config definitions.

    Each config dict should have: name, icon, pattern, label.
    """
    plugins: list[LinkPlugin] = []
    for cfg in link_configs:
        name = cfg.get("name", "custom")
        icon = cfg.get("icon", "🔗")
        pattern = cfg.get("pattern", "")
        label = cfg.get("label", "Link")

        if not pattern:
            continue

        plugins.append(LinkPlugin(
            name=name,
            icon=icon,
            pattern=pattern,
            label=label,
        ))
    return plugins
