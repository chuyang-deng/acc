"""Tests for link detection plugins."""

from ccc.links import LinkRegistry
from ccc.links.github import GitHubPRPlugin, GitHubIssuePlugin
from ccc.links.linear import LinearPlugin
from ccc.links.localhost import LocalhostPlugin
from ccc.links.custom import load_custom_plugins


class TestGitHubPR:
    def test_detects_pr_url(self):
        plugin = GitHubPRPlugin()
        links = plugin.find_links("Check out https://github.com/user/repo/pull/42 for details")
        assert len(links) == 1
        assert links[0].label == "PR #42"
        assert links[0].url == "https://github.com/user/repo/pull/42"

    def test_multiple_prs(self):
        plugin = GitHubPRPlugin()
        text = "PR https://github.com/a/b/pull/1 and https://github.com/c/d/pull/99"
        links = plugin.find_links(text)
        assert len(links) == 2

    def test_no_match(self):
        plugin = GitHubPRPlugin()
        links = plugin.find_links("nothing here")
        assert len(links) == 0


class TestGitHubIssue:
    def test_detects_issue_url(self):
        plugin = GitHubIssuePlugin()
        links = plugin.find_links("See https://github.com/user/repo/issues/7")
        assert len(links) == 1
        assert links[0].label == "Issue #7"


class TestLinear:
    def test_detects_ticket(self):
        plugin = LinearPlugin()
        links = plugin.find_links("Working on ENG-123 now")
        assert len(links) == 1
        assert links[0].label == "ENG-123"

    def test_multiple_tickets(self):
        plugin = LinearPlugin()
        links = plugin.find_links("ENG-1 and PROJ-42 are related")
        assert len(links) == 2


class TestLocalhost:
    def test_detects_localhost(self):
        plugin = LocalhostPlugin()
        links = plugin.find_links("Server at http://localhost:5173")
        assert len(links) == 1
        assert links[0].label == "localhost:5173"

    def test_https_localhost(self):
        plugin = LocalhostPlugin()
        links = plugin.find_links("https://localhost:3000/api")
        assert len(links) == 1


class TestCustomPlugins:
    def test_loads_custom_plugin(self):
        configs = [{
            "name": "jira",
            "icon": "🎫",
            "pattern": r"JIRA-\d+",
            "label": "Jira",
        }]
        plugins = load_custom_plugins(configs)
        assert len(plugins) == 1
        links = plugins[0].find_links("Fix JIRA-100")
        assert len(links) == 1
        assert links[0].label == "Jira"

    def test_skips_empty_pattern(self):
        configs = [{"name": "bad", "pattern": ""}]
        plugins = load_custom_plugins(configs)
        assert len(plugins) == 0


class TestLinkRegistry:
    def test_scans_all_plugins(self):
        registry = LinkRegistry()
        text = (
            "PR: https://github.com/a/b/pull/10\n"
            "Server: http://localhost:3000\n"
            "Ticket: ENG-55\n"
        )
        links = registry.scan(text)
        assert len(links) >= 3

    def test_deduplicates(self):
        registry = LinkRegistry()
        text = "https://github.com/a/b/pull/10 https://github.com/a/b/pull/10"
        links = registry.scan(text)
        assert len(links) == 1

    def test_with_custom_plugins(self):
        registry = LinkRegistry([{
            "name": "vercel",
            "icon": "🚀",
            "pattern": r"https://[\w-]+\.vercel\.app",
            "label": "Preview",
        }])
        links = registry.scan("Deploy at https://my-app.vercel.app")
        assert any(l.label == "Preview" for l in links)
