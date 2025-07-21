"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.tree import ConversationTree
from core.state import ConversationState
from llm.client import OllamaClient
from storage.persistence import ConversationPersistence


@pytest.fixture
def sample_state():
    """Create a sample conversation state."""
    return ConversationState(
        hierarchical_id="1",
        sequence_id=1,
        parent_id=None,
        message="What is the capital of France?",
        response="The capital of France is Paris.",
        model="test-model",
        timestamp=datetime.now(),
        tags=frozenset(["test"]),
        metadata={}
    )


@pytest.fixture
def sample_tree():
    """Create a sample conversation tree with multiple states."""
    tree = ConversationTree()
    
    # Add root state
    state1 = tree.add_state(None, "What is the capital of France?", "Paris", "test-model")
    
    # Add child states
    state2 = tree.add_state(state1.hierarchical_id, "What about population?", "2.1 million", "test-model")
    state3 = tree.add_state(state1.hierarchical_id, "What about Germany?", "Berlin", "test-model")
    
    return tree


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    class MockOllamaClient:
        def __init__(self):
            self.connected = True
            self.models = ["test-model", "another-model"]
            
        def is_connected(self):
            return self.connected
            
        def get_available_models(self):
            return self.models
            
        def chat(self, messages, model):
            return "Mock response"
            
        def chat_stream(self, messages, model):
            yield "Mock "
            yield "streaming "
            yield "response"
            return "Mock streaming response"
            
        def unload_model(self, model):
            return True
    
    return MockOllamaClient()