# api/index.py
import os, sys

# Ensure 'src' package is importable when deployed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Expose the FastAPI ASGI app for Vercel Python runtime
from src.main import app  # noqa: F401
