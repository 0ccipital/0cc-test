"""Professional tree implementation for conversation management."""

from typing import Dict, List, Optional, Union, Set
from collections import defaultdict, deque
from datetime import datetime

from core.state import ConversationState
from utils.errors import StateNotFoundError, NavigationError, TreeOperationError
from utils.validators import validate_state_identifier, parse_state_identifier

class ConversationTree:
    """
    Efficient tree implementation with multiple indexing strategies.
    Supports O(1) lookups by sequence ID and hierarchical ID.
    """
    
    def __init__(self):
        self._states: Dict[str, ConversationState] = {}
        self._sequence_index: Dict[int, str] = {}        # sequence -> hierarchical_id
        self._hierarchy_index: Dict[str, int] = {}       # hierarchical_id -> sequence
        self._parent_children: Dict[str, List[str]] = defaultdict(list)  # parent -> children
        self._current_state: Optional[str] = None
        self._sequence_counter: int = 0
        
    @property
    def current_state_id(self) -> Optional[str]:
        """Get current state hierarchical ID."""
        return self._current_state
    
    @property
    def current_state(self) -> Optional[ConversationState]:
        """Get current state object."""
        if self._current_state:
            return self._states.get(self._current_state)
        return None
    
    @property
    def state_count(self) -> int:
        """Get total number of states."""
        return len(self._states)
    
    def add_state(self, parent_id: Optional[str], message: str, response: str, model: str) -> ConversationState:
        """Add new state to tree with proper indexing."""
        self._sequence_counter += 1
        
        # Generate hierarchical ID
        if parent_id is None:
            hierarchical_id = str(self._sequence_counter)
        else:
            if parent_id not in self._states:
                raise StateNotFoundError(parent_id)
            
            # Count existing children to determine branch index
            children_count = len(self._parent_children[parent_id])
            hierarchical_id = f"{parent_id}.{children_count + 1}"
        
        # Create new state
        state = ConversationState(
            hierarchical_id=hierarchical_id,
            sequence_id=self._sequence_counter,
            parent_id=parent_id,
            message=message,
            response=response,
            model=model,
            timestamp=datetime.now()
        )
        
        # Update all indexes
        self._states[hierarchical_id] = state
        self._sequence_index[self._sequence_counter] = hierarchical_id
        self._hierarchy_index[hierarchical_id] = self._sequence_counter
        
        if parent_id:
            self._parent_children[parent_id].append(hierarchical_id)
        
        # Set as current state
        self._current_state = hierarchical_id
        
        return state
    
    def find_state(self, identifier: Union[int, str]) -> Optional[ConversationState]:
        """Find state by sequence ID or hierarchical ID."""
        if isinstance(identifier, int):
            hierarchical_id = self._sequence_index.get(identifier)
            if hierarchical_id:
                return self._states.get(hierarchical_id)
        elif isinstance(identifier, str):
            return self._states.get(identifier)
        
        return None
    
    def navigate_to(self, identifier: Union[int, str]) -> bool:
        """Navigate to specified state."""
        # Parse and validate identifier
        parsed_id = parse_state_identifier(str(identifier)) if isinstance(identifier, str) else identifier
        if parsed_id is None:
            return False
        
        state = self.find_state(parsed_id)
        if state:
            self._current_state = state.hierarchical_id
            return True
        
        return False
    
    def get_children(self, state_id: str) -> List[ConversationState]:
        """Get children of specified state."""
        children_ids = self._parent_children.get(state_id, [])
        return [self._states[child_id] for child_id in children_ids if child_id in self._states]
    
    def get_parent(self, state_id: str) -> Optional[ConversationState]:
        """Get parent of specified state."""
        state = self._states.get(state_id)
        if state and state.parent_id:
            return self._states.get(state.parent_id)
        return None
    
    def get_siblings(self, state_id: str) -> List[ConversationState]:
        """Get sibling states (same parent)."""
        state = self._states.get(state_id)
        if not state or not state.parent_id:
            return []
        
        siblings = self.get_children(state.parent_id)
        return [s for s in siblings if s.hierarchical_id != state_id]
    
    def get_path_to_root(self, state_id: str) -> List[ConversationState]:
        """Get path from specified state to root."""
        path = []
        current_id = state_id
        
        while current_id and current_id in self._states:
            state = self._states[current_id]
            path.insert(0, state)
            current_id = state.parent_id
        
        return path
    
    def get_subtree(self, state_id: str) -> List[ConversationState]:
        """Get all descendants of specified state."""
        if state_id not in self._states:
            return []
        
        subtree = []
        queue = deque([state_id])
        
        while queue:
            current_id = queue.popleft()
            if current_id in self._states:
                subtree.append(self._states[current_id])
                children_ids = self._parent_children.get(current_id, [])
                queue.extend(children_ids)
        
        return subtree
    
    def get_all_states(self) -> List[ConversationState]:
        """Get all states sorted by sequence ID."""
        return [self._states[self._sequence_index[seq]] 
                for seq in sorted(self._sequence_index.keys())]
    
    def get_root_states(self) -> List[ConversationState]:
        """Get all root states."""
        return [state for state in self._states.values() if state.is_root]
    
    def update_state(self, state_id: str, updated_state: ConversationState) -> bool:
        """Update existing state (for tagging, etc.)."""
        if state_id not in self._states:
            return False
        
        # Ensure hierarchical_id consistency
        if updated_state.hierarchical_id != state_id:
            return False
        
        self._states[state_id] = updated_state
        return True
    
    def get_conversation_messages(self, state_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get conversation messages up to specified state for LLM context."""
        if state_id is None:
            state_id = self._current_state
        
        if not state_id:
            return []
        
        path = self.get_path_to_root(state_id)
        messages = []
        
        for state in path:
            messages.append({"role": "user", "content": state.message})
            messages.append({"role": "assistant", "content": state.response})
        
        return messages
    
    def clear(self) -> None:
        """Clear all states and reset tree."""
        self._states.clear()
        self._sequence_index.clear()
        self._hierarchy_index.clear()
        self._parent_children.clear()
        self._current_state = None
        self._sequence_counter = 0
    
    def to_dict(self) -> Dict:
        """Convert tree to dictionary for serialization."""
        return {
            'states': {state_id: state.to_dict() for state_id, state in self._states.items()},
            'current_state': self._current_state,
            'sequence_counter': self._sequence_counter,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'state_count': len(self._states)
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationTree':
        """Create tree from dictionary."""
        tree = cls()
        tree._sequence_counter = data.get('sequence_counter', 0)
        tree._current_state = data.get('current_state')
        
        # Rebuild states and indexes
        states_data = data.get('states', {})
        for state_id, state_data in states_data.items():
            state = ConversationState.from_dict(state_data)
            tree._states[state_id] = state
            tree._sequence_index[state.sequence_id] = state_id
            tree._hierarchy_index[state_id] = state.sequence_id
            
            # Rebuild parent-children relationships
            if state.parent_id:
                tree._parent_children[state.parent_id].append(state_id)
        
        return tree