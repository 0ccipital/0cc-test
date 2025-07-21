"""Configuration settings for Ollama Context Tree Chat."""

import os
from pathlib import Path

# Ollama Settings
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = None  # Let user choose

# Display Settings
TREE_DISPLAY_MODE = 'horizontal'
MAX_MESSAGE_PREVIEW = 50
COLORS_ENABLED = True

# File Settings
HISTORY_FILE = os.path.expanduser("~/.ollama_chat_history")
DEFAULT_SAVE_DIR = os.path.expanduser("~/.ollama_conversations")
AUTO_SAVE_INTERVAL = 5  # states

# Feature Flags
QUICK_TAGGING_ENABLED = True
AUTO_BRANCH_DETECTION = True

# Ensure save directory exists
Path(DEFAULT_SAVE_DIR).mkdir(parents=True, exist_ok=True)