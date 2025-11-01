"""
Vercel Serverless Function - FastAPI Entry Point
"""
import sys
from pathlib import Path

# Add project root
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

# Method 1: Direct import (try this first)
from backend.app.main import app

# Expose at module level
app = app
