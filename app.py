"""
Vercel Entry Point for FastAPI
Vercel requires an ASGI application or handler function
"""
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the FastAPI app
from backend.app.main import app

# For Vercel Python runtime - expose as handler
def handler(request):
    """Vercel serverless function handler"""
    return app

# Also expose app directly for @vercel/python
app = app
