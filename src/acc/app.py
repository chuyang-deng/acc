"""Main Textual application — Agent Command Center."""

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

from acc.agents import AgentRegistry
from acc.columns import create_default_registry
from acc.config import ACCConfig
from acc.discovery import SessionRegistry, capture_pane, discover_panes
from acc.links import LinkRegistry
from acc.notifications import NotificationManager
from acc.spawner import spawn_session
from acc.status import SessionStatus, content_changed, detect_status
from acc.summarizer import Summarizer
from acc.widgets.detail_panel import DetailPanel
from acc.widgets.header import ACCHeader
from acc.widgets.session_table import SessionSelected, SessionTable


# ──────────────────────────────────────────────────────────────────
# Spawn dialog — multi-step modal for creating new sessions
# ──────────────────────────────────────────────────────────────────


class SpawnDialog(ModalScreen[dict | None]):
    """Modal dialog for spawning a new Agent session."""

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
            yield Static("⚡ New Agent Session", classes="dialog-title")
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
            label.update("Goal / initial prompt for Agent:")
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
            label.update("Additional agent args (optional):")
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
# Input dialog — for sending text to the agent
# ──────────────────────────────────────────────────────────────────


class InputScreen(ModalScreen[str | None]):
    """Modal for sending input to a session."""

    DEFAULT_CSS = """
    InputScreen {
        align: center middle;
    }

    InputScreen #input-container {
        width: 60;
        height: auto;
        max-height: 10;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    InputScreen .input-title {
        text-style: bold;
        color: #bb86fc;
        margin-bottom: 1;
    }

    InputScreen Input {
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, target_name: str) -> None:
        super().__init__()
        self._target_name = target_name

    def compose(self) -> ComposeResult:
        with Vertical(id="input-container"):
            yield Static(f"Send to {self._target_name}", classes="input-title")
            yield Input(placeholder="Type command/response...", id="input-box")
            yield Static(
                "Press Enter to send, Escape to cancel",
                classes="dialog-hint",
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.dismiss(value)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ──────────────────────────────────────────────────────────────────
# Help dialog — quick reference for keys and config
# ──────────────────────────────────────────────────────────────────


class HelpScreen(ModalScreen):
    """Modal screen showing keybindings and help."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen #help-container {
        width: 80;
        height: auto;
        max-height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    HelpScreen .help-title {
        text-style: bold;
        color: #bb86fc;
        margin-bottom: 1;
        text-align: center;
    }

    HelpScreen .help-section {
        color: $secondary;
        text-style: bold;
        margin-top: 1;
    }

    HelpScreen .help-text {
        color: $text;
    }
    
    HelpScreen .help-hint {
        margin-top: 1;
        color: $text-muted;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
        Binding("?", "cancel", "Close"),
        Binding("h", "cancel", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static("Agent Command Center — Help", classes="help-title")
            
            yield Static("Keybindings", classes="help-section")
            yield Static(
                "  n       Spawn new session\n"
                "  Enter   Attach to session (tmux)\n"
                "  i       Send input to session\n"
                "  o       Open detected link\n"
                "  r       Refresh summaries\n"
                "  q       Quit\n"
                "  ? / h   Show this help",
                classes="help-text",
            )
            
            yield Static("Configuration", classes="help-section")
            yield Static(
                "Config file: ~/.acc/config.yaml\n"
                "\n"
                "Features:\n"
                "  • Customize columns (width, order)\n"
                "  • Define custom agents (regex patterns)\n"
                "  • Add custom links (Jira, Linear, etc.)\n"
                "  • Configure LLM (API key, Base URL, Model)",
                classes="help-text",
            )
            
            yield Static("Press Escape to close", classes="help-hint")

    def action_cancel(self) -> None:
        self.dismiss()


class ACCApp(App):
    """Agent Command Center — monitor and manage Agent Code sessions."""

    TITLE = "Agent Command Center"

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
        Binding("i", "send_input", "Input"),
        Binding("o", "open_link", "Open Link"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("?", "help", "Help", key_display="?"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = ACCConfig.load()
        self.registry = SessionRegistry()
        self.agent_registry = AgentRegistry(self.config.agents)
        self.link_registry = LinkRegistry(self.config.links)
        self.notifications = NotificationManager()
        self.summarizer = Summarizer(
            model=self.config.summary_model,
            interval=self.config.summary_interval,
            api_key=self.config.llm_api_key,
            base_url=self.config.llm_base_url,
        )
        self._poll_timer = None

    def compose(self) -> ComposeResult:
        yield ACCHeader()
        with Vertical(id="main-container"):
            yield SessionTable(registry=create_default_registry(self.config))
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
        header = self.query_one(ACCHeader)
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

    def on_data_table_row_selected(self, event) -> None:
        """Handle Enter key on a DataTable row — jump to that session."""
        self.action_jump()

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

        # Exit the TUI, then __main__.py will switch the tmux window
        # and restart acc so it's ready when the user comes back.
        self.exit(result=("jump", session.pane_id, session.session_name))

    def action_send_input(self) -> None:
        """Open input dialog to send text to the selected session."""
        table = self.query_one(SessionTable)
        session = table.get_selected_session()
        if session is None:
            self.bell()
            return

        self.push_screen(
            InputScreen(session.display_name),
            callback=lambda res: self._on_input_sent(session.pane_id, res),
        )

    def _on_input_sent(self, pane_id: str, text: str | None) -> None:
        """Send text to the tmux pane."""
        if not text:
            return
        
        # Send text + Enter to the pane
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, text, "Enter"],
            check=False,
        )
        # Force a refresh to see the reaction
        self._poll()

    def action_spawn(self) -> None:
        """Open the spawn dialog to create a new Agent session."""
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

    def action_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())


def _attach_to_tmux_pane(pane_id: str, session_name: str) -> None:
    """Attach to a tmux pane after exiting the TUI."""
    # Select the target pane first
    subprocess.run(["tmux", "select-window", "-t", pane_id], check=False)
    subprocess.run(["tmux", "select-pane", "-t", pane_id], check=False)

    # If running inside tmux, switch client; otherwise attach
    if os.environ.get("TMUX"):
        subprocess.run(["tmux", "switch-client", "-t", session_name], check=False)
    else:
        subprocess.run(["tmux", "attach-session", "-t", session_name], check=False)
