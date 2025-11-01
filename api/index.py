"""
Vercel Entry Point for FastAPI Application
This file serves as the entry point for Vercel deployment.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Set environment to ensure proper imports
os.chdir(root_dir)

# Import the FastAPI app from backend
try:
    from backend.app.main import app
except ImportError as e:
    # Fallback: create a simple FastAPI app if import fails
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"error": f"Failed to import main app: {str(e)}"}

# This is what Vercel looks for
application = app

# Export both for compatibility
__all__ = ["app", "application"]
