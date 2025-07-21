"""Tree navigation logic and utilities."""

from typing import List, Optional, Union, Tuple
from core.tree import ConversationTree
from core.state import ConversationState
from utils.errors import NavigationError, StateNotFoundError

class TreeNavigator:
    """Handles tree navigation operations."""
    
    def __init__(self, tree: ConversationTree):
        self.tree = tree
    
    def go_to_state(self, identifier: Union[int, str]) -> ConversationState:
        """Navigate to specified state with error handling."""
        if not self.tree.navigate_to(identifier):
            # Provide helpful suggestions
            suggestions = self._get_navigation_suggestions(identifier)
            raise NavigationError(
                f"Cannot navigate to '{identifier}'",
                suggestions=suggestions
            )
        
        current = self.tree.current_state
        if not current:
            raise NavigationError("Navigation failed - no current state")
        
        return current
    
    def go_up(self) -> Optional[ConversationState]:
        """Navigate to parent state."""
        current = self.tree.current_state
        if not current:
            raise NavigationError("No current state")
        
        if current.is_root:
            raise NavigationError("Already at root state")
        
        parent = self.tree.get_parent(current.hierarchical_id)
        if not parent:
            raise NavigationError("Parent state not found")
        
        self.tree.navigate_to(parent.hierarchical_id)
        return parent
    
    def go_down(self, branch_index: int) -> ConversationState:
        """Navigate to specific child branch."""
        current = self.tree.current_state
        if not current:
            raise NavigationError("No current state")
        
        children = self.tree.get_children(current.hierarchical_id)
        if not children:
            raise NavigationError("No child states available")
        
        if branch_index < 1 or branch_index > len(children):
            raise NavigationError(
                f"Invalid branch index {branch_index}. Available: 1-{len(children)}"
            )
        
        target_child = children[branch_index - 1]
        self.tree.navigate_to(target_child.hierarchical_id)
        return target_child
    
    def get_navigation_context(self) -> dict:
        """Get current navigation context for UI."""
        current = self.tree.current_state
        if not current:
            return {'current': None, 'parent': None, 'children': [], 'siblings': []}
        
        return {
            'current': current,
            'parent': self.tree.get_parent(current.hierarchical_id),
            'children': self.tree.get_children(current.hierarchical_id),
            'siblings': self.tree.get_siblings(current.hierarchical_id),
            'path_to_root': self.tree.get_path_to_root(current.hierarchical_id)
        }
    
    def _get_navigation_suggestions(self, identifier: Union[int, str]) -> List[str]:
        """Get navigation suggestions for invalid identifiers."""
        suggestions = []
        
        # Get all valid identifiers
        all_states = self.tree.get_all_states()
        
        if isinstance(identifier, int):
            # Suggest nearby sequence numbers
            valid_sequences = [s.sequence_id for s in all_states]
            close_sequences = [s for s in valid_sequences if abs(s - identifier) <= 2]
            suggestions.extend([f"Try sequence {s}" for s in close_sequences[:3]])
        
        elif isinstance(identifier, str):
            # Suggest similar hierarchical IDs
            valid_hierarchical = [s.hierarchical_id for s in all_states]
            # Simple string similarity
            similar = [h for h in valid_hierarchical if identifier in h or h in identifier]
            suggestions.extend([f"Try '{h}'" for h in similar[:3]])
        
        # Always suggest viewing the tree
        suggestions.append("Use '/states' to see all available states")
        
        return suggestions