"""Column plugin system — each table column is a ColumnDef."""

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


# ── Built-in columns ────────────────────────────────────────────


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


# Default column layout
DEFAULT_COLUMNS: list[ColumnDef] = [
    ColumnDef(key="#", header="#", width=3, extract=_extract_index),
    ColumnDef(key="status", header="Status", width=12, extract=_extract_status),
    ColumnDef(key="agent", header="Agent", width=10, extract=_extract_agent),
    ColumnDef(key="goal", header="Goal", width=0, extract=_extract_goal),  # 0 = auto
    ColumnDef(key="progress", header="Progress", width=20, extract=_extract_progress),
    ColumnDef(key="links", header="Links", width=0, extract=_extract_links),  # 0 = auto
]
