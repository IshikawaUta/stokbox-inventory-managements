"""Vercel Serverless Handler — Adapt Fenrir app untuk Vercel Python Runtime."""
import sys
import os

# Tambah project root ke path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app
from app import app

# Vercel expects an ASGI/WSGI app
# Fenrir is ASGI-compatible
handler = app
