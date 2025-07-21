"""Main CLI interface for Ollama Context Tree Chat."""

import os
import sys
import signal
import readline
import atexit
from pathlib import Path
from datetime import datetime

from tree import ContextTree
from ollama import OllamaClient
from display import TreeDisplay, Colors
import tags
import config

class OllamaChatCLI:
    def __init__(self):
        self.tree = ContextTree()
        self.ollama = OllamaClient()
        self.display = TreeDisplay()
        self.current_model = None
        self.system_message = None
        self.setup_readline()
        self.setup_signal_handlers()
        
    def setup_readline(self):
        """Setup readline for better input handling."""
        try:
            # Enable tab completion
            readline.parse_and_bind("tab: complete")
            
            # Set up history
            history_file = config.HISTORY_FILE
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
            
            # Save history on exit
            atexit.register(readline.write_history_file, history_file)
            
            # Set history length
            readline.set_history_length(1000)
            
        except ImportError:
            pass  # readline not available
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful exit."""
        def signal_handler(sig, frame):
            print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear')
    
    def print_header(self):
        """Print the CLI header with current state info."""
        title = "🌳 OLLAMA CONTEXT TREE CHAT"
        self.display.print_separator("═", Colors.CYAN)
        padding = (self.display.terminal_width - len(title)) // 2
        print(f"{Colors.CYAN}{Colors.BOLD}{' ' * padding}{title}{Colors.RESET}")
        self.display.print_separator("═", Colors.CYAN)
        
        if self.current_model:
            print(f"{Colors.GREEN}📦 Model:{Colors.RESET} {Colors.BOLD}{self.current_model}{Colors.RESET}")
            
            if self.tree.current_state_id:
                current_state = self.tree.get_current_state()
                branch_info = ""
                if current_state and current_state.get("is_branch", False):
                    branch_info = f" {Colors.YELLOW}🌿 [BRANCH]{Colors.RESET}"
                
                print(f"{Colors.BLUE}📍 Current State:{Colors.RESET} {Colors.BOLD}{self.tree.current_state_id}{Colors.RESET}{branch_info}")
                
                # Show path to current state
                if current_state:
                    path = self.tree.get_path_to_state(self.tree.current_state_id)
                    if len(path) > 1:
                        path_display = f" {Colors.GRAY}→{Colors.RESET} ".join(path)
                        print(f"{Colors.GRAY}🛤️  Path:{Colors.RESET} {path_display}")
        
        self.display.print_separator("─", Colors.GRAY)
        print()
    
    def select_model(self) -> bool:
        """Let user select a model from available models."""
        print(f"{Colors.CYAN}Fetching available models...{Colors.RESET}")
        models = self.ollama.get_available_models()
        
        if not models:
            self.display.show_error("No models found. Make sure Ollama is running and has models installed.")
            return False
        
        print(f"\n{Colors.BOLD}📋 Available Models:{Colors.RESET}")
        for i, model in enumerate(models, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {model}")
        
        while True:
            try:
                prompt = f"\n{Colors.BOLD}Select model (1-{len(models)}) or 'q' to quit:{Colors.RESET} "
                choice = input(prompt).strip()
                
                if choice.lower() == 'q':
                    return False
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    self.current_model = models[choice_num - 1]
                    self.display.show_success(f"Selected model: {self.current_model}")
                    return True
                else:
                    self.display.show_error(f"Please enter a number between 1 and {len(models)}")
            except ValueError:
                self.display.show_error("Please enter a valid number or 'q' to quit")
            except (EOFError, KeyboardInterrupt):
                return False
    
    def set_system_message(self):
        """Allow user to set a system message."""
        print(f"\n{Colors.BOLD}🔧 System Message Setup{Colors.RESET}")
        print("Enter a system message (or press Enter to skip):")
        
        try:
            system_msg = input(f"{Colors.CYAN}>{Colors.RESET} ").strip()
            if system_msg:
                self.system_message = system_msg
                preview = system_msg[:50] + "..." if len(system_msg) > 50 else system_msg
                self.display.show_success(f"System message set: {preview}")
            else:
                self.system_message = None
                self.display.show_info("No system message set")
        except (EOFError, KeyboardInterrupt):
            self.system_message = None
            print()
    
    def show_states(self):
        """Display all conversation states."""
        if not self.tree.states:
            print(f"{Colors.GRAY}📭 No conversation states yet.{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}🌳 Conversation Tree:{Colors.RESET}")
        self.display.print_separator("─", Colors.GRAY)
        tree_display = self.display.render_tree(self.tree.states, self.tree.current_state_id)
        print(tree_display)
        self.display.print_separator("─", Colors.GRAY)
        
        # Show state summary
        print(f"\n{Colors.BOLD}📊 State Summary:{Colors.RESET}")
        sorted_states = sorted(self.tree.states.items(), key=lambda x: x[1]["creation_order"])
        
        for state_id, state in sorted_states:
            current_marker = f" {Colors.GREEN}← CURRENT{Colors.RESET}" if state_id == self.tree.current_state_id else ""
            state_line = self.display.render_state_line(state)
            print(f"  {state_line}{current_marker}")
    
    def handle_revert(self) -> bool:
        """Handle revert command with enhanced interface."""
        if not self.tree.states:
            self.display.show_error("No states available to revert to.")
            return False
        
        # Get branch points for smart selection
        branch_points = self.tree.get_branch_points()
        
        if not branch_points:
            self.display.show_info("No branch points found. Showing all states.")
            # Show all states if no branch points
            all_states = list(self.tree.states.values())
            all_states.sort(key=lambda x: x['creation_order'])
            branch_points = all_states
        
        print(f"\n{Colors.BOLD}🔄 Revert to Previous State{Colors.RESET}")
        if self.tree.current_state_id:
            print(f"Current state: {Colors.CYAN}{self.tree.current_state_id}{Colors.RESET}")
        
        # Use display method for selection
        selected_state_id = self.display.prompt_for_revert_choice(branch_points)
        
        if not selected_state_id:
            return False
        
        if selected_state_id == self.tree.current_state_id:
            self.display.show_warning("You're already at that state!")
            return False
        
        print(f"{Colors.CYAN}🔄 Reverting to {selected_state_id}...{Colors.RESET}")
        
        # Unload model for clean context
        if self.current_model:
            self.ollama.unload_model(self.current_model)
        
        if self.tree.revert_to_state(selected_state_id):
            self.display.show_success(f"Successfully reverted to {selected_state_id}")
            self.display.show_info("Next message will create a new branch from this state")
            return True
        else:
            self.display.show_error(f"Failed to revert to {selected_state_id}")
            return False
    
    def handle_tag(self):
        """Handle tagging command."""
        if not self.tree.current_state_id:
            self.display.show_error("No current state to tag.")
            return
        
        current_state = self.tree.get_current_state()
        if not current_state:
            self.display.show_error("Current state not found.")
            return
        
        current_tags = current_state.get('tags', [])
        selected_tag = self.display.prompt_for_tag(current_tags)
        
        if selected_tag:
            if selected_tag in current_tags:
                # Remove tag if already present
                tags.remove_tag(current_state, selected_tag)
                self.display.show_success(f"Removed tag: {tags.get_tag_display(selected_tag)}")
            else:
                # Add tag
                tags.assign_tag(current_state, selected_tag)
                self.display.show_success(f"Added tag: {tags.get_tag_display(selected_tag)}")
    
    def handle_compare(self):
        """Handle branch comparison."""
        if not self.tree.current_state_id:
            self.display.show_error("No current state for comparison.")
            return
        
        siblings = self.tree.get_sibling_states(self.tree.current_state_id)
        if not siblings:
            self.display.show_info("No sibling branches to compare with.")
            return
        
        current_state = self.tree.get_current_state()
        
        print(f"\n{Colors.BOLD}🔍 Compare with sibling branches:{Colors.RESET}")
        for i, sibling_id in enumerate(siblings, 1):
            sibling_state = self.tree.states[sibling_id]
            state_line = self.display.render_state_line(sibling_state)
            print(f"  {i}. {state_line}")
        
        try:
            choice = input(f"\nSelect branch to compare (1-{len(siblings)}) or Enter to cancel: ").strip()
            if not choice:
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(siblings):
                sibling_id = siblings[choice_num - 1]
                sibling_state = self.tree.states[sibling_id]
                
                comparison = self.display.render_comparison(current_state, sibling_state)
                print(f"\n{comparison}")
            else:
                self.display.show_error(f"Please enter a number between 1 and {len(siblings)}")
        except (ValueError, EOFError, KeyboardInterrupt):
            return
    
    def handle_save(self):
        """Handle save command."""
        if not self.tree.states:
            self.display.show_error("No conversation to save.")
            return
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"conversation_{timestamp}.json"
        
        try:
            filename = input(f"Save as [{default_name}]: ").strip()
            if not filename:
                filename = default_name
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Use save directory
            filepath = os.path.join(config.DEFAULT_SAVE_DIR, filename)
            
            if self.tree.save_to_file(filepath):
                self.display.show_success(f"Conversation saved to {filepath}")
            else:
                self.display.show_error("Failed to save conversation")
        except (EOFError, KeyboardInterrupt):
            return
    
    def handle_load(self):
        """Handle load command."""
        save_dir = Path(config.DEFAULT_SAVE_DIR)
        if not save_dir.exists():
            self.display.show_error("No saved conversations found.")
            return
        
        # List available files
        json_files = list(save_dir.glob("*.json"))
        if not json_files:
            self.display.show_error("No saved conversations found.")
            return
        
        print(f"\n{Colors.BOLD}📁 Saved Conversations:{Colors.RESET}")
        for i, filepath in enumerate(json_files, 1):
            # Get file modification time
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            print(f"  {i}. {filepath.name} {Colors.GRAY}[{mtime.strftime('%Y-%m-%d %H:%M')}]{Colors.RESET}")
        
        try:
            choice = input(f"\nSelect conversation to load (1-{len(json_files)}) or Enter to cancel: ").strip()
            if not choice:
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(json_files):
                filepath = json_files[choice_num - 1]
                
                if self.tree.load_from_file(str(filepath)):
                    self.display.show_success(f"Loaded conversation from {filepath.name}")
                    # Update display
                    self.clear_screen()
                    self.print_header()
                else:
                    self.display.show_error("Failed to load conversation")
            else:
                self.display.show_error(f"Please enter a number between 1 and {len(json_files)}")
        except (ValueError, EOFError, KeyboardInterrupt):
            return
    
    def print_help(self):
        """Print available commands with examples."""
        print(f"\n{Colors.BOLD}📖 Available Commands:{Colors.RESET}")
        
        commands = [
            ("/help", "Show this help message"),
            ("/states", "Show conversation tree and all states"),
            ("/revert", "Revert to a previous state (smart branch selection)"),
            ("/tag", "Tag current state (✅ good, ❌ bad, ⚡ branch-point)"),
            ("/compare", "Compare current state with sibling branches"),
            ("/save", "Save conversation tree to file"),
            ("/load", "Load conversation tree from file"),
            ("/model", "Change current model"),
            ("/system", "Set system message"),
            ("/clear", "Clear screen"),
            ("/quit, /q", "Exit the chat")
        ]
        
        for cmd, desc in commands:
            print(f"  {Colors.CYAN}{cmd:<12}{Colors.RESET} - {desc}")
        
        print(f"\n{Colors.BOLD}💬 Chat:{Colors.RESET}")
        print("  Just type your message to chat normally!")
        
        print(f"\n{Colors.BOLD}🏷️  Quick Tagging:{Colors.RESET}")
        print("  After each response, you can quickly tag with:")
        print(tags.get_tag_help())
        
        print(f"\n{Colors.YELLOW}💡 Tip:{Colors.RESET} When you revert to a previous state and continue,")
        print("   a new branch will be created automatically!")
    
    def chat_loop(self):
        """Main chat loop with enhanced UX."""
        self.print_help()
        
        while True:
            try:
                # Show current context with enhanced styling
                if self.tree.current_state_id:
                    current_state = self.tree.get_current_state()
                    branch_indicator = ""
                    if current_state and current_state.get("is_branch", False):
                        branch_indicator = f" {Colors.YELLOW}🌿{Colors.RESET}"
                    
                    prompt = f"\n{Colors.BOLD}[{Colors.CYAN}{self.tree.current_state_id}{Colors.RESET}{branch_indicator}{Colors.BOLD}]{Colors.RESET} {Colors.BOLD}You:{Colors.RESET} "
                else:
                    prompt = f"\n{Colors.BOLD}[{Colors.GRAY}new{Colors.RESET}{Colors.BOLD}]{Colors.RESET} {Colors.BOLD}You:{Colors.RESET} "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input[1:].lower()
                    
                    if command in ['quit', 'q']:
                        print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
                        break
                    elif command == 'help':
                        self.print_help()
                    elif command == 'states':
                        self.show_states()
                    elif command == 'revert':
                        reverted = self.handle_revert()
                        if reverted:
                            # Brief pause and refresh display
                            import time
                            time.sleep(0.5)
                            self.clear_screen()
                            self.print_header()
                    elif command == 'tag':
                        self.handle_tag()
                    elif command == 'compare':
                        self.handle_compare()
                    elif command == 'save':
                        self.handle_save()
                    elif command == 'load':
                        self.handle_load()
                    elif command == 'model':
                        if self.select_model():
                            self.clear_screen()
                            self.print_header()
                    elif command == 'system':
                        self.set_system_message()
                    elif command == 'clear':
                        self.clear_screen()
                        self.print_header()
                    else:
                        self.display.show_error(f"Unknown command: {command}. Type /help for available commands.")
                    continue
                
                # Regular chat message
                print(f"\n{Colors.CYAN}🤖 Thinking...{Colors.RESET}", end="", flush=True)
                
                try:
                    # Check if this will create a branch
                    will_branch = False
                    if self.tree.current_state_id and self.tree.current_state_id in self.tree.states:
                        current_state = self.tree.states[self.tree.current_state_id]
                        if len(current_state.get("children", [])) > 0:
                            will_branch = True
                            print(f"\r{Colors.YELLOW}🌿 Creating new branch from {self.tree.current_state_id}...{Colors.RESET}")
                    else:
                        print(f"\r{' ' * 20}\r", end="")  # Clear "Thinking..." message
                    
                    # Build message history
                    messages = []
                    if self.system_message and not self.tree.current_state_id:
                        messages.append({"role": "system", "content": self.system_message})
                    
                    # Get conversation history up to current state
                    if self.tree.current_state_id:
                        conversation_messages = self.tree.get_conversation_messages(self.tree.current_state_id)
                        messages.extend(conversation_messages)
                    
                    # Add new user message
                    messages.append({"role": "user", "content": user_input})
                    
                    # Send to Ollama
                    response = self.ollama.chat(messages, self.current_model)
                    
                    # Create new state
                    state_id = self.tree.create_state(
                        message=user_input,
                        response=response,
                        model=self.current_model,
                        parent_id=self.tree.current_state_id
                    )
                    
                    # Display response
                    wrapped_response = self._wrap_text(response, self.display.terminal_width - 4)
                    print(f"{Colors.GREEN}🤖 Assistant:{Colors.RESET} {wrapped_response}")
                    
                    # Show branch creation info
                    new_state = self.tree.states[state_id]
                    if new_state.get("is_branch", False):
                        parent_id = new_state["parent_id"]
                        parent_children = self.tree.get_children(parent_id)
                        branch_number = len(parent_children)
                        print(f"\n{Colors.YELLOW}🌿 Created branch {Colors.CYAN}{state_id}{Colors.RESET} {Colors.YELLOW}(Branch {branch_number}) from {Colors.CYAN}{parent_id}{Colors.RESET}")
                        
                        # Show sibling branches
                        siblings = [child for child in parent_children if child != state_id]
                        if siblings:
                            sibling_display = ', '.join([f"{Colors.CYAN}{s}{Colors.RESET}" for s in siblings])
                            print(f"   {Colors.GRAY}Sibling branches: {sibling_display}{Colors.RESET}")
                    
                    # Quick tagging prompt
                    if config.QUICK_TAGGING_ENABLED:
                        print(f"\n{Colors.DIM}Quick tag: [g]ood [b]ranch-point [x]bad [Enter]skip{Colors.RESET}", end=" ")
                        try:
                            # Set a short timeout for quick tagging
                            import select
                            import sys
                            
                            if select.select([sys.stdin], [], [], 2.0)[0]:  # 2 second timeout
                                quick_tag = sys.stdin.readline().strip().lower()
                                if quick_tag:
                                    tag_name = tags.parse_quick_tag(quick_tag)
                                    if tag_name:
                                        tags.assign_tag(new_state, tag_name)
                                        tag_display = tags.get_tag_display(tag_name)
                                        print(f"\r{Colors.GREEN}✅ Tagged: {tag_display}{Colors.RESET}")
                                    else:
                                        print(f"\r{Colors.GRAY}Skipped tagging{Colors.RESET}")
                                else:
                                    print(f"\r{Colors.GRAY}Skipped tagging{Colors.RESET}")
                            else:
                                print(f"\r{Colors.GRAY}Skipped tagging{Colors.RESET}")
                        except:
                            # Fallback if select doesn't work (Windows)
                            print(f"\r{Colors.GRAY}Skipped tagging{Colors.RESET}")
                    
                except Exception as e:
                    print(f"\r{Colors.RED}❌ Error: {e}{Colors.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
                break
            except EOFError:
                print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
                break
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n           '.join(lines)  # Indent continuation lines
    
    def run(self):
        """Main entry point with enhanced startup experience."""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}Welcome to Ollama Context Tree Chat! 🌳{Colors.RESET}")
        print("This tool lets you branch and revert conversations to avoid context pollution.")
        print("When you revert to a previous state and continue, it creates a new branch automatically.")
        print()
        
        # Check if Ollama is running
        if not self.ollama.is_connected():
            self.display.show_error("Cannot connect to Ollama.")
            print("Please make sure Ollama is running with: ollama serve")
            return
        
        # Model selection
        if not self.select_model():
            return
        
        # Optional system message
        self.set_system_message()
        
        # Start chat
        import time
        time.sleep(0.5)  # Brief pause for better UX
        self.clear_screen()
        self.print_header()
        self.chat_loop()

def main():
    """Entry point with enhanced error handling."""
    try:
        # Check if we're in a compatible terminal
        if os.getenv('TERM_PROGRAM') == 'iTerm.app':
            # iTerm2 specific optimizations
            print('\033]0;Ollama Context Tree Chat\007', end='')  # Set window title
        
        cli = OllamaChatCLI()
        cli.run()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Unexpected error: {e}{Colors.RESET}")
        print(f"{Colors.GRAY}If this persists, please check that Ollama is running.{Colors.RESET}")

if __name__ == "__main__":
    main()