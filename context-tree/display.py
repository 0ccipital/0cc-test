"""Enhanced visualization and UI formatting for the context tree."""

import shutil
from typing import Dict, List, Optional
from datetime import datetime
import tags

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

class TreeDisplay:
    def __init__(self):
        self.terminal_width = self._get_terminal_width()
    
    def _get_terminal_width(self) -> int:
        """Get terminal width, default to 80 if can't determine."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def render_tree(self, tree_data: Dict, current_state_id: str, mode: str = 'horizontal') -> str:
        """Render the conversation tree."""
        if not tree_data:
            return f"{Colors.GRAY}No conversation states yet.{Colors.RESET}"
        
        if mode == 'horizontal':
            return self._render_horizontal_tree(tree_data, current_state_id)
        else:
            return self._render_vertical_tree(tree_data, current_state_id)
    
    def _render_horizontal_tree(self, tree_data: Dict, current_state_id: str) -> str:
        """Render tree as horizontal branching paths."""
        from tree import ContextTree
        
        # Create temporary tree object to use path methods
        temp_tree = ContextTree()
        temp_tree.states = tree_data
        temp_tree.current_state_id = current_state_id
        
        paths = temp_tree.get_all_paths_from_root()
        lines = []
        
        for path in paths:
            line = self._format_path(path, tree_data, current_state_id)
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _format_path(self, path: List[str], tree_data: Dict, current_state_id: str) -> str:
        """Format a single path for horizontal display."""
        parts = []
        
        for i, state_id in enumerate(path):
            state = tree_data[state_id]
            
            # Format state display
            state_display = self._format_state_for_path(state, state_id == current_state_id)
            parts.append(state_display)
            
            # Add arrow if not last
            if i < len(path) - 1:
                parts.append(f" {Colors.GRAY}→{Colors.RESET} ")
        
        return ''.join(parts)
    
    def _format_state_for_path(self, state: Dict, is_current: bool) -> str:
        """Format a single state for path display."""
        state_id = state['id']
        message = state['message']
        
        # Truncate message for display
        max_msg_len = 35
        if len(message) > max_msg_len:
            message = message[:max_msg_len] + "..."
        
        # Get tag display
        tag_display = ""
        if state.get('tags'):
            tag_emojis = [tags.get_tag_display(tag) for tag in state['tags']]
            tag_display = " " + "".join(tag_emojis)
        
        # Color based on current state and tags
        if is_current:
            color = Colors.CYAN + Colors.BOLD
            marker = " ← current"
        else:
            color = Colors.WHITE
            marker = ""
        
        # Add branch indicator for branches
        branch_indicator = ""
        if state.get('is_branch', False):
            branch_indicator = f" {Colors.YELLOW}⚡{Colors.RESET}"
        
        return f"{color}{state_id}:{Colors.RESET} {message}{tag_display}{branch_indicator}{Colors.CYAN if is_current else ''}{marker}{Colors.RESET}"
    
    def _render_vertical_tree(self, tree_data: Dict, current_state_id: str) -> str:
        """Render tree in vertical format with proper branching."""
        # Find root states
        roots = [state for state in tree_data.values() if state["parent_id"] is None]
        
        if not roots:
            return f"{Colors.GRAY}No conversation states yet.{Colors.RESET}"
        
        lines = []
        for root in roots:
            self._render_vertical_node(root['id'], tree_data, current_state_id, lines, "", True)
        
        return '\n'.join(lines)
    
    def _render_vertical_node(self, state_id: str, tree_data: Dict, current_state_id: str, 
                             lines: List[str], prefix: str, is_last: bool):
        """Recursively render a node in vertical format."""
        state = tree_data[state_id]
        
        # Create tree prefix
        if not prefix:
            tree_prefix = ""
        else:
            tree_prefix = prefix + ("└── " if is_last else "├── ")
        
        # Format message
        message = state['message']
        if len(message) > 45:
            message = message[:45] + "..."
        
        # Get tag display
        tag_display = ""
        if state.get('tags'):
            tag_emojis = [tags.get_tag_display(tag) for tag in state['tags']]
            tag_display = " " + "".join(tag_emojis)
        
        # Current state marker
        current_marker = f" {Colors.CYAN}← CURRENT{Colors.RESET}" if state_id == current_state_id else ""
        
        # Branch indicator
        branch_indicator = f" {Colors.YELLOW}🌿{Colors.RESET}" if state.get('is_branch', False) else ""
        
        line = f"{tree_prefix}{Colors.CYAN}{state_id}:{Colors.RESET} {message}{tag_display}{branch_indicator}{current_marker}"
        lines.append(line)
        
        # Render children
        children = state.get('children', [])
        for i, child_id in enumerate(children):
            is_last_child = i == len(children) - 1
            child_prefix = prefix + ("    " if is_last else "│   ")
            self._render_vertical_node(child_id, tree_data, current_state_id, lines, child_prefix, is_last_child)
    
    def render_branch_points(self, branch_points: List[Dict], show_tags: bool = True) -> str:
        """Render branch points for selection."""
        if not branch_points:
            return f"{Colors.GRAY}No branch points found.{Colors.RESET}"
        
        lines = [f"{Colors.BOLD}📍 Branch Points (states with multiple paths):{Colors.RESET}"]
        lines.append("")
        
        for i, state in enumerate(branch_points, 1):
            # Format message preview
            message = state['message']
            if len(message) > 40:
                message = message[:40] + "..."
            
            # Get tag display
            tag_display = ""
            if show_tags and state.get('tags'):
                tag_emojis = [tags.get_tag_display(tag) for tag in state['tags']]
                tag_display = " " + "".join(tag_emojis)
            
            # Timestamp
            timestamp = datetime.fromisoformat(state['timestamp']).strftime("%H:%M:%S")
            
            # Children count
            child_count = len(state.get('children', []))
            
            line = f"  {Colors.CYAN}{i}.{Colors.RESET} {Colors.BOLD}{state['id']}{Colors.RESET}: {message}{tag_display} {Colors.GRAY}[{timestamp}, {child_count} branches]{Colors.RESET}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def render_comparison(self, state1: Dict, state2: Dict) -> str:
        """Render side-by-side comparison of two states."""
        lines = [f"{Colors.BOLD}🔍 Branch Comparison:{Colors.RESET}"]
        lines.append("=" * min(60, self.terminal_width))
        
        # State info
        lines.append(f"{Colors.CYAN}State A: {state1['id']}{Colors.RESET} | {Colors.CYAN}State B: {state2['id']}{Colors.RESET}")
        lines.append("")
        
        # Messages
        lines.append(f"{Colors.YELLOW}User Message:{Colors.RESET}")
        lines.append(f"A: {state1['message']}")
        lines.append(f"B: {state2['message']}")
        lines.append("")
        
        # Responses (truncated)
        lines.append(f"{Colors.GREEN}Assistant Response:{Colors.RESET}")
        resp1 = state1['response'][:100] + "..." if len(state1['response']) > 100 else state1['response']
        resp2 = state2['response'][:100] + "..." if len(state2['response']) > 100 else state2['response']
        lines.append(f"A: {resp1}")
        lines.append(f"B: {resp2}")
        lines.append("")
        
        # Tags
        tags1 = state1.get('tags', [])
        tags2 = state2.get('tags', [])
        if tags1 or tags2:
            lines.append(f"{Colors.MAGENTA}Tags:{Colors.RESET}")
            tags1_display = " ".join([tags.get_tag_display(tag) for tag in tags1]) if tags1 else "None"
            tags2_display = " ".join([tags.get_tag_display(tag) for tag in tags2]) if tags2 else "None"
            lines.append(f"A: {tags1_display}")
            lines.append(f"B: {tags2_display}")
        
        return '\n'.join(lines)
    
    def render_state_line(self, state: Dict, show_full: bool = False) -> str:
        """Render a single state line."""
        state_id = state['id']
        message = state['message'] if show_full else (state['message'][:50] + "..." if len(state['message']) > 50 else state['message'])
        
        # Get tag display
        tag_display = ""
        if state.get('tags'):
            tag_emojis = [tags.get_tag_display(tag) for tag in state['tags']]
            tag_display = " " + "".join(tag_emojis)
        
        # Timestamp
        timestamp = datetime.fromisoformat(state['timestamp']).strftime("%H:%M:%S")
        
        return f"{Colors.CYAN}{state_id}:{Colors.RESET} {message}{tag_display} {Colors.GRAY}[{timestamp}]{Colors.RESET}"
    
    def prompt_for_revert_choice(self, branch_points: List[Dict]) -> Optional[str]:
        """Interactive prompt for revert choice."""
        if not branch_points:
            return None
        
        print(self.render_branch_points(branch_points))
        print()
        
        while True:
            try:
                choice = input(f"{Colors.BOLD}Select state to revert to (1-{len(branch_points)}) or 'c' to cancel:{Colors.RESET} ").strip()
                
                if choice.lower() == 'c':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(branch_points):
                    return branch_points[choice_num - 1]['id']
                else:
                    print(f"{Colors.RED}❌ Please enter a number between 1 and {len(branch_points)}{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Please enter a valid number or 'c' to cancel{Colors.RESET}")
            except (EOFError, KeyboardInterrupt):
                return None
    
    def prompt_for_tag(self, current_tags: List[str]) -> Optional[str]:
        """Interactive prompt for tagging."""
        print(f"\n{Colors.BOLD}🏷️  Quick Tag Options:{Colors.RESET}")
        print(tags.get_tag_help())
        print(f"  [Enter] Skip tagging")
        
        current_display = ", ".join([tags.get_tag_display(tag) for tag in current_tags]) if current_tags else "None"
        print(f"\nCurrent tags: {current_display}")
        
        try:
            choice = input(f"{Colors.BOLD}Select tag:{Colors.RESET} ").strip().lower()
            
            if not choice:
                return None
            
            return tags.parse_quick_tag(choice)
        except (EOFError, KeyboardInterrupt):
            return None
    
    def show_success(self, message: str):
        """Show success message."""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    
    def show_error(self, message: str):
        """Show error message."""
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    
    def show_info(self, message: str):
        """Show info message."""
        print(f"{Colors.BLUE}💡 {message}{Colors.RESET}")
    
    def show_warning(self, message: str):
        """Show warning message."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    
    def print_separator(self, char: str = "═", color: str = Colors.BLUE):
        """Print a separator line."""
        print(f"{color}{char * self.terminal_width}{Colors.RESET}")
    
    def print_header(self, title: str):
        """Print application header."""
        self.print_separator("═", Colors.CYAN)
        padding = (self.terminal_width - len(title)) // 2
        print(f"{Colors.CYAN}{Colors.BOLD}{' ' * padding}{title}{Colors.RESET}")
        self.print_separator("═", Colors.CYAN)