"""Enhanced display utilities with streaming support."""

import sys
from typing import Generator, Optional
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ui.renderer import TreeRenderer

class StreamingDisplay:
    """Handle streaming display with Rich formatting."""
    
    def __init__(self):
        self.console = Console()
        self.renderer = TreeRenderer()
    
    def stream_response(self, response_generator: Generator[str, None, str], prefix: str = "🤖 Assistant: ") -> str:
        """Display streaming response with Rich formatting but scrollable."""
        # Use console.print for the prefix with styling
        self.console.print()  # Add some space
        self.console.print("🤖 Assistant: ", style="bright_green bold", end="")
        
        complete_response = ""
        
        # Stream chunks directly without Live wrapper
        for chunk in response_generator:
            complete_response += chunk
            # Use regular print for streaming content to allow scrolling
            print(chunk, end="", flush=True)
        
        print()  # Newline at end
        return complete_response
    
    def show_thinking(self, message: str = "Thinking") -> Live:
        """Show thinking indicator with spinner."""
        spinner_text = Text()
        spinner_text.append("🤖 ", style="bright_green")
        spinner_text.append(f"{message}...", style="cyan")
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        
        task = progress.add_task(message, total=None)
        return Live(progress, console=self.console)
    
    def print_success(self, message: str):
        """Print success message."""
        self.console.print(f"✅ {message}", style="bright_green")
    
    def print_error(self, message: str):
        """Print error message."""
        self.console.print(f"❌ {message}", style="bright_red")
    
    def print_info(self, message: str):
        """Print info message."""
        self.console.print(f"💡 {message}", style="bright_blue")
    
    def print_warning(self, message: str):
        """Print warning message."""
        self.console.print(f"⚠️  {message}", style="yellow")
    
    def print_tree(self, tree, highlight_current: bool = True):
        """Print conversation tree."""
        tree_output = self.renderer.render_tree(tree, highlight_current)
        self.console.print(tree_output)
    
    def print_state_summary(self, states, current_state_id):
        """Print state summary."""
        summary = self.renderer.render_state_summary(states, current_state_id)
        self.console.print(summary)
    
    def print_navigation_context(self, nav_context):
        """Print navigation context."""
        context_output = self.renderer.render_navigation_context(nav_context)
        self.console.print(Panel(context_output, title="Navigation Context", border_style="blue"))
    
    def print_comparison(self, state1, state2):
        """Print state comparison."""
        comparison = self.renderer.render_comparison(state1, state2)
        self.console.print(comparison)
    
    def clear_line(self):
        """Clear current line."""
        self.console.print("\r" + " " * 80 + "\r", end="")