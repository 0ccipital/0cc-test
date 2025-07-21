"""Tests for ConversationState."""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.state import ConversationState


def test_state_creation():
    """Test basic state creation."""
    state = ConversationState(
        hierarchical_id="1",
        sequence_id=1,
        parent_id=None,
        message="Test message",
        response="Test response",
        model="test-model",
        timestamp=datetime.now()
    )
    
    assert state.hierarchical_id == "1"
    assert state.sequence_id == 1
    assert state.is_root is True
    assert state.depth == 1


def test_state_with_tags():
    """Test state tag operations."""
    state = ConversationState(
        hierarchical_id="1",
        sequence_id=1,
        parent_id=None,
        message="Test",
        response="Test",
        model="test",
        timestamp=datetime.now()
    )
    
    # Add tag
    tagged_state = state.add_tag("important")
    assert "important" in tagged_state.tags
    assert len(tagged_state.tags) == 1
    
    # Remove tag
    untagged_state = tagged_state.remove_tag("important")
    assert "important" not in untagged_state.tags
    assert len(untagged_state.tags) == 0


def test_state_serialization():
    """Test state to/from dict conversion."""
    original_state = ConversationState(
        hierarchical_id="1.2",
        sequence_id=2,
        parent_id="1",
        message="Test message",
        response="Test response",
        model="test-model",
        timestamp=datetime.now(),
        tags=frozenset(["tag1", "tag2"])
    )
    
    # Convert to dict and back
    state_dict = original_state.to_dict()
    restored_state = ConversationState.from_dict(state_dict)
    
    assert restored_state.hierarchical_id == original_state.hierarchical_id
    assert restored_state.sequence_id == original_state.sequence_id
    assert restored_state.tags == original_state.tags