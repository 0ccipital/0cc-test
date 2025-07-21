#!/usr/bin/env python3
"""Simple test runner that handles imports correctly."""

import sys
import subprocess
from pathlib import Path

def main():
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    env = {"PYTHONPATH": str(src_path)}
    
    # Run pytest with proper environment
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v"
    ], env={**dict(os.environ), **env} if 'os' in globals() else env)
    
    return result.returncode

if __name__ == "__main__":
    import os
    sys.exit(main())