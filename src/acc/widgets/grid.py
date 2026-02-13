"""Grid layout widgets for Agent Command Center."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static

from acc.discovery import Session as TrackedSession


class SessionCard(Static):
    """A card representing a single agent session."""

    DEFAULT_CSS = """
    SessionCard {
        width: 100%;
        height: auto;
        border: solid $secondary;
        padding: 0 1;
        margin: 1;
        background: $surface;
    }

    SessionCard:focus {
        border: double $accent;
    }

    SessionCard .header {
        dock: top;
        height: 1;
        text-style: bold;
        color: $accent;
    }

    SessionCard .goal {
        color: $text;
        height: auto;
    }

    SessionCard .progress {
        color: $text-muted;
        height: auto;
    }

    SessionCard .status-icon {
        width: 2;
    }
    """

    def __init__(self, session: TrackedSession) -> None:
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        icon = self.session.status.icon
        name = self.session.display_name
        yield Label(f"{icon} {name}", classes="header")
        
        goal = self.session.goal or "No goal detected"
        yield Label(f"Goal: {goal}", classes="goal")
        
        progress = self.session.progress or "No progress detected"
        yield Label(f"Progress: {progress}", classes="progress")

    def update_session(self, session: TrackedSession) -> None:
        """Update the card with new session data."""
        self.session = session
        # Re-compose or specific updates?
        # For simplicity, just update the labels if possible.
        # But we yielded Labels.
        # Querying them is better.
        try:
            self.query_one(".header", Label).update(f"{session.status.icon} {session.display_name}")
            self.query_one(".goal", Label).update(f"Goal: {session.goal or 'No goal detected'}")
            self.query_one(".progress", Label).update(f"Progress: {session.progress or 'No progress detected'}")
        except Exception:
            pass


class SessionGrid(Vertical):
    """A grid view of session cards."""

    DEFAULT_CSS = """
    SessionGrid {
        height: 1fr;
        width: 1fr;
        overflow-y: scroll;
    }

    SessionGrid > Grid {
        grid-size: 3;
        grid-gutter: 1;
        padding: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cards: dict[str, SessionCard] = {}

    def compose(self) -> ComposeResult:
        yield Grid(id="card-grid")

    def refresh_sessions(self, sessions: dict[str, TrackedSession]) -> None:
        """Update the grid with the latest sessions."""
        grid = self.query_one("#card-grid", Grid)
        
        # Remove stale cards
        for pane_id in list(self.cards.keys()):
            if pane_id not in sessions:
                self.cards[pane_id].remove()
                del self.cards[pane_id]

        # Add/Update cards
        for pane_id, session in sessions.items():
            if pane_id in self.cards:
                self.cards[pane_id].update_session(session)
            else:
                card = SessionCard(session)
                self.cards[pane_id] = card
                grid.mount(card)
