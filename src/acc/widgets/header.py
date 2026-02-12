"""Header widget — title, session count, and notification badge."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static


class ACCHeader(Widget):
    """Top header bar with title, session count, and attention badge."""

    DEFAULT_CSS = """
    ACCHeader {
        dock: top;
        height: 3;
        background: $primary-darken-3;
        color: $text;
        padding: 0 2;
    }

    ACCHeader .header-title {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
        color: #bb86fc;
        padding: 1 0;
    }

    ACCHeader .header-info {
        width: auto;
        content-align: right middle;
        padding: 1 0;
        color: $text-muted;
    }

    ACCHeader .header-badge {
        width: auto;
        content-align: right middle;
        padding: 1 2;
        color: #ff5555;
        text-style: bold;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._session_count = 0
        self._badge_count = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("⚡ Agent Command Center", classes="header-title")
            yield Static("0 sessions", id="session-count", classes="header-info")
            yield Static("", id="badge", classes="header-badge")

    def update_counts(self, session_count: int, badge_count: int) -> None:
        """Update the session count and badge display."""
        self._session_count = session_count
        self._badge_count = badge_count

        count_widget = self.query_one("#session-count", Static)
        count_widget.update(f"{session_count} session{'s' if session_count != 1 else ''}")

        badge_widget = self.query_one("#badge", Static)
        if badge_count > 0:
            badge_widget.update(f"🔔{badge_count}")
        else:
            badge_widget.update("")
