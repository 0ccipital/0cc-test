"""Main application entry point."""

import sys
import os
import signal
import readline
import atexit
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.tree import ConversationTree
from core.navigation import TreeNavigator
from llm.client import OllamaClient
from storage.persistence import ConversationPersistence
from ui.commands import CommandRegistry, AppContext
from ui.display import StreamingDisplay
from ui.interactive import InteractiveSelector, InteractiveTreeBrowser, TagSelector, LoadSelector
from utils.errors import TreeChatError, LLMError

class OllamaTreeChatApp:
    """Main application class."""
    
    def __init__(self):
        self.console = Console()
        self.display = StreamingDisplay()
        
        # Core components
        self.tree = ConversationTree()
        self.navigator = TreeNavigator(self.tree)
        self.ollama_client = OllamaClient()
        self.persistence = ConversationPersistence()
        self.command_registry = CommandRegistry()
        
        # Application state
        self.current_model: Optional[str] = None
        self.system_message: Optional[str] = None
        self.recent_tags: list = []
        
        # Setup
        self.setup_readline()
        self.setup_signal_handlers()
    
    def setup_readline(self):
        """Setup readline for better input handling."""
        try:
            readline.parse_and_bind("tab: complete")
            
            history_file = Path.home() / ".ollama_chat_history"
            try:
                readline.read_history_file(str(history_file))
            except FileNotFoundError:
                pass
            
            atexit.register(readline.write_history_file, str(history_file))
            readline.set_history_length(1000)
            
        except ImportError:
            pass  # readline not available
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful exit."""
        def signal_handler(sig, frame):
            self.display.print_warning("Goodbye!")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def print_header(self):
        """Print application header."""
        title = Text("🌳 OLLAMA CONTEXT TREE CHAT v2.0", style="bold cyan")
        
        info_lines = []
        if self.current_model:
            info_lines.append(f"📦 Model: {self.current_model}")
            
            if self.tree.current_state_id:
                current_state = self.tree.current_state
                if current_state:
                    branch_info = " 🌿" if not current_state.is_root else ""
                    info_lines.append(f"📍 Current: {current_state.display_name}{branch_info}")
        
        if info_lines:
            info_text = "\n".join(info_lines)
            panel = Panel(f"{title}\n\n{info_text}", border_style="cyan")
        else:
            panel = Panel(title, border_style="cyan")
        
        self.console.print(panel)
    
    def select_model(self) -> bool:
        """Let user select a model."""
        try:
            models = self.ollama_client.get_available_models()
        except LLMError as e:
            self.display.print_error(f"Failed to get models: {e}")
            return False
        
        if not models:
            self.display.print_error("No models found. Make sure Ollama is running and has models installed.")
            return False
        
        self.console.print("\n📋 Available Models:")
        for i, model in enumerate(models, 1):
            self.console.print(f"  {i}. {model}")
        
        while True:
            try:
                choice = self.console.input(f"\nSelect model (1-{len(models)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return False
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    self.current_model = models[choice_num - 1]
                    self.display.print_success(f"Selected model: {self.current_model}")
                    return True
                else:
                    self.display.print_error(f"Please enter a number between 1 and {len(models)}")
            except ValueError:
                self.display.print_error("Please enter a valid number or 'q' to quit")
            except (EOFError, KeyboardInterrupt):
                return False
    
    def set_system_message(self):
        """Allow user to set a system message."""
        self.console.print("\n🔧 System Message Setup")
        self.console.print("Enter a system message (or press Enter to skip):")
        
        try:
            system_msg = self.console.input("> ").strip()
            if system_msg:
                self.system_message = system_msg
                preview = system_msg[:50] + "..." if len(system_msg) > 50 else system_msg
                self.display.print_success(f"System message set: {preview}")
            else:
                self.system_message = None
                self.display.print_info("No system message set")
        except (EOFError, KeyboardInterrupt):
            self.system_message = None
    
    def handle_chat_message(self, message: str):
        """Handle regular chat message with streaming."""
        try:
            # Build message history
            messages = []
            if self.system_message and self.tree.state_count == 0:
                messages.append({"role": "system", "content": self.system_message})
            
            # Get conversation history
            conversation_messages = self.tree.get_conversation_messages()
            messages.extend(conversation_messages)
            
            # Add new user message
            messages.append({"role": "user", "content": message})
            
            # Stream response
            response_generator = self.ollama_client.chat_stream(messages, self.current_model)
            complete_response = self.display.stream_response(response_generator)
            
            # Add to tree
            state = self.tree.add_state(
                parent_id=self.tree.current_state_id,
                message=message,
                response=complete_response,
                model=self.current_model
            )
            
            # Show branch creation info if applicable
            if state.is_branch:  # Now uses the property
                parent_children = self.tree.get_children(state.parent_id) if state.parent_id else []
                siblings = [s for s in parent_children if s.hierarchical_id != state.hierarchical_id]
                branch_number = len(siblings) + 1
                self.display.print_info(f"Created branch {state.display_name} (Branch {branch_number}) from {state.parent_id}")
                if siblings:
                    sibling_names = [s.display_name for s in siblings]
                    self.console.print(f"   Sibling branches: {', '.join(sibling_names)}", style="dim")
            
        except Exception as e:
            self.display.print_error(f"Chat failed: {e}")
    
    def handle_command(self, command_line: str):
        """Handle command execution."""
        context = AppContext(
            tree=self.tree,
            navigator=self.navigator,
            ollama_client=self.ollama_client,
            persistence=self.persistence,
            current_model=self.current_model,
            system_message=self.system_message
        )
        
        result = self.command_registry.execute(command_line, context)
        
        if result.success:
            if result.message == "show_help":
                self.show_help()
            elif result.message == "interactive_tag":
                self.handle_interactive_tag(result.data)
            elif result.message == "show_tree":
                self.display.print_tree(result.data)
            elif result.message == "show_load_menu":
                self.handle_load_menu(result.data)
            elif result.message == "interactive_tree":
                self.handle_interactive_tree(result.data)
            elif result.message:
                self.display.print_success(result.message)
            
            if result.should_exit:
                return True
        else:
            self.display.print_error(result.message)
        
        return False
    
    def handle_interactive_tag(self, current_state):
        """Handle interactive tagging."""
        selector = TagSelector(self.recent_tags)
        selected_tag = selector.select_tag(list(current_state.tags))
        
        if selected_tag:
            if selected_tag in current_state.tags:
                updated_state = current_state.remove_tag(selected_tag)
                self.tree.update_state(current_state.hierarchical_id, updated_state)
                self.display.print_success(f"Removed tag: {selected_tag}")
            else:
                updated_state = current_state.add_tag(selected_tag)
                self.tree.update_state(current_state.hierarchical_id, updated_state)
                self.display.print_success(f"Added tag: {selected_tag}")
                
                # Update recent tags
                if selected_tag in self.recent_tags:
                    self.recent_tags.remove(selected_tag)
                self.recent_tags.insert(0, selected_tag)
                self.recent_tags = self.recent_tags[:10]  # Keep last 10
    
    def handle_load_menu(self, persistence):
        """Handle load conversation menu."""
        conversations = persistence.list_conversations()
        selector = LoadSelector(conversations)
        selected_filename = selector.select_conversation()
        
        if selected_filename:
            try:
                loaded_tree = persistence.load_conversation(selected_filename)
                self.tree = loaded_tree
                self.navigator = TreeNavigator(self.tree)
                self.display.print_success(f"Loaded conversation: {selected_filename}")
            except Exception as e:
                self.display.print_error(f"Failed to load conversation: {e}")
    
    def handle_interactive_tree(self, tree):
        """Handle interactive tree browser."""
        browser = InteractiveTreeBrowser(tree)
        selected_state = browser.browse()
        
        if selected_state:
            self.tree.navigate_to(selected_state.hierarchical_id)
            self.display.print_success(f"Navigated to {selected_state.display_name}")
    
    def chat_loop(self):
        """Main chat loop."""
        self.console.print("\n💬 Chat started! Type your message or use commands (type /help for help)")
        
        while True:
            try:
                # Show current context with enhanced styling
                if self.tree.current_state_id:
                    current_state = self.tree.current_state
                    if current_state:
                        branch_indicator = " 🌿" if current_state.is_branch else ""  # Use property
                        prompt = f"\n[{current_state.display_name}{branch_indicator}] You: "
                    else:
                        prompt = "\n[unknown] You: "
                else:
                    prompt = "\n[new] You: "
                
                user_input = self.console.input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    should_exit = self.handle_command(user_input)
                    if should_exit:
                        break
                else:
                    # Regular chat message
                    self.handle_chat_message(user_input)
                    
            except KeyboardInterrupt:
                self.display.print_warning("\nGoodbye!")
                break
            except EOFError:
                self.display.print_warning("\nGoodbye!")
                break
            except Exception as e:
                self.display.print_error(f"Unexpected error: {e}")
    
    def run(self):
        """Main application entry point."""
        try:
            # Check terminal compatibility
            if os.getenv('TERM_PROGRAM') == 'iTerm.app':
                print('\033]0;Ollama Context Tree Chat\007', end='')  # Set window title
            
            self.print_header()
            
            self.console.print("\n🌳 Welcome to Ollama Context Tree Chat v2.0!")
            self.console.print("Professional CLI for branching LLM conversations")
            self.console.print("Navigate conversation trees to avoid context pollution\n")
            
            # Check Ollama connection
            if not self.ollama_client.is_connected():
                self.display.print_error("Cannot connect to Ollama.")
                self.console.print("Please make sure Ollama is running with: ollama serve")
                return
            
            # Model selection
            if not self.select_model():
                return
            
            # Optional system message
            self.set_system_message()
            
            # Start chat
            self.print_header()
            self.chat_loop()
            
        except Exception as e:
            self.display.print_error(f"Application error: {e}")

    def show_help(self):
        """Show help information."""
        self.console.print("\n📖 Available Commands:")
        
        commands_info = [
            ("/help, /h", "Show this help message"),
            ("/goto <id>, /g, /cd", "Navigate to any state by sequence or hierarchical ID"),
            ("/up, /u", "Navigate to parent state"),
            ("/down <n>, /d", "Navigate to specific child branch"),
            ("/states, /s", "Show conversation tree and all states"),
            ("/tag <text>, /t", "Tag current state with custom text"),
            ("/tree", "Interactive tree browser with live preview"),
            ("/save [name], /sv", "Save conversation tree to file"),
            ("/load, /l", "Load conversation tree from file"),
            ("/new, /n", "Start new conversation"),
            ("/quit, /q", "Exit the application"),
        ]
        
        for cmd, desc in commands_info:
            self.console.print(f"  {cmd:<20} - {desc}")
        
        self.console.print("\n💬 Chat:")
        self.console.print("  Just type your message to chat normally!")
        
        self.console.print("\n🏷️  Tagging:")
        self.console.print("  /t debugging memory leak    - Tag without quotes")
        self.console.print("  /t                          - Interactive tag menu")
        
        self.console.print("\n🌳 Navigation:")
        self.console.print("  /goto 3        - Go to sequence number 3")
        self.console.print("  /goto 1.2.1    - Go to hierarchical position 1.2.1")
        self.console.print("  /tree          - Interactive tree browser")
        
        self.console.print("\n💡 Pro Tip: When you revert to a previous state and continue,")
        self.console.print("   a new branch will be created automatically!")

def main():
    """Entry point for the application."""
    try:
        app = OllamaTreeChatApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()