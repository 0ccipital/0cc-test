"""Interactive UI components for state selection and tree browsing."""

import sys
import termios
import tty
from typing import Optional, List, Dict, Any
from core.tree import ConversationTree
from core.state import ConversationState
from utils.validators import parse_state_identifier

class InteractiveSelector:
    """Interactive state selector with live preview."""
    
    def __init__(self, tree: ConversationTree):
        self.tree = tree
        self.current_input = ""
    
    def select_state(self) -> Optional[ConversationState]:
        """
        Interactive state selection with live preview.
        Returns selected state or None if cancelled.
        """
        print("\n🔍 Interactive State Selection")
        print("Type state number or ID (ESC to cancel):")
        print("-" * 40)
        
        try:
            while True:
                key = self._get_single_keypress()
                
                if key == '\x1b':  # ESC key
                    print("\nCancelled")
                    return None
                elif key == '\r' or key == '\n':  # Enter key
                    if self.current_input:
                        state = self._get_state_from_input()
                        if state:
                            print(f"\nSelected: {state.display_name}")
                            return state
                        else:
                            print(f"\nInvalid state: {self.current_input}")
                            return None
                    else:
                        print("\nNo input provided")
                        return None
                elif key == '\x7f' or key == '\b':  # Backspace
                    if self.current_input:
                        self.current_input = self.current_input[:-1]
                        self._update_display()
                elif key.isdigit() or key == '.':
                    self.current_input += key
                    self._update_display()
                
        except KeyboardInterrupt:
            print("\nCancelled")
            return None
    
    def _get_single_keypress(self) -> str:
        """Get a single keypress without Enter."""
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            # Fallback for non-TTY environments
            return input()
    
    def _update_display(self):
        """Update the live preview display."""
        # Clear current line and move up
        print(f"\r{' ' * 60}\r", end="")
        
        if self.current_input:
            print(f"Input: {self.current_input}")
            
            # Show preview of matching state
            state = self._get_state_from_input()
            if state:
                preview = self._format_state_preview(state)
                print(f"Preview: {preview}")
            else:
                print("Preview: No matching state")
        else:
            print("Input: ")
            print("Preview: ")
        
        # Move cursor back up
        print("\033[2A", end="")
    
    def _get_state_from_input(self) -> Optional[ConversationState]:
        """Get state from current input."""
        if not self.current_input:
            return None
        
        parsed_id = parse_state_identifier(self.current_input)
        if parsed_id is not None:
            return self.tree.find_state(parsed_id)
        
        return None
    
    def _format_state_preview(self, state: ConversationState) -> str:
        """Format state for preview display."""
        message_preview = state.message[:40] + "..." if len(state.message) > 40 else state.message
        response_preview = state.response[:40] + "..." if len(state.response) > 40 else state.response
        
        tags_display = ""
        if state.tags:
            tags_display = f" [{', '.join(list(state.tags)[:2])}]"
        
        return f"{state.display_name}: {message_preview} → {response_preview}{tags_display}"


class InteractiveTreeBrowser:
    """Interactive tree browser with navigation."""
    
    def __init__(self, tree: ConversationTree):
        self.tree = tree
        self.current_view_state = tree.current_state_id
    
    def browse(self) -> Optional[ConversationState]:
        """
        Interactive tree browser.
        Returns selected state or None if cancelled.
        """
        print("\n🌳 Interactive Tree Browser")
        print("Use arrow keys to navigate, Enter to select, ESC to cancel")
        print("=" * 60)
        
        try:
            while True:
                self._display_tree_view()
                key = self._get_single_keypress()
                
                if key == '\x1b':  # ESC key
                    print("\nCancelled")
                    return None
                elif key == '\r' or key == '\n':  # Enter key
                    if self.current_view_state:
                        state = self.tree.find_state(self.current_view_state)
                        if state:
                            print(f"\nSelected: {state.display_name}")
                            return state
                elif key == 'q':  # Quit
                    print("\nCancelled")
                    return None
                elif key in ['j', '\x1b[B']:  # Down arrow or j
                    self._navigate_down()
                elif key in ['k', '\x1b[A']:  # Up arrow or k
                    self._navigate_up()
                elif key in ['h', '\x1b[D']:  # Left arrow or h
                    self._navigate_left()
                elif key in ['l', '\x1b[C']:  # Right arrow or l
                    self._navigate_right()
                
        except KeyboardInterrupt:
            print("\nCancelled")
            return None
    
    def _get_single_keypress(self) -> str:
        """Get a single keypress without Enter."""
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                # Handle arrow keys (they send multiple characters)
                if key == '\x1b':
                    key += sys.stdin.read(2)
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            return input()
    
    def _display_tree_view(self):
        """Display current tree view with highlighting."""
        # Clear screen area
        print("\033[H\033[J", end="")
        
        print("🌳 Interactive Tree Browser")
        print("Use j/k (or ↑↓) to navigate, h/l (or ←→) for parent/child, Enter to select, ESC/q to cancel")
        print("=" * 60)
        
        if self.tree.state_count == 0:
            print("No conversation states yet.")
            return
        
        # Display tree with current selection highlighted
        self._render_tree_with_highlight()
        
        # Show current state details
        if self.current_view_state:
            current_state = self.tree.find_state(self.current_view_state)
            if current_state:
                print("\n" + "─" * 60)
                print(f"Selected: {current_state.display_name}")
                print(f"Message: {current_state.message}")
                print(f"Response: {current_state.response[:100]}...")
                if current_state.tags:
                    print(f"Tags: {', '.join(current_state.tags)}")
    
    def _render_tree_with_highlight(self):
        """Render tree with current selection highlighted."""
        all_states = self.tree.get_all_states()
        roots = [s for s in all_states if s.is_root]
        
        for root in roots:
            self._render_state_node(root, "", True, 0)
    
    def _render_state_node(self, state: ConversationState, prefix: str, is_last: bool, depth: int):
        """Render a single state node with highlighting."""
        # Determine if this state is currently selected
        is_selected = state.hierarchical_id == self.current_view_state
        
        # Create tree prefix
        if depth == 0:
            tree_prefix = ""
        else:
            tree_prefix = prefix + ("└── " if is_last else "├── ")
        
        # Format state display
        message_preview = state.message[:40] + "..." if len(state.message) > 40 else state.message
        
        # Highlight selected state
        if is_selected:
            line = f"{tree_prefix}► {state.display_name}: {message_preview}"
            print(f"\033[7m{line}\033[0m")  # Reverse video
        else:
            line = f"{tree_prefix}  {state.display_name}: {message_preview}"
            print(line)
        
        # Render children
        children = self.tree.get_children(state.hierarchical_id)
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            child_prefix = prefix + ("    " if is_last else "│   ")
            self._render_state_node(child, child_prefix, is_last_child, depth + 1)
    
    def _navigate_down(self):
        """Navigate to next state in tree order."""
        all_states = self.tree.get_all_states()
        if not all_states:
            return
        
        if not self.current_view_state:
            self.current_view_state = all_states[0].hierarchical_id
            return
        
        # Find current state index and move to next
        current_index = None
        for i, state in enumerate(all_states):
            if state.hierarchical_id == self.current_view_state:
                current_index = i
                break
        
        if current_index is not None and current_index < len(all_states) - 1:
            self.current_view_state = all_states[current_index + 1].hierarchical_id
    
    def _navigate_up(self):
        """Navigate to previous state in tree order."""
        all_states = self.tree.get_all_states()
        if not all_states:
            return
        
        if not self.current_view_state:
            self.current_view_state = all_states[-1].hierarchical_id
            return
        
        # Find current state index and move to previous
        current_index = None
        for i, state in enumerate(all_states):
            if state.hierarchical_id == self.current_view_state:
                current_index = i
                break
        
        if current_index is not None and current_index > 0:
            self.current_view_state = all_states[current_index - 1].hierarchical_id
    
    def _navigate_left(self):
        """Navigate to parent state."""
        if not self.current_view_state:
            return
        
        current_state = self.tree.find_state(self.current_view_state)
        if current_state and current_state.parent_id:
            self.current_view_state = current_state.parent_id
    
    def _navigate_right(self):
        """Navigate to first child state."""
        if not self.current_view_state:
            return
        
        children = self.tree.get_children(self.current_view_state)
        if children:
            self.current_view_state = children[0].hierarchical_id


class TagSelector:
    """Interactive tag selector with suggestions."""
    
    def __init__(self, recent_tags: List[str] = None):
        self.recent_tags = recent_tags or []
    
    def select_tag(self, current_tags: List[str]) -> Optional[str]:
        """
        Interactive tag selection with suggestions.
        Returns selected tag or None if cancelled.
        """
        print("\n🏷️  Tag Selection")
        print("Recent tags:")
        
        if self.recent_tags:
            for i, tag in enumerate(self.recent_tags[:5], 1):
                marker = "✓" if tag in current_tags else " "
                print(f"  {i}. [{marker}] {tag}")
        else:
            print("  No recent tags")
        
        print("\nOptions:")
        print("  [1-5] Select recent tag")
        print("  [text] Enter custom tag")
        print("  [Enter] Cancel")
        
        try:
            user_input = input("\nYour choice: ").strip()
            
            if not user_input:
                return None
            
            # Check if it's a number for recent tag selection
            try:
                tag_index = int(user_input)
                if 1 <= tag_index <= len(self.recent_tags):
                    return self.recent_tags[tag_index - 1]
            except ValueError:
                pass
            
            # Treat as custom tag
            return user_input
            
        except (EOFError, KeyboardInterrupt):
            return None


class LoadSelector:
    """Interactive conversation loader."""
    
    def __init__(self, conversations: List[Dict[str, str]]):
        self.conversations = conversations
    
    def select_conversation(self) -> Optional[str]:
        """
        Interactive conversation selection.
        Returns filename or None if cancelled.
        """
        if not self.conversations:
            print("No saved conversations found.")
            return None
        
        print("\n📁 Load Conversation")
        print("Available conversations:")
        print("-" * 60)
        
        for i, conv in enumerate(self.conversations, 1):
            print(f"  {i}. {conv['name']}")
            print(f"     Saved: {conv['saved_at'][:19]} | States: {conv['state_count']} | Size: {conv['size']}")
            print()
        
        try:
            choice = input(f"Select conversation (1-{len(self.conversations)}) or Enter to cancel: ").strip()
            
            if not choice:
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(self.conversations):
                return self.conversations[choice_num - 1]['filename']
            else:
                print(f"Invalid choice: {choice}")
                return None
                
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None
        except (EOFError, KeyboardInterrupt):
            return None