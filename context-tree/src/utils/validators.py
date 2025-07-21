"""Input validation utilities."""

import re
from typing import Union, Optional


def validate_state_identifier(identifier: Union[int, str]) -> bool:
    """Validate state identifier format."""
    if isinstance(identifier, int):
        return identifier > 0
    
    if isinstance(identifier, str):
        # Check hierarchical format: 1, 1.1, 1.2.3, etc.
        pattern = r'^\d+(\.\d+)*$'
        return bool(re.match(pattern, identifier))
    
    return False


def validate_tag_name(tag: str) -> bool:
    """Validate tag name format."""
    if not tag or not tag.strip():
        return False
    
    # Allow alphanumeric, spaces, hyphens, underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    return bool(re.match(pattern, tag.strip()))


def validate_filename(filename: str) -> bool:
    """Validate filename for saving conversations."""
    if not filename or not filename.strip():
        return False
    
    # Basic filename validation
    invalid_chars = '<>:"/\\|?*'
    return not any(char in filename for char in invalid_chars)


def parse_state_identifier(identifier: str) -> Optional[Union[int, str]]:
    """Parse user input to state identifier."""
    identifier = identifier.strip()
    
    # Try parsing as integer first
    try:
        seq_id = int(identifier)
        return seq_id if seq_id > 0 else None
    except ValueError:
        pass
    
    # Try parsing as hierarchical ID
    if validate_state_identifier(identifier):
        return identifier
    
    return None