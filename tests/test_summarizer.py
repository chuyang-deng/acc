"""Tests for the LLM summarizer."""

from ccc.summarizer import Summarizer, SessionSummary


class TestSummarizerParsing:
    """Test response parsing (no API calls needed)."""

    def test_parses_well_formed_response(self):
        text = (
            "Goal: Fix the flaky auth tests\n"
            "Progress: Identified root cause in token refresh\n"
            "Needs user: no"
        )
        summary = Summarizer._parse_response(text)
        assert summary.goal == "Fix the flaky auth tests"
        assert summary.progress == "Identified root cause in token refresh"
        assert summary.needs_user is False

    def test_parses_needs_user_yes(self):
        text = (
            "Goal: Update API docs\n"
            "Progress: Waiting for clarification\n"
            "Needs user: yes"
        )
        summary = Summarizer._parse_response(text)
        assert summary.needs_user is True

    def test_handles_missing_fields(self):
        text = "Some unexpected response format"
        summary = Summarizer._parse_response(text)
        assert summary.goal == "Unknown"
        assert summary.progress == "Unknown"
        assert summary.needs_user is False


class TestSummarizerCaching:
    """Test cache behavior."""

    def test_should_refresh_new_pane(self):
        s = Summarizer(interval=60)
        assert s.should_refresh("pane-1") is True

    def test_get_cached_returns_none_for_unknown(self):
        s = Summarizer()
        assert s.get_cached("unknown") is None
