"""Save/load operations for conversation trees."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from core.tree import ConversationTree
from utils.errors import PersistenceError
from utils.validators import validate_filename

class ConversationPersistence:
    """Handle saving and loading conversation trees."""
    
    def __init__(self, save_directory: Path = None):
        self.save_directory = save_directory or Path.home() / ".ollama_conversations" / "trees"
        self.save_directory.mkdir(parents=True, exist_ok=True)
    
    def save_conversation(self, tree: ConversationTree, name: Optional[str] = None) -> str:
        """
        Save conversation tree to file.
        
        Args:
            tree: ConversationTree to save
            name: Optional custom name, otherwise auto-generated
            
        Returns:
            str: Filename that was saved
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"conversation_{timestamp}"
        
        if not validate_filename(name):
            raise PersistenceError(f"Invalid filename: {name}")
        
        # Ensure .json extension
        if not name.endswith('.json'):
            name += '.json'
        
        filepath = self.save_directory / name
        
        try:
            # Prepare data with metadata
            data = tree.to_dict()
            data['metadata'].update({
                'saved_at': datetime.now().isoformat(),
                'filename': name,
                'version': '2.0.0'
            })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return name
            
        except Exception as e:
            raise PersistenceError(f"Failed to save conversation: {e}")
    
    def load_conversation(self, filename: str) -> ConversationTree:
        """
        Load conversation tree from file.
        
        Args:
            filename: Name of file to load
            
        Returns:
            ConversationTree: Loaded tree
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.save_directory / filename
        
        if not filepath.exists():
            raise PersistenceError(f"File not found: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ConversationTree.from_dict(data)
            
        except json.JSONDecodeError as e:
            raise PersistenceError(f"Invalid JSON in file {filename}: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to load conversation: {e}")
    
    def list_conversations(self) -> List[Dict[str, str]]:
        """
        List all saved conversations with metadata.
        
        Returns:
            List of dictionaries with conversation info
        """
        conversations = []
        
        for filepath in self.save_directory.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                conversations.append({
                    'filename': filepath.name,
                    'name': filepath.stem,
                    'saved_at': metadata.get('saved_at', 'Unknown'),
                    'state_count': metadata.get('state_count', 0),
                    'size': f"{filepath.stat().st_size / 1024:.1f} KB"
                })
                
            except Exception:
                # Skip corrupted files
                continue
        
        # Sort by saved_at descending
        conversations.sort(key=lambda x: x['saved_at'], reverse=True)
        return conversations
    
    def delete_conversation(self, filename: str) -> bool:
        """
        Delete saved conversation.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            bool: True if deleted successfully
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.save_directory / filename
        
        try:
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception as e:
            raise PersistenceError(f"Failed to delete conversation: {e}")
    
    def get_save_directory(self) -> Path:
        """Get the save directory path."""
        return self.save_directory