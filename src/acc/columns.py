"""Column plugin system — each table column is a registered ColumnDef."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from acc.config import ACCConfig
    from acc.discovery import Session


@dataclass
class ColumnDef:
    """Defines a single column in the session table."""

    key: str  # unique identifier
    header: str  # display header
    width: int  # character width (0 = auto)
    extract: Callable[[Session, int], str]  # (session, row_index) -> cell text


class ColumnRegistry:
    """Registry of column plugins. Controls which columns appear and in what order."""

    def __init__(self) -> None:
        self._columns: list[ColumnDef] = []

    def register(self, column: ColumnDef) -> None:
        """Register a column plugin."""
        # Replace if key already exists
        self._columns = [c for c in self._columns if c.key != column.key]
        self._columns.append(column)

    def unregister(self, key: str) -> None:
        """Remove a column by key."""
        self._columns = [c for c in self._columns if c.key != key]

    @property
    def columns(self) -> list[ColumnDef]:
        """Get all registered columns in order."""
        return list(self._columns)


# ── Built-in column extractors ──────────────────────────────────


def _extract_index(session: Session, idx: int) -> str:
    return str(idx + 1)


def _extract_status(session: Session, idx: int) -> str:
    return f"{session.status.icon} {session.status.label}"


def _extract_agent(session: Session, idx: int) -> str:
    return session.agent_name or "—"


def _extract_goal(session: Session, idx: int) -> str:
    return (session.goal or "—")[:60]


def _extract_progress(session: Session, idx: int) -> str:
    return (session.progress or "—")[:40]


def _extract_links(session: Session, idx: int) -> str:
    if session.links:
        return ", ".join(f"{ln.icon}{ln.label}" for ln in session.links[:3])
    return "—"


def create_default_registry(config: ACCConfig | None = None) -> ColumnRegistry:
    """Create a ColumnRegistry, potentially customized by config."""
    registry = ColumnRegistry()

    # Map of all available extractors
    extractors = {
        "#": _extract_index,
        "status": _extract_status,
        "agent": _extract_agent,
        "goal": _extract_goal,
        "progress": _extract_progress,
        "links": _extract_links,
    }

    # Default defaults if no config provided
    defaults = [
        {"key": "#", "header": "#", "width": 3},
        {"key": "status", "header": "Status", "width": 12},
        {"key": "agent", "header": "Agent", "width": 10},
        {"key": "goal", "header": "Goal", "width": 0},
        {"key": "progress", "header": "Progress", "width": 20},
        {"key": "links", "header": "Links", "width": 0},
    ]

    # Use config columns if available, otherwise defaults
    column_configs = defaults
    if config and config.columns:
        column_configs = config.columns

    for col_cfg in column_configs:
        key = col_cfg.get("key")
        if not key or key not in extractors:
            continue

        # Skip if explicitly hidden
        if not col_cfg.get("visible", True):
            continue

        registry.register(
            ColumnDef(
                key=key,
                header=col_cfg.get("header", key.capitalize()),
                width=col_cfg.get("width", 0),
                extract=extractors[key],
            )
        )

    return registry
