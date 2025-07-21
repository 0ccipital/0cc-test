#!/usr/bin/env python3
"""Entry point script for Ollama Context Tree Chat."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now we can import from the src directory
if __name__ == "__main__":
    from main import main
    main()