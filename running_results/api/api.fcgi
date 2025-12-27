#!/usr/bin/env python3
"""
FastCGI server script for DreamHost deployment.

This script allows the race results API to be deployed on DreamHost
shared hosting using FastCGI.

Setup instructions for DreamHost:
1. Upload this file and the running_results package to your web directory
2. Make this file executable: chmod +x api.fcgi
3. Create a .htaccess file to redirect requests to this script
4. Set environment variables for API keys and database path

Example .htaccess:
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ api.fcgi/$1 [QSA,L]

Environment variables (set in .htaccess or shell):
    RACE_DB_PATH: Path to SQLite database file
    RACE_API_KEYS: Comma-separated list of valid API keys
    RACE_API_SECRET_KEY: Secret key for Flask session
"""

import sys
import os

# Add the directory containing running_results to the Python path
# Adjust this path based on your deployment structure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flup.server.fcgi import WSGIServer
from running_results.api import create_app, APIConfig

# Create application with configuration from environment
config = APIConfig.from_env()

# Ensure database path is absolute
if not os.path.isabs(config.DATABASE_PATH):
    config.DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        config.DATABASE_PATH
    )

app = create_app(config=config)

if __name__ == '__main__':
    # Run with FastCGI server
    WSGIServer(app).run()
