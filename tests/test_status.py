"""Tests for session status detection."""

import time

from ccc.agents import ClaudeDetector, OpenCodeDetector, CodexDetector, AiderDetector
from ccc.status import SessionStatus, detect_status, content_changed


class TestDetectStatus:
    """Test the detect_status heuristics with default (no detector) fallback."""

    def test_crashed_when_process_exited_nonzero(self):
        status = detect_status(
            pane_content="some output\nerror occurred",
            agent_running=False,
            exit_code=1,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.CRASHED

    def test_done_when_process_exited_cleanly(self):
        status = detect_status(
            pane_content="all done",
            agent_running=False,
            exit_code=0,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.DONE

    def test_done_when_process_exited_no_code(self):
        status = detect_status(
            pane_content="finished",
            agent_running=False,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.DONE

    def test_needs_attention_question_mark(self):
        status = detect_status(
            pane_content="Should I proceed with the refactoring?\n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_needs_attention_yes_no_prompt(self):
        status = detect_status(
            pane_content="Do you want to continue? (Y/n)",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_needs_attention_bare_prompt(self):
        status = detect_status(
            pane_content="some output\n❯ \n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_working_with_spinner(self):
        status = detect_status(
            pane_content="Processing ⠋ loading...",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.WORKING

    def test_working_with_recent_output(self):
        status = detect_status(
            pane_content="Writing file auth.py\nAdding middleware",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
        )
        assert status == SessionStatus.WORKING

    def test_idle_after_timeout(self):
        status = detect_status(
            pane_content="last output a while ago",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time() - 60,  # 60s ago
        )
        assert status == SessionStatus.IDLE


class TestAgentSpecificDetection:
    """Test status detection with agent-specific detectors."""

    def test_claude_question_detection(self):
        detector = ClaudeDetector()
        status = detect_status(
            pane_content="Do you want to proceed?\n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
            detector=detector,
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_opencode_waiting_for_input(self):
        detector = OpenCodeDetector()
        status = detect_status(
            pane_content="waiting for input\n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
            detector=detector,
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_codex_approve_prompt(self):
        detector = CodexDetector()
        status = detect_status(
            pane_content="Please approve this change\n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
            detector=detector,
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_aider_prompt(self):
        detector = AiderDetector()
        status = detect_status(
            pane_content="aider> \n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
            detector=detector,
        )
        assert status == SessionStatus.NEEDS_ATTENTION

    def test_opencode_working(self):
        detector = OpenCodeDetector()
        status = detect_status(
            pane_content="thinking about the problem...\n",
            agent_running=True,
            exit_code=None,
            last_output_time=time.time(),
            detector=detector,
        )
        assert status == SessionStatus.WORKING


class TestContentChanged:
    """Test content change detection."""

    def test_detects_change(self):
        changed, h = content_changed(0, "new content")
        assert changed is True

    def test_detects_no_change(self):
        content = "same content"
        _, h = content_changed(0, content)
        changed, _ = content_changed(h, content)
        assert changed is False
