"""Session table widget — main list of tracked sessions."""

from __future__ import annotations

from textual.widgets import DataTable
from textual.message import Message

from acc.columns import ColumnRegistry, create_default_registry
from acc.discovery import Session
from acc.status import SessionStatus


class SessionSelected(Message):
    """Emitted when a session row is highlighted."""

    def __init__(self, session: Session | None) -> None:
        super().__init__()
        self.session = session


class SessionTable(DataTable):
    """DataTable showing all tracked sessions, driven by a ColumnRegistry."""

    DEFAULT_CSS = """
    SessionTable {
        height: 1fr;
        min-height: 8;
        margin: 0 1;
    }

    SessionTable > .datatable--cursor {
        background: $secondary-darken-1;
    }
    """

    def __init__(self, registry: ColumnRegistry | None = None, **kwargs) -> None:
        super().__init__(cursor_type="row", zebra_stripes=True, **kwargs)
        self._registry = registry or create_default_registry()
        self._session_list: list[Session] = []

    def on_mount(self) -> None:
        for col in self._registry.columns:
            if col.width > 0:
                self.add_column(col.header, key=col.key, width=col.width)
            else:
                self.add_column(col.header, key=col.key)

    def refresh_sessions(self, sessions: dict[str, Session]) -> None:
        """Update the table with the current session list."""
        self._session_list = list(sessions.values())
        prev_cursor = self.cursor_row
        self.clear()

        for idx, session in enumerate(self._session_list):
            cells = [col.extract(session, idx) for col in self._registry.columns]
            self.add_row(*cells)

        # Restore cursor position
        if self._session_list and prev_cursor < len(self._session_list):
            self.move_cursor(row=prev_cursor)
        elif self._session_list:
            self.move_cursor(row=0)

    def get_selected_session(self) -> Session | None:
        """Get the currently highlighted session."""
        if not self._session_list:
            return None
        row = self.cursor_row
        if 0 <= row < len(self._session_list):
            return self._session_list[row]
        return None

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Forward the selection to the app."""
        session = self.get_selected_session()
        self.post_message(SessionSelected(session))
