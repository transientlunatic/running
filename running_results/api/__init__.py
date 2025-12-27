"""
RESTful API for race results database.

This module provides a Flask-based REST API for accessing and managing
race results stored in the database. The API supports authentication
using API keys and can be deployed on shared hosting with FastCGI.

Example usage:
    >>> from running_results.api import create_app
    >>> app = create_app(db_path='race_results.db')
    >>> app.run(debug=True)
"""

from .app import create_app, get_app
from .auth import require_api_key
from .config import APIConfig

__all__ = ['create_app', 'get_app', 'require_api_key', 'APIConfig']
