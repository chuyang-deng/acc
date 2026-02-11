"""Main Textual application — Claude Command Center."""

from __future__ import annotations

import os
import subprocess
import time
import webbrowser

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, Static

from ccc.agents import AgentRegistry
from ccc.config import CCCConfig
from ccc.discovery import SessionRegistry, capture_pane, discover_panes
from ccc.links import LinkRegistry
from ccc.notifications import NotificationManager
from ccc.spawner import spawn_session
from ccc.status import SessionStatus, content_changed, detect_status
from ccc.summarizer import Summarizer
from ccc.widgets.detail_panel import DetailPanel
from ccc.widgets.header import CCCHeader
from ccc.widgets.session_table import SessionSelected, SessionTable


# ──────────────────────────────────────────────────────────────────
# Spawn dialog — multi-step modal for creating new sessions
# ──────────────────────────────────────────────────────────────────


class SpawnDialog(ModalScreen[dict | None]):
    """Modal dialog for spawning a new Claude session."""

    DEFAULT_CSS = """
    SpawnDialog {
        align: center middle;
    }

    SpawnDialog #dialog-container {
        width: 70;
        height: auto;
        max-height: 22;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    SpawnDialog .dialog-title {
        text-style: bold;
        color: #bb86fc;
        margin-bottom: 1;
    }

    SpawnDialog .dialog-label {
        margin-top: 1;
        color: $text-muted;
    }

    SpawnDialog Input {
        margin: 0 0 1 0;
    }

    SpawnDialog .dialog-hint {
        color: $text-disabled;
        text-style: italic;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, default_dir: str = "") -> None:
        super().__init__()
        self._default_dir = default_dir or os.getcwd()
        self._step = 0  # 0=dir, 1=goal, 2=args
        self._data: dict = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Static("⚡ New Claude Session", classes="dialog-title")
            yield Label("Working directory:", classes="dialog-label")
            yield Input(
                value=self._default_dir,
                placeholder="/path/to/project",
                id="input-dir",
            )
            yield Static(
                "Press Enter to continue, Escape to cancel",
                classes="dialog-hint",
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()

        if self._step == 0:
            # Working directory
            self._data["working_dir"] = value or self._default_dir
            self._step = 1
            # Switch to goal input
            label = self.query_one(".dialog-label", Label)
            label.update("Goal / initial prompt for Claude:")
            inp = self.query_one(Input)
            inp.value = ""
            inp.placeholder = "e.g. Fix the flaky auth tests"

        elif self._step == 1:
            if not value:
                self.app.bell()
                return
            self._data["goal"] = value
            self._step = 2
            label = self.query_one(".dialog-label", Label)
            label.update("Additional claude args (optional):")
            inp = self.query_one(Input)
            inp.value = ""
            inp.placeholder = "e.g. --model opus --resume abc123"

        elif self._step == 2:
            self._data["extra_args"] = value.split() if value else []
            self.dismiss(self._data)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ──────────────────────────────────────────────────────────────────
# Link picker — shown when a session has multiple links
# ──────────────────────────────────────────────────────────────────


class LinkPickerScreen(ModalScreen[str | None]):
    """Modal for picking a link to open."""

    DEFAULT_CSS = """
    LinkPickerScreen {
        align: center middle;
    }

    LinkPickerScreen #picker-container {
        width: 60;
        height: auto;
        max-height: 15;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    LinkPickerScreen .picker-title {
        text-style: bold;
        color: #bb86fc;
        margin-bottom: 1;
    }

    LinkPickerScreen .picker-item {
        padding: 0 1;
    }

    LinkPickerScreen .picker-item:hover {
        background: $secondary;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, links: list) -> None:
        super().__init__()
        self._links = links

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-container"):
            yield Static("Open Link", classes="picker-title")
            for idx, link in enumerate(self._links):
                yield Static(
                    f"  [{idx + 1}] {link.icon} {link.label}  —  {link.url}",
                    classes="picker-item",
                    id=f"link-{idx}",
                )
            yield Static(
                "\nPress 1-9 to open, Escape to cancel",
                classes="picker-hint",
            )

    def on_key(self, event) -> None:
        if event.character and event.character.isdigit():
            idx = int(event.character) - 1
            if 0 <= idx < len(self._links):
                self.dismiss(self._links[idx].url)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ──────────────────────────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────────────────────────


class CCCApp(App):
    """Claude Command Center — monitor and manage Claude Code sessions."""

    TITLE = "Claude Command Center"

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        height: 1fr;
    }

    #empty-state {
        content-align: center middle;
        height: 1fr;
        color: $text-muted;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "spawn", "New Session"),
        Binding("enter", "jump", "Jump to Pane"),
        Binding("o", "open_link", "Open Link"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = CCCConfig.load()
        self.registry = SessionRegistry()
        self.agent_registry = AgentRegistry(self.config.agents)
        self.link_registry = LinkRegistry(self.config.links)
        self.notifications = NotificationManager()
        self.summarizer = Summarizer(
            model=self.config.summary_model,
            interval=self.config.summary_interval,
        )
        self._poll_timer = None

    def compose(self) -> ComposeResult:
        yield CCCHeader()
        with Vertical(id="main-container"):
            yield SessionTable()
            yield DetailPanel()
        yield Footer()

    def on_mount(self) -> None:
        """Start the polling loop."""
        self._poll()
        self._poll_timer = self.set_interval(
            self.config.refresh_interval, self._poll
        )

    def _poll(self) -> None:
        """Discover sessions, update statuses, and refresh the UI."""
        # Discover panes
        discovered = discover_panes(self.agent_registry)
        sessions = self.registry.update(discovered)

        # Update each session's status, links, and summary
        for pane_id, session in sessions.items():
            content = capture_pane(pane_id, lines=50)
            changed, new_hash = content_changed(session.last_content_hash, content)

            if changed:
                session.last_output_time = time.time()
                session.last_content_hash = new_hash

                # Update links
                session.links = self.link_registry.scan(content)

            # Detect status using agent-specific detector
            session.status = detect_status(
                pane_content=content,
                agent_running=session.agent_running,
                exit_code=session.exit_code,
                last_output_time=session.last_output_time,
                detector=session.detector,
            )

            # LLM summarization (async-friendly — runs in background)
            if self.summarizer.should_refresh(pane_id):
                long_content = capture_pane(pane_id, lines=200)
                summary = self.summarizer.summarize(pane_id, long_content)
                if summary:
                    session.goal = summary.goal
                    session.progress = summary.progress
            elif cached := self.summarizer.get_cached(pane_id):
                session.goal = session.goal or cached.goal
                session.progress = session.progress or cached.progress

        # Check for notifications
        alerting = self.notifications.check_transitions(sessions)
        if alerting:
            self.notifications.ring_bell()

        # Update UI
        header = self.query_one(CCCHeader)
        header.update_counts(len(sessions), self.notifications.badge_count)

        table = self.query_one(SessionTable)
        table.refresh_sessions(sessions)

        # Update detail panel for current selection
        selected = table.get_selected_session()
        detail = self.query_one(DetailPanel)
        detail.show_session(selected)

    # ── Keybinding actions ───────────────────────────────────────

    def on_session_selected(self, message: SessionSelected) -> None:
        """Update the detail panel when a session is highlighted."""
        detail = self.query_one(DetailPanel)
        detail.show_session(message.session)

    def action_cursor_down(self) -> None:
        table = self.query_one(SessionTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self.query_one(SessionTable)
        table.action_cursor_up()

    def action_jump(self) -> None:
        """Jump to the selected session's tmux pane."""
        table = self.query_one(SessionTable)
        session = table.get_selected_session()
        if session is None:
            self.bell()
            return

        # Clear attention for this session
        self.notifications.clear_attention(session.pane_id)
        session.needs_attention_notified = False

        # Exit the TUI and attach to the tmux pane
        self.exit(result=("jump", session.pane_id, session.session_name))

    def action_spawn(self) -> None:
        """Open the spawn dialog to create a new Claude session."""
        recent = self.config.recent_dirs
        default_dir = recent[0] if recent else os.getcwd()
        self.push_screen(SpawnDialog(default_dir), callback=self._on_spawn_result)

    def _on_spawn_result(self, result: dict | None) -> None:
        """Handle the spawn dialog result."""
        if result is None:
            return

        pane_id = spawn_session(
            working_dir=result["working_dir"],
            goal=result["goal"],
            extra_args=result.get("extra_args", []),
            config=self.config,
        )

        if pane_id:
            self.registry.track_spawned(pane_id)
            # Update recent dirs
            wd = result["working_dir"]
            if wd not in self.config.recent_dirs:
                self.config.recent_dirs.insert(0, wd)
                self.config.recent_dirs = self.config.recent_dirs[:10]
            # Force immediate poll
            self._poll()
        else:
            self.bell()

    def action_open_link(self) -> None:
        """Open a link from the selected session."""
        table = self.query_one(SessionTable)
        session = table.get_selected_session()
        if session is None or not session.links:
            self.bell()
            return

        if len(session.links) == 1:
            webbrowser.open(session.links[0].url)
        else:
            self.push_screen(
                LinkPickerScreen(session.links),
                callback=self._on_link_picked,
            )

    def _on_link_picked(self, url: str | None) -> None:
        if url:
            webbrowser.open(url)

    def action_refresh(self) -> None:
        """Force refresh all summaries."""
        for pane_id in list(self.registry.sessions.keys()):
            self.summarizer.invalidate(pane_id)
        self._poll()


def _attach_to_tmux_pane(pane_id: str, session_name: str) -> None:
    """Attach to a tmux pane after exiting the TUI."""
    # Select the target pane first
    subprocess.run(["tmux", "select-window", "-t", pane_id], check=False)
    subprocess.run(["tmux", "select-pane", "-t", pane_id], check=False)

    # Attach to the session
    subprocess.run(["tmux", "attach-session", "-t", session_name], check=False)
