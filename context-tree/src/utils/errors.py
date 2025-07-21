"""Exception hierarchy for the application."""

from typing import Union


class TreeChatError(Exception):
    """Base exception for all application errors."""
    pass


class TreeOperationError(TreeChatError):
    """Errors related to tree operations."""
    pass


class StateNotFoundError(TreeOperationError):
    """Specific state lookup failures."""
    
    def __init__(self, identifier: Union[int, str]):
        self.identifier = identifier
        super().__init__(f"State not found: {identifier}")


class NavigationError(TreeOperationError):
    """Navigation failures with suggested alternatives."""
    
    def __init__(self, message: str, suggestions: list = None):
        self.suggestions = suggestions or []
        super().__init__(message)


class LLMError(TreeChatError):
    """LLM communication errors."""
    pass


class StreamingError(LLMError):
    """Streaming-specific errors."""
    pass


class PersistenceError(TreeChatError):
    """Save/load operation errors."""
    pass


class ValidationError(TreeChatError):
    """Input validation errors."""
    pass