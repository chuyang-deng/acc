import pytest
from pathlib import Path
import yaml
from acc.config import ACCConfig
from acc.columns import create_default_registry
from acc.agents import AgentRegistry
from acc.links import LinkRegistry

@pytest.fixture
def custom_config_file(tmp_path):
    config_data = {
        "columns": [
            {"key": "agent", "width": 20},
            {"key": "status", "width": 5},
            # "goal" is omitted, so it should be hidden/missing from the registry
        ],
        "agents": [
            {
                "name": "CustomBoi",
                "process_names": ["boi"],
                "working_patterns": ["doing stuff"],
                "attention_patterns": ["hey listen"],
            }
        ],
        "links": [
            {
                "name": "ticket",
                "pattern": "TICKET-\\d+",
                "icon": "🎫",
                "label": "Ticket",
            }
        ]
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_file

def test_custom_columns(custom_config_file):
    config = ACCConfig.load(custom_config_file)
    registry = create_default_registry(config)
    
    cols = registry.columns
    assert len(cols) == 2
    assert cols[0].key == "agent"
    assert cols[0].width == 20
    assert cols[1].key == "status" 
    assert cols[1].width == 5

def test_default_columns_fallback():
    # Load with no config file -> should get defaults
    config = ACCConfig.load(Path("/non/existent/path"))
    registry = create_default_registry(config)
    assert len(registry.columns) == 6 # #, status, agent, goal, progress, links

def test_custom_agents(custom_config_file):
    config = ACCConfig.load(custom_config_file)
    registry = AgentRegistry(config.agents)
    
    detector = registry.get_detector_by_name("CustomBoi")
    assert detector is not None
    assert "boi" in detector.process_names
    # Check if compiled regex works
    assert detector.working_patterns[0].search("I am doing stuff now")

def test_custom_links(custom_config_file):
    config = ACCConfig.load(custom_config_file)
    registry = LinkRegistry(config.links)
    
    # helper to find the custom plugin
    plugin = next((p for p in registry.plugins if p.name == "ticket"), None)
    assert plugin is not None
    assert plugin.icon == "🎫"
    
    # Test matching
    text = "Reference to TICKET-123 in the logs"
    links = registry.scan(text)
    assert len(links) == 1
    assert links[0].url == "TICKET-123"
