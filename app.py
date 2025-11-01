"""
Vercel Entry Point - Root level app.py
This is the primary entry point that Vercel searches for.
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.chdir(current_dir)

# Import the FastAPI application
from backend.app.main import app

# Vercel looks for 'app' variable
__all__ = ["app"]
