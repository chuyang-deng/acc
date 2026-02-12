import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
from pathlib import Path

# Mock modules before importing acc.summarizer
sys.modules["anthropic"] = MagicMock()
sys.modules["openai"] = MagicMock()

from acc.summarizer import Summarizer

class TestSummarizerProviders(unittest.TestCase):
    def setUp(self):
        self.mock_anthropic = sys.modules["anthropic"]
        self.mock_openai = sys.modules["openai"]
        
    def test_init_anthropic_default(self):
        s = Summarizer(api_key="test_key")
        self.assertEqual(s.provider, "anthropic")
        
        # Test lazy init
        client = s._get_client()
        self.mock_anthropic.Anthropic.assert_called_with(api_key="test_key", base_url=None)

    def test_init_openai(self):
        s = Summarizer(api_key="test_key", provider="openai")
        self.assertEqual(s.provider, "openai")
        
        client = s._get_client()
        self.mock_openai.OpenAI.assert_called_with(api_key="test_key", base_url=None)

    def test_init_ollama_defaults(self):
        s = Summarizer(provider="ollama")
        self.assertEqual(s.provider, "ollama")
        
        client = s._get_client()
        # Should default to localhost:11434/v1 and dummy key
        self.mock_openai.OpenAI.assert_called_with(api_key="ollama", base_url="http://localhost:11434/v1")

    def test_init_apple(self):
        s = Summarizer(provider="apple")
        self.assertEqual(s.provider, "apple")
        
        client = s._get_client()
        self.assertEqual(client, "apple")

    @patch("acc.summarizer.Summarizer._parse_response")
    def test_summarize_anthropic(self, mock_parse):
        s = Summarizer(provider="anthropic")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Goal: Test")]
        mock_client.messages.create.return_value = mock_response
        s._client = mock_client
        
        # Mock cache to force update
        s.should_refresh = MagicMock(return_value=True)
        
        summary = s.summarize("pane1", "content")
        
        mock_client.messages.create.assert_called()
        mock_parse.assert_called_with("Goal: Test")

    @patch("acc.summarizer.Summarizer._parse_response")
    def test_summarize_openai(self, mock_parse):
        s = Summarizer(provider="openai")
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Goal: OpenAI"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        s._client = mock_client
        
        s.should_refresh = MagicMock(return_value=True)
        
        summary = s.summarize("pane1", "content")
        
        mock_client.chat.completions.create.assert_called()
        mock_parse.assert_called_with("Goal: OpenAI")

    @patch("acc.summarizer.subprocess.run")
    @patch("acc.summarizer.Path")
    @patch("acc.summarizer.Summarizer._parse_response")
    def test_summarize_apple(self, mock_parse, mock_path_cls, mock_run):
        s = Summarizer(provider="apple")
        s._client = "apple"
        
        # Mock Path: Path(__file__).parent / "scripts" / "afm_wrapper.swift"
        # mock_path_cls is the Path class
        mock_file_path = MagicMock()
        mock_path_cls.return_value = mock_file_path
        
        mock_parent = MagicMock()
        mock_file_path.parent = mock_parent
        
        mock_scripts_dir = MagicMock()
        mock_parent.__truediv__.return_value = mock_scripts_dir
        
        mock_script_path = MagicMock()
        mock_scripts_dir.__truediv__.return_value = mock_script_path
        
        # Script exists
        mock_script_path.exists.return_value = True
        
        # When str(script_path) is called
        mock_script_path.__str__.return_value = "/path/to/src/acc/scripts/afm_wrapper.swift"
        
        # Mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Goal: Apple"
        mock_run.return_value = mock_result
        
        s.should_refresh = MagicMock(return_value=True)
        
        summary = s.summarize("pane1", "content")
        
        # Verify swift command was called
        args, _ = mock_run.call_args
        cmd = args[0]
        self.assertEqual(cmd[0], "swift")
        self.assertIn("afm_wrapper.swift", str(cmd[1]))
        
        mock_parse.assert_called_with("Goal: Apple")

    @patch("acc.summarizer.platform")
    @patch("acc.summarizer.urllib.request.urlopen")
    def test_resolve_auto_provider(self, mock_urlopen, mock_platform):
        s = Summarizer(provider="auto")
        
        # Scenario 1: Mac with version >= 26 -> Apple
        mock_platform.system.return_value = "Darwin"
        mock_platform.mac_ver.return_value = ('26.1.0', ('', '', ''), '')
        
        # Mock script existence
        with patch("acc.summarizer.Path") as mock_path:
            mock_script = MagicMock()
            mock_script.exists.return_value = True
            mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value = mock_script
            
            provider = s._resolve_auto_provider()
            self.assertEqual(provider, "apple")

        # Scenario 2: Mac < 26 -> Should check Ollama
        mock_platform.mac_ver.return_value = ('25.0.0', ('', '', ''), '')
        # Ollama running
        mock_urlopen.return_value.__enter__.return_value = MagicMock()
        
        provider = s._resolve_auto_provider()
        self.assertEqual(provider, "ollama")
        
        # Scenario 3: Ollama down, API key set -> Anthropic
        mock_urlopen.side_effect = Exception("Connection refused")
        s.api_key = "sk-ant-123"
        provider = s._resolve_auto_provider()
        self.assertEqual(provider, "anthropic")
        
        # Scenario 4: OpenAI key
        s.api_key = "sk-123"
        provider = s._resolve_auto_provider()
        self.assertEqual(provider, "openai")

if __name__ == "__main__":
    unittest.main()
