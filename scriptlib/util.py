"""Utility functions for scriptlib.

IMPORTANT: Best to avoid cicular imports
"""
import os

def get_install_base() -> str:
    """Return the directory one level above the scriptlib directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
