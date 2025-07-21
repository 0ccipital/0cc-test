"""Core tree operations and state management."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import tags

class ContextTree:
    def __init__(self):
        self.states: Dict[str, Dict] = {}
        self.current_state_id: Optional[str] = None
        self.global_counter = 0
        
    def _generate_state_id(self, parent_id: Optional[str] = None) -> str:
        """Generate a state ID that reflects tree structure."""
        self.global_counter += 1
        
        if parent_id is None:
            return f"state_{self.global_counter}"
        
        parent_state = self.states.get(parent_id)
        if parent_state:
            existing_children = len(parent_state["children"])
            if existing_children == 0:
                return f"state_{self.global_counter}"
            else:
                branch_letter = chr(ord('a') + existing_children - 1)
                return f"state_{self.global_counter}_{branch_letter}"
        
        return f"state_{self.global_counter}"
    
    def create_state(self, message: str, response: str, model: str, parent_id: Optional[str] = None) -> str:
        """Create a new conversation state."""
        state_id = self._generate_state_id(parent_id)
        
        # Calculate depth
        depth = 0
        if parent_id and parent_id in self.states:
            depth = self.states[parent_id]["depth"] + 1
        
        # Determine if this creates a branch
        is_branch = False
        if parent_id and parent_id in self.states:
            parent_children = self.states[parent_id]["children"]
            if len(parent_children) > 0:
                is_branch = True
        
        # Create state
        state = {
            'id': state_id,
            'parent_id': parent_id,
            'children': [],
            'message': message,
            'response': response,
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'tags': [],
            'is_branch_point': False,  # Will be updated when children are added
            'depth': depth,
            'creation_order': self.global_counter,
            'is_branch': is_branch
        }
        
        self.states[state_id] = state
        
        # Update parent
        if parent_id and parent_id in self.states:
            self.states[parent_id]["children"].append(state_id)
            # Update parent's branch point status
            self.states[parent_id]["is_branch_point"] = len(self.states[parent_id]["children"]) > 1
        
        self.current_state_id = state_id
        return state_id
    
    def revert_to_state(self, state_id: str) -> bool:
        """Revert to a previous state."""
        if state_id not in self.states:
            return False
        
        self.current_state_id = state_id
        return True
    
    def get_current_state(self) -> Optional[Dict]:
        """Get the current state data."""
        if self.current_state_id:
            return self.states.get(self.current_state_id)
        return None
    
    def get_branch_points(self) -> List[Dict]:
        """Get states where conversation branched (multiple children)."""
        branch_points = []
        for state in self.states.values():
            if state.get('is_branch_point', False):
                branch_points.append(state)
        
        # Sort by creation order
        branch_points.sort(key=lambda x: x['creation_order'])
        return branch_points
    
    def get_children(self, state_id: str) -> List[str]:
        """Get children of a state."""
        if state_id in self.states:
            return self.states[state_id]["children"].copy()
        return []
    
    def get_path_to_state(self, state_id: str) -> List[str]:
        """Get path from root to a specific state."""
        if state_id not in self.states:
            return []
        
        path = []
        current = state_id
        while current:
            path.insert(0, current)
            current = self.states[current]["parent_id"]
        return path
    
    def get_sibling_states(self, state_id: str) -> List[str]:
        """Get sibling states (same parent)."""
        if state_id not in self.states:
            return []
        
        state = self.states[state_id]
        parent_id = state["parent_id"]
        
        if not parent_id:
            return []  # Root state has no siblings
        
        siblings = self.get_children(parent_id)
        return [s for s in siblings if s != state_id]
    
    def get_all_paths_from_root(self) -> List[List[str]]:
        """Get all paths from root states to leaf states."""
        paths = []
        
        # Find root states
        roots = [state_id for state_id, state in self.states.items() 
                if state["parent_id"] is None]
        
        for root in roots:
            self._collect_paths(root, [root], paths)
        
        return paths
    
    def _collect_paths(self, state_id: str, current_path: List[str], all_paths: List[List[str]]):
        """Recursively collect all paths from a state."""
        children = self.get_children(state_id)
        
        if not children:
            # Leaf node - add this path
            all_paths.append(current_path.copy())
        else:
            # Continue down each child
            for child in children:
                new_path = current_path + [child]
                self._collect_paths(child, new_path, all_paths)
    
    def save_to_file(self, filename: str) -> bool:
        """Save conversation tree to file."""
        try:
            data = {
                'states': self.states,
                'current_state_id': self.current_state_id,
                'global_counter': self.global_counter,
                'saved_at': datetime.now().isoformat()
            }
            
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Load conversation tree from file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.states = data.get('states', {})
            self.current_state_id = data.get('current_state_id')
            self.global_counter = data.get('global_counter', 0)
            
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def get_conversation_messages(self, state_id: Optional[str] = None) -> List[Dict]:
        """Get conversation messages up to a specific state."""
        if state_id is None:
            state_id = self.current_state_id
        
        if not state_id or state_id not in self.states:
            return []
        
        path = self.get_path_to_state(state_id)
        messages = []
        
        for state_id in path:
            state = self.states[state_id]
            messages.append({"role": "user", "content": state["message"]})
            messages.append({"role": "assistant", "content": state["response"]})
        
        return messages