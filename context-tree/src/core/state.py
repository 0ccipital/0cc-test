"""Conversation state model and operations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, FrozenSet, Dict, Any, Set


@dataclass(frozen=True)
class ConversationState:
    """Immutable conversation state representation."""
    
    hierarchical_id: str
    sequence_id: int
    parent_id: Optional[str]
    message: str
    response: str
    model: str
    timestamp: datetime
    tags: FrozenSet[str] = field(default_factory=frozenset)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_branch(self) -> bool:
        """Check if this state represents a branch."""
        return self.metadata.get('is_branch', False)

    @property
    def display_name(self) -> str:
        """Get display name combining sequence and hierarchical ID."""
        return f"{self.sequence_id} ({self.hierarchical_id})"
    
    @property
    def is_root(self) -> bool:
        """Check if this is a root state."""
        return self.parent_id is None
    
    @property
    def depth(self) -> int:
        """Calculate depth in tree based on hierarchical ID."""
        return len(self.hierarchical_id.split('.'))
    
    def with_tags(self, tags: Set[str]) -> 'ConversationState':
        """Return new state with updated tags (immutable pattern)."""
        return ConversationState(
            hierarchical_id=self.hierarchical_id,
            sequence_id=self.sequence_id,
            parent_id=self.parent_id,
            message=self.message,
            response=self.response,
            model=self.model,
            timestamp=self.timestamp,
            tags=frozenset(tags),
            metadata=self.metadata
        )
    
    def add_tag(self, tag: str) -> 'ConversationState':
        """Return new state with added tag."""
        new_tags = set(self.tags)
        new_tags.add(tag.strip())
        return self.with_tags(new_tags)
    
    def remove_tag(self, tag: str) -> 'ConversationState':
        """Return new state with removed tag."""
        new_tags = set(self.tags)
        new_tags.discard(tag.strip())
        return self.with_tags(new_tags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'hierarchical_id': self.hierarchical_id,
            'sequence_id': self.sequence_id,
            'parent_id': self.parent_id,
            'message': self.message,
            'response': self.response,
            'model': self.model,
            'timestamp': self.timestamp.isoformat(),
            'tags': list(self.tags),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create state from dictionary."""
        return cls(
            hierarchical_id=data['hierarchical_id'],
            sequence_id=data['sequence_id'],
            parent_id=data.get('parent_id'),
            message=data['message'],
            response=data['response'],
            model=data['model'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            tags=frozenset(data.get('tags', [])),
            metadata=data.get('metadata', {})
        )