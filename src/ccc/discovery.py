"""Session discovery — find coding agent sessions running in tmux panes."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field

import psutil

from ccc.agents import AgentDetector, AgentRegistry
from ccc.links import DetectedLink
from ccc.status import SessionStatus


@dataclass
class Session:
    """Represents a single coding agent session running in a tmux pane."""

    pane_id: str  # e.g. "ccc:0.1"
    pane_pid: int
    session_name: str
    window_index: int
    pane_index: int

    # Mutable state
    agent_running: bool = False
    agent_name: str = ""  # e.g. "Claude", "OpenCode", "Codex"
    detector: AgentDetector | None = None
    status: SessionStatus = SessionStatus.WORKING
    exit_code: int | None = None
    goal: str = ""
    progress: str = ""
    links: list[DetectedLink] = field(default_factory=list)
    last_output_time: float = field(default_factory=time.time)
    last_content_hash: int = 0
    needs_attention_notified: bool = False
    spawned_by_ccc: bool = False

    @property
    def display_name(self) -> str:
        prefix = f"[{self.agent_name}] " if self.agent_name else ""
        return prefix + (self.goal or f"Session {self.pane_id}")


def _run_tmux(*args: str) -> str:
    """Run a tmux command and return stdout."""
    try:
        result = subprocess.run(
            ["tmux", *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _find_agent_in_tree(
    pid: int, agent_registry: AgentRegistry
) -> tuple[bool, AgentDetector | None]:
    """Walk the process tree under `pid` to check for any known agent process.

    Returns (agent_found, matching_detector).
    """
    all_names = agent_registry.all_process_names()
    try:
        parent = psutil.Process(pid)
        for proc in [parent] + parent.children(recursive=True):
            try:
                name = proc.name().lower()
                cmdline = " ".join(proc.cmdline()).lower()
                for agent_name in all_names:
                    if agent_name.lower() in name or agent_name.lower() in cmdline:
                        detector = agent_registry.find_detector(agent_name)
                        return True, detector
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False, None


def _is_process_alive(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _get_exit_code(pid: int) -> int | None:
    """Try to get exit code of a finished process. Returns None if still running."""
    try:
        proc = psutil.Process(pid)
        if proc.status() == psutil.STATUS_ZOMBIE:
            return proc.wait(timeout=0)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return None


def discover_panes(agent_registry: AgentRegistry) -> list[Session]:
    """Discover all tmux panes and check which ones are running a coding agent."""
    output = _run_tmux(
        "list-panes", "-a",
        "-F", "#{session_name}:#{window_index}.#{pane_index} #{pane_pid}",
    )
    if not output:
        return []

    sessions: list[Session] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        pane_id = parts[0]
        try:
            pane_pid = int(parts[1])
        except ValueError:
            continue

        # Parse pane_id: "session_name:window_index.pane_index"
        try:
            session_part, pane_part = pane_id.rsplit(".", 1)
            session_name, window_str = session_part.split(":", 1)
            window_index = int(window_str)
            pane_index = int(pane_part)
        except (ValueError, IndexError):
            continue

        agent_running, detector = _find_agent_in_tree(pane_pid, agent_registry)

        session = Session(
            pane_id=pane_id,
            pane_pid=pane_pid,
            session_name=session_name,
            window_index=window_index,
            pane_index=pane_index,
            agent_running=agent_running,
            agent_name=detector.name if detector else "",
            detector=detector,
        )
        sessions.append(session)

    return sessions


def capture_pane(pane_id: str, lines: int = 50) -> str:
    """Capture the last N lines of a tmux pane."""
    return _run_tmux(
        "capture-pane", "-t", pane_id, "-p",
        "-S", str(-lines),
    )


class SessionRegistry:
    """Maintains the set of tracked sessions across poll cycles."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self._spawned_pane_ids: set[str] = set()

    def track_spawned(self, pane_id: str) -> None:
        """Mark a pane as spawned by ccc so we keep tracking it."""
        self._spawned_pane_ids.add(pane_id)

    def update(self, discovered: list[Session]) -> dict[str, Session]:
        """Merge discovered panes into the registry.

        Returns the updated session dict.
        Only tracks panes that are running an agent or were spawned by ccc.
        """
        current_pane_ids = {s.pane_id for s in discovered}

        # Remove sessions whose panes no longer exist
        to_remove = []
        for pane_id in self.sessions:
            if (
                pane_id not in current_pane_ids
                and pane_id not in self._spawned_pane_ids
            ):
                to_remove.append(pane_id)
        for pane_id in to_remove:
            del self.sessions[pane_id]

        # Update or add sessions
        for new_session in discovered:
            should_track = (
                new_session.agent_running
                or new_session.pane_id in self._spawned_pane_ids
            )
            if not should_track:
                continue

            if new_session.pane_id in self.sessions:
                existing = self.sessions[new_session.pane_id]
                existing.agent_running = new_session.agent_running
                existing.pane_pid = new_session.pane_pid
                existing.agent_name = new_session.agent_name or existing.agent_name
                existing.detector = new_session.detector or existing.detector
            else:
                if new_session.pane_id in self._spawned_pane_ids:
                    new_session.spawned_by_ccc = True
                self.sessions[new_session.pane_id] = new_session

        return self.sessions
