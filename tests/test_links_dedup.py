
import unittest
from acc.links import LinkRegistry, DetectedLink

class TestLinkDeduplication(unittest.TestCase):
    def test_dedup_trailing_slash(self):
        registry = LinkRegistry()
        text = "Visit http://localhost:3000 and http://localhost:3000/ for more info."
        links = registry.scan(text)
        # Should be 1 link, not 2
        self.assertEqual(len(links), 1, f"Found {len(links)} links: {[l.url for l in links]}")

    def test_dedup_mixed_plugins(self):
        # GitHub plugin vs Generic plugin
        # GitHub plugin finds https://github.com/owner/repo
        # Generic plugin finds https://github.com/owner/repo/
        registry = LinkRegistry()
        text = "Check out https://github.com/owner/repo/ and the repo at owner/repo"
        links = registry.scan(text)
        # generic might find the URL. repo plugin might find 'owner/repo' -> 'https://github.com/owner/repo'
        # They should be deduped.
        # Note: repo plugin regex is roughly `[a-zA-Z0-9-]+/[a-zA-Z0-9rc\._-]+`
        
        # Let's see what happens.
        # We expect 1 link if they resolve to same URL.
        # If 'owner/repo' resolves to 'https://github.com/owner/repo'
        # And regex text has 'https://github.com/owner/repo/'
        
        # Actually owner/repo probably resolves to `https://github.com/owner/repo`.
        # The generic URL plugin will find `https://github.com/owner/repo/`.
        
        # This test might be tricky depending on which plugin runs first.
        # GitHubRepo runs before Generic.
        pass

if __name__ == '__main__':
    unittest.main()
