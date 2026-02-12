import os
import pytest
from unittest.mock import MagicMock, patch
from acc.config import ACCConfig
from acc.summarizer import Summarizer

def test_llm_config_loading(tmp_path):
    # Test loading from config file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_api_key: my-secret-key\nllm_base_url: https://local-llm:1234")
    
    config = ACCConfig.load(config_file)
    assert config.llm_api_key == "my-secret-key"
    assert config.llm_base_url == "https://local-llm:1234"

def test_llm_env_vars():
    # Test loading from environment variables
    with patch.dict(os.environ, {
        "ACC_LLM_API_KEY": "env-key",
        "ACC_LLM_BASE_URL": "https://env-url"
    }):
        config = ACCConfig.load()
        assert config.llm_api_key == "env-key"
        assert config.llm_base_url == "https://env-url"

def test_summarizer_init_with_config():
    # Test that Summarizer initializes Anthropic client with correct args
    api_key = "test-key"
    base_url = "https://test-url"
    
    summarizer = Summarizer(api_key=api_key, base_url=base_url)
    
    with patch("anthropic.Anthropic") as MockAnthropic:
        client = summarizer._get_client()
        
        MockAnthropic.assert_called_once_with(
            api_key=api_key,
            base_url=base_url
        )
        assert client == MockAnthropic.return_value
