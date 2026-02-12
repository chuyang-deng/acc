"""Column plugin system — each table column is a registered ColumnDef."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ccc.discovery import Session


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


def create_default_registry() -> ColumnRegistry:
    """Create a ColumnRegistry with all built-in columns."""
    registry = ColumnRegistry()
    registry.register(ColumnDef(key="#", header="#", width=3, extract=_extract_index))
    registry.register(ColumnDef(key="status", header="Status", width=12, extract=_extract_status))
    registry.register(ColumnDef(key="agent", header="Agent", width=10, extract=_extract_agent))
    registry.register(ColumnDef(key="goal", header="Goal", width=0, extract=_extract_goal))
    registry.register(ColumnDef(key="progress", header="Progress", width=20, extract=_extract_progress))
    registry.register(ColumnDef(key="links", header="Links", width=0, extract=_extract_links))
    return registry
