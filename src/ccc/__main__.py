"""Entry point for `python -m ccc` and the `ccc` console script."""

from ccc.app import CCCApp, _attach_to_tmux_pane


def main() -> None:
    app = CCCApp()
    result = app.run()

    # After TUI exits, handle any pending action
    if isinstance(result, tuple) and result[0] == "jump":
        _, pane_id, session_name = result
        _attach_to_tmux_pane(pane_id, session_name)


if __name__ == "__main__":
    main()
