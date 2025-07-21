"""Command system with pattern implementation."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from core.tree import ConversationTree
from core.navigation import TreeNavigator
from llm.client import OllamaClient
from storage.persistence import ConversationPersistence
from utils.errors import TreeChatError, ValidationError
from utils.validators import parse_state_identifier, validate_tag_name

@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str = ""
    data: Any = None
    should_exit: bool = False


@dataclass
class AppContext:
    """Application context passed to commands."""
    tree: ConversationTree
    navigator: TreeNavigator
    ollama_client: OllamaClient
    persistence: ConversationPersistence
    current_model: Optional[str] = None
    system_message: Optional[str] = None


class Command(ABC):
    """Base command interface."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name."""
        pass
    
    @property
    @abstractmethod
    def aliases(self) -> List[str]:
        """Command aliases."""
        pass
    
    @abstractmethod
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        """Execute the command."""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Get help text for the command."""
        pass

class HelpCommand(Command):
    """Show help information."""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def aliases(self) -> List[str]:
        return ["h", "?"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        return CommandResult(True, "show_help", data=context)
    
    def get_help(self) -> str:
        return "Show available commands and usage information"
    
class GotoCommand(Command):
    """Navigate to specific state."""
    
    @property
    def name(self) -> str:
        return "goto"
    
    @property
    def aliases(self) -> List[str]:
        return ["g", "cd"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        if not args:
            return CommandResult(False, "Usage: /goto <state_id>")
        
        identifier = args[0]
        parsed_id = parse_state_identifier(identifier)
        
        if parsed_id is None:
            return CommandResult(False, f"Invalid state identifier: {identifier}")
        
        try:
            state = context.navigator.go_to_state(parsed_id)
            return CommandResult(True, f"Navigated to {state.display_name}")
        except TreeChatError as e:
            return CommandResult(False, str(e))
    
    def get_help(self) -> str:
        return "Navigate to any state by sequence number or hierarchical ID"


class UpCommand(Command):
    """Navigate to parent state."""
    
    @property
    def name(self) -> str:
        return "up"
    
    @property
    def aliases(self) -> List[str]:
        return ["u"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        try:
            parent = context.navigator.go_up()
            return CommandResult(True, f"Moved up to {parent.display_name}")
        except TreeChatError as e:
            return CommandResult(False, str(e))
    
    def get_help(self) -> str:
        return "Navigate to parent state"


class DownCommand(Command):
    """Navigate to child state."""
    
    @property
    def name(self) -> str:
        return "down"
    
    @property
    def aliases(self) -> List[str]:
        return ["d"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        if not args:
            return CommandResult(False, "Usage: /down <branch_number>")
        
        try:
            branch_index = int(args[0])
            child = context.navigator.go_down(branch_index)
            return CommandResult(True, f"Moved down to {child.display_name}")
        except ValueError:
            return CommandResult(False, "Branch number must be an integer")
        except TreeChatError as e:
            return CommandResult(False, str(e))
    
    def get_help(self) -> str:
        return "Navigate to specific child branch by number"


class TagCommand(Command):
    """Tag current state."""
    
    @property
    def name(self) -> str:
        return "tag"
    
    @property
    def aliases(self) -> List[str]:
        return ["t"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        current = context.tree.current_state
        if not current:
            return CommandResult(False, "No current state to tag")
        
        if not args:
            # Interactive tagging will be handled by UI
            return CommandResult(True, "interactive_tag", data=current)
        
        # Join all args as tag text (no quotes needed)
        tag_text = " ".join(args).strip()
        
        if not validate_tag_name(tag_text):
            return CommandResult(False, f"Invalid tag name: {tag_text}")
        
        # Update state with new tag
        if tag_text in current.tags:
            # Remove tag if already present
            updated_state = current.remove_tag(tag_text)
            context.tree.update_state(current.hierarchical_id, updated_state)
            return CommandResult(True, f"Removed tag: {tag_text}")
        else:
            # Add tag
            updated_state = current.add_tag(tag_text)
            context.tree.update_state(current.hierarchical_id, updated_state)
            return CommandResult(True, f"Added tag: {tag_text}")
    
    def get_help(self) -> str:
        return "Tag current state with custom text"


class StatesCommand(Command):
    """Show conversation tree."""
    
    @property
    def name(self) -> str:
        return "states"
    
    @property
    def aliases(self) -> List[str]:
        return ["s"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        if context.tree.state_count == 0:
            return CommandResult(True, "No conversation states yet.")
        
        return CommandResult(True, "show_tree", data=context.tree)
    
    def get_help(self) -> str:
        return "Show conversation tree and all states"


class SaveCommand(Command):
    """Save conversation."""
    
    @property
    def name(self) -> str:
        return "save"
    
    @property
    def aliases(self) -> List[str]:
        return ["sv"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        if context.tree.state_count == 0:
            return CommandResult(False, "No conversation to save")
        
        name = " ".join(args).strip() if args else None
        
        try:
            filename = context.persistence.save_conversation(context.tree, name)
            return CommandResult(True, f"Conversation saved as {filename}")
        except TreeChatError as e:
            return CommandResult(False, str(e))
    
    def get_help(self) -> str:
        return "Save conversation tree to file"


class LoadCommand(Command):
    """Load conversation."""
    
    @property
    def name(self) -> str:
        return "load"
    
    @property
    def aliases(self) -> List[str]:
        return ["l"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        return CommandResult(True, "show_load_menu", data=context.persistence)
    
    def get_help(self) -> str:
        return "Load conversation tree from file"


class NewCommand(Command):
    """Start new conversation."""
    
    @property
    def name(self) -> str:
        return "new"
    
    @property
    def aliases(self) -> List[str]:
        return ["n"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        context.tree.clear()
        return CommandResult(True, "Started new conversation")
    
    def get_help(self) -> str:
        return "Clear current tree and start new conversation"


class QuitCommand(Command):
    """Exit application."""
    
    @property
    def name(self) -> str:
        return "quit"
    
    @property
    def aliases(self) -> List[str]:
        return ["q", "exit"]
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        return CommandResult(True, "Goodbye!", should_exit=True)
    
    def get_help(self) -> str:
        return "Exit the application"


class TreeCommand(Command):
    """Interactive tree browser."""
    
    @property
    def name(self) -> str:
        return "tree"
    
    @property
    def aliases(self) -> List[str]:
        return []
    
    def execute(self, args: List[str], context: AppContext) -> CommandResult:
        if context.tree.state_count == 0:
            return CommandResult(False, "No conversation states to browse")
        
        return CommandResult(True, "interactive_tree", data=context.tree)
    
    def get_help(self) -> str:
        return "Interactive tree browser with live preview"


class CommandRegistry:
    """Command registration and dispatch."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}
        
        # Register built-in commands
        self._register_builtin_commands()
    
    def _register_builtin_commands(self):
        """Register all built-in commands."""
        commands = [
            HelpCommand(),
            GotoCommand(),
            UpCommand(),
            DownCommand(),
            TagCommand(),
            StatesCommand(),
            SaveCommand(),
            LoadCommand(),
            NewCommand(),
            QuitCommand(),
            TreeCommand(),
        ]
        
        for command in commands:
            self.register(command)
    
    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command
        
        for alias in command.aliases:
            self._aliases[alias] = command.name
    
    def find_command(self, name: str) -> Optional[Command]:
        """Find command by name or alias."""
        # Check direct name first
        if name in self._commands:
            return self._commands[name]
        
        # Check aliases
        if name in self._aliases:
            return self._commands[self._aliases[name]]
        
        return None
    
    def execute(self, input_line: str, context: AppContext) -> CommandResult:
        """Parse and execute command."""
        if not input_line.startswith('/'):
            return CommandResult(False, "Not a command")
        
        # Parse command and arguments
        parts = input_line[1:].split()
        if not parts:
            return CommandResult(False, "Empty command")
        
        command_name = parts[0].lower()
        args = parts[1:]
        
        command = self.find_command(command_name)
        if not command:
            return CommandResult(False, f"Unknown command: {command_name}")
        
        try:
            return command.execute(args, context)
        except Exception as e:
            return CommandResult(False, f"Command failed: {e}")
    
    def get_all_commands(self) -> List[Command]:
        """Get all registered commands."""
        return list(self._commands.values())