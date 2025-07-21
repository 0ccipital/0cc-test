"""Tree visualization and rendering utilities."""

from typing import List, Dict, Optional
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel

from core.tree import ConversationTree
from core.state import ConversationState

class TreeRenderer:
    """Professional tree rendering with Rich library."""
    
    def __init__(self):
        self.console = Console()
    
    def render_tree(self, tree: ConversationTree, highlight_current: bool = True) -> str:
        """Render conversation tree with Rich formatting."""
        if tree.state_count == 0:
            return "No conversation states yet."
        
        # Create Rich tree
        rich_tree = Tree("🌳 Conversation Tree")
        
        # Get root states
        roots = tree.get_root_states()
        
        for root in roots:
            self._add_state_to_tree(tree, rich_tree, root, highlight_current)
        
        # Capture output
        with self.console.capture() as capture:
            self.console.print(rich_tree)
        
        return capture.get()
    
    def _add_state_to_tree(self, tree: ConversationTree, parent_node, state: ConversationState, highlight_current: bool):
        """Recursively add state and children to Rich tree."""
        # Format state display
        display_text = self._format_state_display(state, tree.current_state_id if highlight_current else None)
        
        # Add to tree
        state_node = parent_node.add(display_text)
        
        # Add children
        children = tree.get_children(state.hierarchical_id)
        for child in children:
            self._add_state_to_tree(tree, state_node, child, highlight_current)
    
    def _format_state_display(self, state: ConversationState, current_state_id: Optional[str]) -> Text:
        """Format state for display with colors and styling."""
        text = Text()
        
        # State ID with styling
        if state.hierarchical_id == current_state_id:
            text.append(f"{state.display_name}", style="bold cyan")
            text.append(" ← current", style="bright_cyan")
        else:
            text.append(f"{state.display_name}", style="cyan")
        
        text.append(": ")
        
        # Message preview
        message_preview = state.message[:40] + "..." if len(state.message) > 40 else state.message
        text.append(message_preview, style="white")
        
        # Tags
        if state.tags:
            text.append(" ")
            for tag in list(state.tags)[:3]:  # Show max 3 tags
                text.append(f"[{tag}]", style="yellow")
        
        # Branch indicator
        if state.hierarchical_id != state.sequence_id:  # It's a branch
            text.append(" 🌿", style="yellow")
        
        return text
    
    def render_state_summary(self, states: List[ConversationState], current_state_id: Optional[str]) -> str:
        """Render state summary table."""
        if not states:
            return "No states to display."
        
        # Create table-like output
        lines = []
        lines.append("📊 State Summary")
        lines.append("─" * 60)
        
        for state in states:
            current_marker = " ← current" if state.hierarchical_id == current_state_id else ""
            
            # Format line
            timestamp = state.timestamp.strftime("%H:%M:%S")
            message_preview = state.message[:35] + "..." if len(state.message) > 35 else state.message
            
            tags_display = ""
            if state.tags:
                tags_display = f" [{', '.join(list(state.tags)[:2])}]"
            
            line = f"  {state.display_name}: {message_preview}{tags_display} [{timestamp}]{current_marker}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def render_navigation_context(self, nav_context: Dict) -> str:
        """Render current navigation context."""
        current = nav_context.get('current')
        if not current:
            return "No current state."
        
        lines = []
        lines.append(f"📍 Current: {current.display_name}")
        
        # Parent info
        parent = nav_context.get('parent')
        if parent:
            lines.append(f"⬆️  Parent: {parent.display_name}")
        else:
            lines.append("⬆️  Parent: None (root)")
        
        # Children info
        children = nav_context.get('children', [])
        if children:
            lines.append(f"⬇️  Children: {len(children)}")
            for i, child in enumerate(children[:3], 1):  # Show max 3
                lines.append(f"    {i}. {child.display_name}")
            if len(children) > 3:
                lines.append(f"    ... and {len(children) - 3} more")
        else:
            lines.append("⬇️  Children: None")
        
        # Siblings info
        siblings = nav_context.get('siblings', [])
        if siblings:
            lines.append(f"↔️  Siblings: {len(siblings)}")
        
        return "\n".join(lines)
    
    def render_comparison(self, state1: ConversationState, state2: ConversationState) -> str:
        """Render side-by-side comparison of two states."""
        lines = []
        lines.append("🔍 Branch Comparison")
        lines.append("=" * 70)
        
        # Headers
        lines.append(f"Branch A: {state1.display_name} | Branch B: {state2.display_name}")
        lines.append("")
        
        # Messages
        lines.append("💬 User Messages:")
        lines.append(f"A: {state1.message}")
        lines.append(f"B: {state2.message}")
        lines.append("")
        
        # Responses (truncated)
        lines.append("🤖 Assistant Responses:")
        resp1 = state1.response[:100] + "..." if len(state1.response) > 100 else state1.response
        resp2 = state2.response[:100] + "..." if len(state2.response) > 100 else state2.response
        lines.append(f"A: {resp1}")
        lines.append(f"B: {resp2}")
        lines.append("")
        
        # Tags
        if state1.tags or state2.tags:
            lines.append("🏷️  Tags:")
            tags1_display = ", ".join(state1.tags) if state1.tags else "none"
            tags2_display = ", ".join(state2.tags) if state2.tags else "none"
            lines.append(f"A: {tags1_display}")
            lines.append(f"B: {tags2_display}")
        
        return "\n".join(lines)