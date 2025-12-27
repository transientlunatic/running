"""
API authentication utilities.

Provides API key authentication for protected endpoints.
"""

from functools import wraps
from flask import request, jsonify, current_app
from typing import Callable


def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require API key authentication for an endpoint.

    The API key can be provided in three ways:
    1. Header: X-API-Key: <your-api-key>
    2. Query parameter: ?api_key=<your-api-key>
    3. Bearer token: Authorization: Bearer <your-api-key>

    Example:
        @app.route('/api/results', methods=['POST'])
        @require_api_key
        def add_results():
            # This endpoint requires authentication
            return {'status': 'success'}

    Returns:
        Decorated function that checks API key before executing
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in multiple locations
        api_key = None

        # 1. Check X-API-Key header
        api_key = request.headers.get("X-API-Key")

        # 2. Check query parameter
        if not api_key:
            api_key = request.args.get("api_key")

        # 3. Check Authorization header (Bearer token)
        if not api_key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix

        # Validate API key
        if not api_key:
            return (
                jsonify(
                    {
                        "error": "API key required",
                        "message": (
                            "Provide API key via X-API-Key header, "
                            "api_key query parameter, or Authorization Bearer token"
                        ),
                    }
                ),
                401,
            )

        # Get config from app
        config = current_app.config.get("API_CONFIG")
        if not config or not config.is_valid_api_key(api_key):
            return (
                jsonify(
                    {
                        "error": "Invalid API key",
                        "message": "The provided API key is not valid",
                    }
                ),
                403,
            )

        return f(*args, **kwargs)

    return decorated_function
