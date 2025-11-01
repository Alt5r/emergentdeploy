"""
Vercel Serverless Function for FastAPI
This wraps the FastAPI app as a Vercel serverless function
"""
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Import FastAPI app
from backend.app.main import app

# Export for Vercel
app = app
