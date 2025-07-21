import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os
import sys
import shutil
import signal
import readline
import atexit

class OllamaContextTree:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.states: Dict[str, Dict] = {}
        self.current_state_id: Optional[str] = None
        self.global_counter = 0
        
    def _generate_state_id(self, parent_id: Optional[str] = None) -> str:
        """Generate a state ID that reflects tree structure"""
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
    
    def _unload_model(self, model: str) -> bool:
        """Completely unload model from memory to clear all context"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [],
                    "keep_alive": 0
                }
            )
            return response.status_code == 200
        except Exception as e:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                return [model["name"] for model in models_data.get("models", [])]
            else:
                return []
        except Exception as e:
            return []
    
    def chat_and_save_state(self, 
                           message: str, 
                           model: str = "llama3.2",
                           parent_state_id: Optional[str] = None,
                           system_message: Optional[str] = None) -> str:
        """Send a chat message and save the resulting state"""
        
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        if parent_state_id and parent_state_id in self.states:
            parent_messages = self.states[parent_state_id]["messages"]
            messages.extend(parent_messages)
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["message"]["content"]
                
                complete_messages = messages + [{"role": "assistant", "content": assistant_message}]
                
                state_id = self._generate_state_id(parent_state_id)
                
                depth = 0
                if parent_state_id:
                    depth = self.states[parent_state_id]["depth"] + 1
                
                is_branch = False
                branch_info = None
                if parent_state_id and parent_state_id in self.states:
                    parent_children = self.states[parent_state_id]["children"]
                    if len(parent_children) > 0:
                        is_branch = True
                        branch_info = {
                            "branched_from": parent_state_id,
                            "branch_number": len(parent_children) + 1,
                            "sibling_states": parent_children.copy()
                        }
                
                self.states[state_id] = {
                    "id": state_id,
                    "parent_id": parent_state_id,
                    "messages": complete_messages,
                    "last_user_message": message,
                    "last_assistant_message": assistant_message,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "children": [],
                    "depth": depth,
                    "is_branch": is_branch,
                    "branch_info": branch_info,
                    "creation_order": self.global_counter
                }
                
                if parent_state_id and parent_state_id in self.states:
                    self.states[parent_state_id]["children"].append(state_id)
                
                self.current_state_id = state_id
                return state_id
                
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Failed to chat with Ollama: {e}")
    
    def revert_to_state(self, state_id: str) -> bool:
        """Revert to a previous state"""
        if state_id not in self.states:
            return False
        
        model = self.states[state_id]["model"]
        if self._unload_model(model):
            self.current_state_id = state_id
            return True
        return False
    
    def get_path_to_state(self, state_id: str) -> List[str]:
        """Get the path from root to a specific state"""
        if state_id not in self.states:
            return []
        
        path = []
        current = state_id
        while current:
            path.insert(0, current)
            current = self.states[current]["parent_id"]
        return path
    
    def print_conversation_tree(self, state_id: str = None, indent: int = 0, is_last_child: bool = True, prefix: str = ""):
        """Print a visual representation of the conversation tree with proper branching"""
        if state_id is None:
            roots = [s for s in self.states.values() if s["parent_id"] is None]
            if not roots:
                print("No conversation states yet.")
                return
            for i, root in enumerate(roots):
                is_last = i == len(roots) - 1
                self.print_conversation_tree(root["id"], 0, is_last, "")
            return
        
        if state_id not in self.states:
            return
            
        state = self.states[state_id]
        
        if indent == 0:
            tree_prefix = ""
        else:
            tree_prefix = prefix + ("└── " if is_last_child else "├── ")
        
        user_msg = state["last_user_message"][:45] + "..." if len(state["last_user_message"]) > 45 else state["last_user_message"]
        
        current_marker = " ← CURRENT" if state_id == self.current_state_id else ""
        branch_marker = " 🌿" if state["is_branch"] else ""
        
        timestamp = datetime.fromisoformat(state["timestamp"]).strftime("%H:%M:%S")
        
        print(f"{tree_prefix}{state['id']}: {user_msg}{branch_marker}{current_marker}")
        
        children = state["children"]
        for i, child_id in enumerate(children):
            is_last = i == len(children) - 1
            if indent == 0:
                child_prefix = ""
            else:
                child_prefix = prefix + ("    " if is_last_child else "│   ")
            self.print_conversation_tree(child_id, indent + 1, is_last, child_prefix)

class Colors:
    """ANSI color codes for terminal output"""
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
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'

class OllamaChatCLI:
    def __init__(self):
        self.tree = OllamaContextTree()
        self.current_model = None
        self.system_message = None
        self.terminal_width = self._get_terminal_width()
        self.setup_readline()
        self.setup_signal_handlers()
        
    def _get_terminal_width(self) -> int:
        """Get terminal width, default to 80 if can't determine"""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def setup_readline(self):
        """Setup readline for better input handling"""
        try:
            # Enable tab completion
            readline.parse_and_bind("tab: complete")
            
            # Set up history
            history_file = os.path.expanduser("~/.ollama_chat_history")
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
        """Setup signal handlers for graceful exit"""
        def signal_handler(sig, frame):
            print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear')
    
    def print_separator(self, char="═", color=Colors.BLUE):
        """Print a separator line"""
        print(f"{color}{char * self.terminal_width}{Colors.RESET}")
    
    def print_header(self):
        """Print the CLI header with enhanced styling"""
        self.print_separator("═", Colors.CYAN)
        title = "🌳 OLLAMA CONTEXT TREE CHAT"
        padding = (self.terminal_width - len(title)) // 2
        print(f"{Colors.CYAN}{Colors.BOLD}{' ' * padding}{title}{Colors.RESET}")
        self.print_separator("═", Colors.CYAN)
        
        if self.current_model:
            print(f"{Colors.GREEN}📦 Model:{Colors.RESET} {Colors.BOLD}{self.current_model}{Colors.RESET}")
            
            if self.tree.current_state_id:
                current_state = self.tree.states[self.tree.current_state_id]
                branch_info = ""
                if current_state["is_branch"]:
                    branch_info = f" {Colors.YELLOW}🌿 [BRANCH]{Colors.RESET}"
                
                print(f"{Colors.BLUE}📍 Current State:{Colors.RESET} {Colors.BOLD}{self.tree.current_state_id}{Colors.RESET}{branch_info}")
                
                # Show path to current state
                path = self.tree.get_path_to_state(self.tree.current_state_id)
                if len(path) > 1:
                    path_display = f" {Colors.GRAY}→{Colors.RESET} ".join(path)
                    print(f"{Colors.GRAY}🛤️  Path:{Colors.RESET} {path_display}")
        
        self.print_separator("─", Colors.GRAY)
        print()
    
    def print_error(self, message: str):
        """Print an error message with styling"""
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    
    def print_success(self, message: str):
        """Print a success message with styling"""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    
    def print_info(self, message: str):
        """Print an info message with styling"""
        print(f"{Colors.BLUE}💡 {message}{Colors.RESET}")
    
    def print_warning(self, message: str):
        """Print a warning message with styling"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    
    def select_model(self) -> bool:
        """Let user select a model from available models"""
        print(f"{Colors.CYAN}Fetching available models...{Colors.RESET}")
        models = self.tree.get_available_models()
        
        if not models:
            self.print_error("No models found. Make sure Ollama is running and has models installed.")
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
                    self.print_success(f"Selected model: {self.current_model}")
                    return True
                else:
                    self.print_error(f"Please enter a number between 1 and {len(models)}")
            except ValueError:
                self.print_error("Please enter a valid number or 'q' to quit")
            except (EOFError, KeyboardInterrupt):
                return False
    
    def set_system_message(self):
        """Allow user to set a system message"""
        print(f"\n{Colors.BOLD}🔧 System Message Setup{Colors.RESET}")
        print("Enter a system message (or press Enter to skip):")
        
        try:
            system_msg = input(f"{Colors.CYAN}>{Colors.RESET} ").strip()
            if system_msg:
                self.system_message = system_msg
                preview = system_msg[:50] + "..." if len(system_msg) > 50 else system_msg
                self.print_success(f"System message set: {preview}")
            else:
                self.system_message = None
                self.print_info("No system message set")
        except (EOFError, KeyboardInterrupt):
            self.system_message = None
            print()
    
    def show_states(self):
        """Display all conversation states with enhanced formatting"""
        if not self.tree.states:
            print(f"{Colors.GRAY}📭 No conversation states yet.{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}🌳 Conversation Tree:{Colors.RESET}")
        self.print_separator("─", Colors.GRAY)
        self.tree.print_conversation_tree()
        self.print_separator("─", Colors.GRAY)
        
        print(f"\n{Colors.BOLD}📊 State Details:{Colors.RESET}")
        sorted_states = sorted(self.tree.states.items(), key=lambda x: x[1]["creation_order"])
        
        for state_id, state in sorted_states:
            timestamp = datetime.fromisoformat(state["timestamp"]).strftime("%H:%M:%S")
            current_marker = f" {Colors.GREEN}← CURRENT{Colors.RESET}" if state_id == self.tree.current_state_id else ""
            branch_marker = f" {Colors.YELLOW}🌿{Colors.RESET}" if state["is_branch"] else ""
            
            message_preview = state['last_user_message'][:40] + "..." if len(state['last_user_message']) > 40 else state['last_user_message']
            
            print(f"  {Colors.CYAN}{state_id}:{Colors.RESET} {message_preview} {Colors.GRAY}[{timestamp}]{Colors.RESET}{branch_marker}{current_marker}")
    
    def select_state_to_revert(self) -> bool:
        """Let user select a state to revert to with enhanced UX"""
        if not self.tree.states:
            self.print_error("No states available to revert to.")
            return False
        
        self.show_states()
        
        print(f"\n{Colors.BOLD}🔄 Revert to Previous State{Colors.RESET}")
        print(f"Current state: {Colors.CYAN}{self.tree.current_state_id}{Colors.RESET}")
        print("Available states to revert to:")
        
        sorted_states = sorted(self.tree.states.items(), key=lambda x: x[1]["creation_order"])
        
        for i, (state_id, state) in enumerate(sorted_states, 1):
            branch_marker = f" {Colors.YELLOW}🌿{Colors.RESET}" if state["is_branch"] else ""
            current_marker = f" {Colors.GREEN}← CURRENT{Colors.RESET}" if state_id == self.tree.current_state_id else ""
            message_preview = state['last_user_message'][:35] + "..." if len(state['last_user_message']) > 35 else state['last_user_message']
            
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {state_id}: {message_preview}{branch_marker}{current_marker}")
        
        while True:
            try:
                prompt = f"\n{Colors.BOLD}Select state to revert to (1-{len(sorted_states)}) or 'c' to cancel:{Colors.RESET} "
                choice = input(prompt).strip()
                
                if choice.lower() == 'c':
                    return False
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(sorted_states):
                    target_state_id = sorted_states[choice_num - 1][0]
                    
                    if target_state_id == self.tree.current_state_id:
                        self.print_warning("You're already at that state!")
                        continue
                    
                    print(f"{Colors.CYAN}🔄 Reverting to {target_state_id}...{Colors.RESET}")
                    if self.tree.revert_to_state(target_state_id):
                        self.print_success(f"Successfully reverted to {target_state_id}")
                        self.print_info("Next message will create a new branch from this state")
                        return True
                    else:
                        self.print_error(f"Failed to revert to {target_state_id}")
                        return False
                else:
                    self.print_error(f"Please enter a number between 1 and {len(sorted_states)}")
            except ValueError:
                self.print_error("Please enter a valid number or 'c' to cancel")
            except (EOFError, KeyboardInterrupt):
                return False
    
    def print_help(self):
        """Print available commands with enhanced formatting"""
        print(f"\n{Colors.BOLD}📖 Available Commands:{Colors.RESET}")
        
        commands = [
            ("/help", "Show this help message"),
            ("/states", "Show conversation tree and states"),
            ("/revert", "Revert to a previous state"),
            ("/model", "Change model"),
            ("/system", "Set system message"),
            ("/clear", "Clear screen"),
            ("/path", "Show path to current state"),
            ("/info", "Show detailed current state info"),
            ("/quit, /q", "Exit the chat")
        ]
        
        for cmd, desc in commands:
            print(f"  {Colors.CYAN}{cmd:<12}{Colors.RESET} - {desc}")
        
        print(f"\n{Colors.BOLD}💬 Chat:{Colors.RESET}")
        print("  Just type your message to chat normally!")
        
        print(f"\n{Colors.YELLOW}💡 Tip:{Colors.RESET} When you revert to a previous state and continue,")
        print("   a new branch will be created automatically!")
    
    def show_current_path(self):
        """Show the path to the current state with enhanced formatting"""
        if not self.tree.current_state_id:
            self.print_error("No current state.")
            return
        
        path = self.tree.get_path_to_state(self.tree.current_state_id)
        print(f"\n{Colors.BOLD}🛤️  Path to current state ({self.tree.current_state_id}):{Colors.RESET}")
        
        for i, state_id in enumerate(path):
            state = self.tree.states[state_id]
            indent = "  " * i
            arrow = f" {Colors.GRAY}→{Colors.RESET} " if i < len(path) - 1 else ""
            branch_marker = f" {Colors.YELLOW}🌿{Colors.RESET}" if state["is_branch"] else ""
            current_marker = f" {Colors.GREEN}← CURRENT{Colors.RESET}" if state_id == self.tree.current_state_id else ""
            
            message_preview = state['last_user_message'][:35] + "..." if len(state['last_user_message']) > 35 else state['last_user_message']
            
            print(f"{indent}{Colors.CYAN}{state_id}:{Colors.RESET} {message_preview}{branch_marker}{current_marker}{arrow}")
    
    def show_current_state_info(self):
        """Show detailed information about the current state"""
        if not self.tree.current_state_id:
            self.print_error("No current state.")
            return
        
        state = self.tree.states[self.tree.current_state_id]
        
        print(f"\n{Colors.BOLD}📊 Current State Information:{Colors.RESET}")
        self.print_separator("─", Colors.GRAY)
        
        info_items = [
            ("State ID", state['id']),
            ("Parent", state['parent_id'] or 'None (root)'),
            ("Children", ', '.join(state['children']) if state['children'] else 'None'),
            ("Depth", str(state['depth'])),
            ("Creation Order", f"#{state['creation_order']}"),
            ("Is Branch", 'Yes' if state['is_branch'] else 'No'),
            ("Timestamp", state['timestamp']),
            ("Model", state['model'])
        ]
        
        for label, value in info_items:
            print(f"{Colors.CYAN}{label}:{Colors.RESET} {value}")
        
        if state['branch_info']:
            branch_info = state['branch_info']
            print(f"{Colors.CYAN}Branch Info:{Colors.RESET}")
            print(f"  - Branched from: {branch_info['branched_from']}")
            print(f"  - Branch number: {branch_info['branch_number']}")
            print(f"  - Sibling states: {', '.join(branch_info['sibling_states'])}")
        
        print(f"\n{Colors.BOLD}Messages:{Colors.RESET}")
        print(f"{Colors.YELLOW}User:{Colors.RESET} {state['last_user_message']}")
        
        # Word wrap the assistant response
        response = state['last_assistant_message']
        wrapped_response = self._wrap_text(response, self.terminal_width - 4)
        print(f"{Colors.GREEN}Assistant:{Colors.RESET} {wrapped_response}")
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width"""
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
    
    def _format_assistant_response(self, response: str) -> str:
        """Format assistant response with proper wrapping and styling"""
        wrapped = self._wrap_text(response, self.terminal_width - 4)
        return f"{Colors.GREEN}🤖 Assistant:{Colors.RESET} {wrapped}"
    
    def chat_loop(self):
        """Main chat loop with enhanced UX"""
        self.print_help()
        
        while True:
            try:
                # Show current context with enhanced styling
                if self.tree.current_state_id:
                    current_state = self.tree.states[self.tree.current_state_id]
                    branch_indicator = ""
                    if current_state["is_branch"]:
                        branch_info = current_state["branch_info"]
                        branch_indicator = f" {Colors.YELLOW}🌿{branch_info['branch_number']}{Colors.RESET}"
                    
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
                        reverted = self.select_state_to_revert()
                        if reverted:
                            time.sleep(0.5)  # Brief pause for better UX
                            self.clear_screen()
                            self.print_header()
                    elif command == 'model':
                        if self.select_model():
                            self.clear_screen()
                            self.print_header()
                    elif command == 'system':
                        self.set_system_message()
                    elif command == 'clear':
                        self.clear_screen()
                        self.print_header()
                    elif command == 'path':
                        self.show_current_path()
                    elif command == 'info':
                        self.show_current_state_info()
                    else:
                        self.print_error(f"Unknown command: {command}. Type /help for available commands.")
                    continue
                
                # Regular chat message
                print(f"\n{Colors.CYAN}🤖 Thinking...{Colors.RESET}", end="", flush=True)
                
                try:
                    # Check if this will create a branch
                    will_branch = False
                    if self.tree.current_state_id and self.tree.current_state_id in self.tree.states:
                        current_state = self.tree.states[self.tree.current_state_id]
                        if len(current_state["children"]) > 0:
                            will_branch = True
                            print(f"\r{Colors.YELLOW}🌿 Creating new branch from {self.tree.current_state_id}...{Colors.RESET}")
                    else:
                        print(f"\r{' ' * 20}\r", end="")  # Clear "Thinking..." message
                    
                    state_id = self.tree.chat_and_save_state(
                        user_input,
                        model=self.current_model,
                        parent_state_id=self.tree.current_state_id,
                        system_message=self.system_message if not self.tree.current_state_id else None
                    )
                    
                    response = self.tree.states[state_id]["last_assistant_message"]
                    print(self._format_assistant_response(response))
                    
                    # Show branch creation info
                    new_state = self.tree.states[state_id]
                    if new_state["is_branch"]:
                        branch_info = new_state["branch_info"]
                        print(f"\n{Colors.YELLOW}🌿 Created branch {Colors.CYAN}{state_id}{Colors.RESET} {Colors.YELLOW}(Branch {branch_info['branch_number']}) from {Colors.CYAN}{branch_info['branched_from']}{Colors.RESET}")
                        if branch_info['sibling_states']:
                            siblings = ', '.join([f"{Colors.CYAN}{s}{Colors.RESET}" for s in branch_info['sibling_states']])
                            print(f"   {Colors.GRAY}Sibling branches: {siblings}{Colors.RESET}")
                    
                except Exception as e:
                        print(f"\r{Colors.RED}❌ Error: {e}{Colors.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
                break
            except EOFError:
                print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.RESET}")
                break
    
    def run(self):
        """Main entry point with enhanced startup experience"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}Welcome to Ollama Context Tree Chat! 🌳{Colors.RESET}")
        print("This tool lets you branch and revert conversations to avoid context pollution.")
        print("When you revert to a previous state and continue, it creates a new branch automatically.")
        print()
        
        # Check if Ollama is running
        try:
            models = self.tree.get_available_models()
            if not models:
                self.print_error("Cannot connect to Ollama or no models found.")
                print("Please make sure Ollama is running with: ollama serve")
                return
        except:
            self.print_error("Cannot connect to Ollama.")
            print("Please make sure Ollama is running with: ollama serve")
            return
        
        # Model selection
        if not self.select_model():
            return
        
        # Optional system message
        self.set_system_message()
        
        # Start chat
        time.sleep(0.5)  # Brief pause for better UX
        self.clear_screen()
        self.print_header()
        self.chat_loop()

def main():
    """Entry point with enhanced error handling"""
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