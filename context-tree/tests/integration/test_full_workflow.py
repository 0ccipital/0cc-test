"""Integration tests for full application workflow."""

import pytest
from src.core.tree import ConversationTree
from src.core.navigation import TreeNavigator
from src.storage.persistence import ConversationPersistence


def test_complete_conversation_workflow(temp_storage_dir):
    """Test complete workflow: create, navigate, save, load."""
    # Create tree and add states
    tree = ConversationTree()
    navigator = TreeNavigator(tree)
    
    # Build conversation tree
    state1 = tree.add_state(None, "What is AI?", "AI is artificial intelligence", "test-model")
    state2 = tree.add_state(state1.hierarchical_id, "How does it work?", "Through algorithms", "test-model")
    state3 = tree.add_state(state1.hierarchical_id, "What are the types?", "ML, NLP, etc.", "test-model")
    
    # Test navigation
    navigator.go_to_state(1)  # Go to root
    assert tree.current_state_id == state1.hierarchical_id
    
    navigator.go_to_state("1.2")  # Go to branch
    assert tree.current_state_id == state3.hierarchical_id
    
    # Test save/load
    persistence = ConversationPersistence(temp_storage_dir)
    filename = persistence.save_conversation(tree, "test_conversation")
    
    # Load into new tree
    loaded_tree = persistence.load_conversation(filename)
    
    assert loaded_tree.state_count == tree.state_count
    assert loaded_tree.current_state_id == tree.current_state_id
    
    # Verify conversation messages
    original_messages = tree.get_conversation_messages()
    loaded_messages = loaded_tree.get_conversation_messages()
    assert original_messages == loaded_messages


def test_branching_and_tagging_workflow(sample_tree):
    """Test branching with tagging workflow."""
    tree = sample_tree
    
    # Tag states
    current_state = tree.current_state
    tagged_state = current_state.add_tag("important")
    tree.update_state(current_state.hierarchical_id, tagged_state)
    
    # Navigate and verify tags persist
    tree.navigate_to(1)
    tree.navigate_to(current_state.hierarchical_id)
    
    updated_state = tree.current_state
    assert "important" in updated_state.tags