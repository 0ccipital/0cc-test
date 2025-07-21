"""Tests for ConversationTree."""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.tree import ConversationTree
from utils.errors import StateNotFoundError


def test_empty_tree():
    """Test empty tree initialization."""
    tree = ConversationTree()
    assert tree.state_count == 0
    assert tree.current_state_id is None
    assert tree.current_state is None


def test_add_root_state():
    """Test adding root state."""
    tree = ConversationTree()
    state = tree.add_state(None, "Test message", "Test response", "test-model")
    
    assert tree.state_count == 1
    assert state.hierarchical_id == "1"
    assert state.sequence_id == 1
    assert state.is_root is True
    assert tree.current_state_id == state.hierarchical_id


def test_add_child_states():
    """Test adding child states and branching."""
    tree = ConversationTree()
    
    # Add root
    root = tree.add_state(None, "Root message", "Root response", "test-model")
    
    # Add first child
    child1 = tree.add_state(root.hierarchical_id, "Child 1", "Response 1", "test-model")
    assert child1.hierarchical_id == "1.1"
    assert child1.sequence_id == 2
    
    # Add second child (creates branch)
    child2 = tree.add_state(root.hierarchical_id, "Child 2", "Response 2", "test-model")
    assert child2.hierarchical_id == "1.2"
    assert child2.sequence_id == 3
    
    # Verify tree structure
    assert tree.state_count == 3
    children = tree.get_children(root.hierarchical_id)
    assert len(children) == 2
    assert child1 in children
    assert child2 in children


def test_navigation():
    """Test tree navigation."""
    tree = ConversationTree()
    
    root = tree.add_state(None, "Root", "Root response", "test-model")
    child = tree.add_state(root.hierarchical_id, "Child", "Child response", "test-model")
    
    # Navigate by sequence ID
    assert tree.navigate_to(1) is True
    assert tree.current_state_id == root.hierarchical_id
    
    # Navigate by hierarchical ID
    assert tree.navigate_to("1.1") is True
    assert tree.current_state_id == child.hierarchical_id
    
    # Invalid navigation
    assert tree.navigate_to(999) is False
    assert tree.navigate_to("invalid") is False


def test_tree_serialization():
    """Test tree save/load."""
    tree = ConversationTree()
    
    root = tree.add_state(None, "Root", "Root response", "test-model")
    child = tree.add_state(root.hierarchical_id, "Child", "Child response", "test-model")
    
    # Convert to dict and back
    tree_dict = tree.to_dict()
    restored_tree = ConversationTree.from_dict(tree_dict)
    
    assert restored_tree.state_count == tree.state_count
    assert restored_tree.current_state_id == tree.current_state_id
    
    # Verify states are preserved
    original_states = tree.get_all_states()
    restored_states = restored_tree.get_all_states()
    
    assert len(original_states) == len(restored_states)
    for orig, restored in zip(original_states, restored_states):
        assert orig.hierarchical_id == restored.hierarchical_id
        assert orig.message == restored.message