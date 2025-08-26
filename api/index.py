"""
Vercel API handler for Baltic Exchange Scraper
This file is specifically for Vercel serverless deployment
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app

# Export the FastAPI app for Vercel
handler = app
