"""Entry point for `python -m ccc` and the `ccc` console script."""

import subprocess

from ccc.app import CCCApp


def _jump_to_pane(pane_id: str, session_name: str) -> None:
    """Attach the user's terminal to the tmux session at the given pane.

    1. select-window/pane so the right window is shown on attach
    2. attach-session blocks until user detaches (Ctrl-b d)
    """
    subprocess.run(["tmux", "select-window", "-t", pane_id], check=False)
    subprocess.run(["tmux", "select-pane", "-t", pane_id], check=False)
    subprocess.run(["tmux", "attach-session", "-t", session_name])


def main() -> None:
    while True:
        app = CCCApp()
        result = app.run()

        if isinstance(result, tuple) and result[0] == "jump":
            _, pane_id, session_name = result
            _jump_to_pane(pane_id, session_name)
            # attach-session blocks until user detaches (Ctrl-b d).
            # When they detach, ccc restarts automatically.
            continue
        else:
            break  # Normal quit (q)


if __name__ == "__main__":
    main()
