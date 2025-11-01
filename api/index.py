"""
Vercel Entry Point for FastAPI Application
This file serves as the entry point for Vercel deployment.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Import the FastAPI app from backend
from backend.app.main import app

# Export the app instance for Vercel
__all__ = ["app"]
