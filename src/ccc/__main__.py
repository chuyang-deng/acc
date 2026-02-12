"""Entry point for `python -m ccc` and the `ccc` console script."""

import subprocess

from ccc.app import CCCApp


def _switch_to_pane(pane_id: str, session_name: str) -> None:
    """Switch the tmux client to the given pane."""
    subprocess.run(["tmux", "select-window", "-t", pane_id], check=False)
    subprocess.run(["tmux", "select-pane", "-t", pane_id], check=False)

    # Try switch-client first (works inside tmux), fall back to attach
    r = subprocess.run(
        ["tmux", "switch-client", "-t", session_name],
        capture_output=True,
    )
    if r.returncode != 0:
        subprocess.run(["tmux", "attach-session", "-t", session_name], check=False)


def main() -> None:
    while True:
        app = CCCApp()
        result = app.run()

        if isinstance(result, tuple) and result[0] == "jump":
            _, pane_id, session_name = result
            _switch_to_pane(pane_id, session_name)
            # Loop: ccc restarts automatically.
            # - Inside tmux: switch-client changes the visible window,
            #   ccc restarts in its own window in the background.
            #   User returns with Ctrl-b l and ccc is already running.
            # - Outside tmux: attach-session blocks until detach,
            #   then ccc restarts when user comes back.
            continue
        else:
            break  # Normal quit (q)


if __name__ == "__main__":
    main()
