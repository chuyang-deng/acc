"""Session spawner — create new Agent sessions in tmux panes."""

from __future__ import annotations

import logging
import re
import subprocess

logging.basicConfig(
    filename="acc_debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("acc.spawner")

from acc.config import ACCConfig


def _slugify(text: str) -> str:
    """Convert text to a tmux-friendly window name slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:40] or "session"


def _ensure_session(session_name: str) -> bool:
    """Ensure the tmux session exists, creating it if needed.

    Returns True if session exists or was created.
    """
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True,
    )
    if result.returncode == 0:
        return True

    # Create a new detached session
    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", session_name],
        capture_output=True,
    )
    return result.returncode == 0


def spawn_session(
    working_dir: str,
    goal: str,
    extra_args: list[str] | None = None,
    config: ACCConfig | None = None,
) -> str | None:
    """Spawn a new Agent session in a tmux window.

    Args:
        working_dir: Directory to cd into.
        goal: Task description / initial prompt.
        extra_args: Additional CLI arguments.
        config: App configuration.

    Returns:
        The pane ID of the new session, or None on failure.
    """
    if config is None:
        config = ACCConfig()

    session_name = config.tmux_session
    claude_path = config.claude_path
    window_name = _slugify(goal)

    # Build claude command
    all_args = list(config.default_claude_args)
    if extra_args:
        all_args.extend(extra_args)

    args_str = " ".join(all_args) if all_args else ""
    prompt_escaped = goal.replace("'", "'\\''")

    command = f"cd {working_dir} && {claude_path} {args_str} -p '{prompt_escaped}'"

    # Ensure the tmux session exists
    if not _ensure_session(session_name):
        logger.error("Failed to ensure session %s", session_name)
        return None

    # Create new window
    result = subprocess.run(
        [
            "tmux",
            "new-window",
            "-t",
            session_name,
            "-n",
            window_name,
            "-P",
            "-F",
            "#{session_name}:#{window_index}.#{pane_index}",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        logger.error("tmux new-window failed: %s", result.stderr)
        return None

    pane_id = result.stdout.strip()
    logger.info("Spawned session %s window %s -> pane %s", session_name, window_name, pane_id)
    return pane_id or None
