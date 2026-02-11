"""Session table widget — main list of tracked sessions."""

from __future__ import annotations

from textual.widgets import DataTable
from textual.message import Message

from ccc.discovery import Session
from ccc.status import SessionStatus


class SessionSelected(Message):
    """Emitted when a session row is highlighted."""

    def __init__(self, session: Session | None) -> None:
        super().__init__()
        self.session = session


class SessionTable(DataTable):
    """DataTable showing all tracked Claude sessions."""

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

    def __init__(self) -> None:
        super().__init__(cursor_type="row", zebra_stripes=True)
        self._sessions_by_row: dict[int, Session] = {}
        self._session_list: list[Session] = []

    def on_mount(self) -> None:
        self.add_columns("#", "Status", "Goal", "Progress", "Links")

    def refresh_sessions(self, sessions: dict[str, Session]) -> None:
        """Update the table with the current session list."""
        self._session_list = list(sessions.values())

        # Remember current cursor position
        prev_cursor = self.cursor_row

        self.clear()
        self._sessions_by_row.clear()

        for idx, session in enumerate(self._session_list):
            status_text = f"{session.status.icon} {session.status.label}"

            # Truncate goal/progress for table display
            goal = (session.goal or "—")[:35]
            progress = (session.progress or "—")[:20]

            # Format links
            if session.links:
                links_text = ", ".join(
                    f"{ln.icon}{ln.label}" for ln in session.links[:3]
                )
            else:
                links_text = "—"

            # Style for attention rows
            label_style = ""
            if session.status == SessionStatus.NEEDS_ATTENTION:
                label_style = "bold red"
            elif session.status == SessionStatus.CRASHED:
                label_style = "bold magenta"

            row_key = self.add_row(
                str(idx + 1),
                status_text,
                goal,
                progress,
                links_text,
            )
            self._sessions_by_row[idx] = session

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
