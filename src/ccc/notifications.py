"""Notification manager — track state transitions and fire alerts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccc.status import SessionStatus

if TYPE_CHECKING:
    from ccc.discovery import Session


# Transitions that should trigger a notification
_NOTIFY_TRANSITIONS: set[tuple[SessionStatus, SessionStatus]] = {
    (SessionStatus.WORKING, SessionStatus.NEEDS_ATTENTION),
    (SessionStatus.WORKING, SessionStatus.DONE),
    (SessionStatus.WORKING, SessionStatus.CRASHED),
    (SessionStatus.IDLE, SessionStatus.NEEDS_ATTENTION),
}


class NotificationManager:
    """Tracks session state transitions and fires notifications."""

    def __init__(self) -> None:
        self._previous_states: dict[str, SessionStatus] = {}
        self._attention_panes: set[str] = set()

    @property
    def badge_count(self) -> int:
        """Number of sessions currently needing attention."""
        return len(self._attention_panes)

    def clear_attention(self, pane_id: str) -> None:
        """Clear the attention flag for a session (e.g. after user jumps in)."""
        self._attention_panes.discard(pane_id)

    def check_transitions(
        self,
        sessions: dict[str, "Session"],  # noqa: F821
    ) -> list[str]:
        """Check all sessions for state transitions.

        Returns list of pane_ids that newly need attention.
        """
        newly_alerting: list[str] = []

        for pane_id, session in sessions.items():
            prev = self._previous_states.get(pane_id)
            curr = session.status

            if prev is not None and (prev, curr) in _NOTIFY_TRANSITIONS:
                if not session.needs_attention_notified:
                    newly_alerting.append(pane_id)
                    self._attention_panes.add(pane_id)
                    session.needs_attention_notified = True

            # If session returned to working, clear its attention flag
            if curr == SessionStatus.WORKING:
                self._attention_panes.discard(pane_id)
                session.needs_attention_notified = False

            self._previous_states[pane_id] = curr

        # Clean up stale entries
        active_ids = set(sessions.keys())
        stale = set(self._previous_states.keys()) - active_ids
        for pane_id in stale:
            del self._previous_states[pane_id]
            self._attention_panes.discard(pane_id)

        return newly_alerting

    @staticmethod
    def ring_bell() -> None:
        """Emit a terminal bell character."""
        print("\a", end="", flush=True)
