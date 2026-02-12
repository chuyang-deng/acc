"""Detail panel widget — shows full details for the selected session."""

from __future__ import annotations

from textual.widgets import Static

from acc.discovery import Session


class DetailPanel(Static):
    """Panel showing details for the currently selected session."""

    DEFAULT_CSS = """
    DetailPanel {
        height: auto;
        min-height: 7;
        max-height: 12;
        margin: 0 1;
        padding: 1 2;
        border: solid $primary-darken-2;
        background: $surface;
    }
    """

    def __init__(self) -> None:
        super().__init__("Select a session to view details")

    def show_session(self, session: Session | None) -> None:
        """Update the panel with session details."""
        if session is None:
            self.update("No session selected")
            return

        status_line = f"{session.status.icon} {session.status.label}"
        goal_line = session.goal or "Unknown"
        progress_line = session.progress or "Unknown"
        tmux_line = f'session "{session.session_name}", window {session.window_index}, pane {session.pane_index}'

        if session.links:
            links_line = "  ".join(
                f"{ln.icon} {ln.label} ({ln.url})" for ln in session.links
            )
        else:
            links_line = "none"

        text = (
            f"[bold]Session Detail — {goal_line}[/bold]\n"
            f"{'─' * 60}\n"
            f"  Status:   {status_line}\n"
            f"  Goal:     {goal_line}\n"
            f"  Progress: {progress_line}\n"
            f"  Links:    {links_line}\n"
            f"  Tmux:     {tmux_line}"
        )
        self.update(text)
