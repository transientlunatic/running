"""
Flask application for race results REST API.

This module creates and configures the Flask application with all
API routes for accessing and managing race results.
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime

from ..database import RaceResultsDatabase
from ..models import NormalizedRaceResult, normalize_race_results, ColumnMapping
from .config import APIConfig
from .auth import require_api_key


def create_app(
    config: Optional[APIConfig] = None,
    db_path: Optional[str] = None
) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: APIConfig instance (if None, uses default config)
        db_path: Path to database (overrides config.DATABASE_PATH if provided)
        
    Returns:
        Configured Flask application
        
    Example:
        >>> app = create_app(db_path='race_results.db')
        >>> app.run(host='0.0.0.0', port=5000)
    """
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = APIConfig()
    
    if db_path:
        config.DATABASE_PATH = db_path
    
    app.config['API_CONFIG'] = config
    app.config['DATABASE_PATH'] = config.DATABASE_PATH
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Enable CORS if configured
    if config.CORS_ENABLED:
        CORS(app)
    
    # Register routes
    register_routes(app)
    
    # Error handlers
    register_error_handlers(app)
    
    return app


def get_db() -> RaceResultsDatabase:
    """
    Get database connection for current request.
    
    Creates a new connection if one doesn't exist for this request.
    Connection is stored in Flask's g object and closed after request.
    """
    if 'db' not in g:
        from flask import current_app
        db_path = current_app.config['DATABASE_PATH']
        g.db = RaceResultsDatabase(db_path)
    return g.db


def close_db(error=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def register_routes(app: Flask) -> None:
    """Register all API routes."""
    
    # Clean up database connections after each request
    app.teardown_appcontext(close_db)
    
    @app.route('/')
    def index():
        """API root endpoint with basic information."""
        return jsonify({
            'name': 'Race Results API',
            'version': '1.0.0',
            'description': 'RESTful API for managing and querying running race results',
            'endpoints': {
                'GET /api/races': 'List all races',
                'GET /api/races/<race_name>': 'Get race details',
                'GET /api/races/<race_name>/results': 'Get race results',
                'GET /api/races/<race_name>/years/<year>': 'Get results for specific year',
                'GET /api/runner/<name>': 'Get runner history',
                'POST /api/results': 'Add new results (requires API key)',
                'GET /api/health': 'Health check endpoint'
            },
            'authentication': 'API key required for POST endpoints (X-API-Key header or api_key query param)'
        })
    
    @app.route('/api/health')
    def health():
        """Health check endpoint."""
        try:
            db = get_db()
            # Simple query to verify database is accessible
            db.get_races()
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 503
    
    @app.route('/api/races', methods=['GET'])
    def list_races():
        """
        List all races in the database.
        
        Returns:
            JSON array of race information including:
            - race_name
            - race_category
            - num_years (number of years with data)
            - first_year and last_year
            - total_results
            
        Example:
            GET /api/races
            
            Response:
            {
                "races": [
                    {
                        "race_name": "Edinburgh Marathon",
                        "race_category": "marathon",
                        "num_years": 3,
                        "first_year": 2022,
                        "last_year": 2024,
                        "total_results": 15000
                    }
                ],
                "count": 1
            }
        """
        try:
            db = get_db()
            races_df = db.get_races()
            
            return jsonify({
                'races': races_df.to_dict('records'),
                'count': len(races_df)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/races/<race_name>', methods=['GET'])
    def get_race(race_name: str):
        """
        Get details about a specific race.
        
        Args:
            race_name: Name of the race
            
        Query parameters:
            include_results: If 'true', include all results (default: false)
            
        Returns:
            JSON object with race details and optionally all results
            
        Example:
            GET /api/races/Edinburgh%20Marathon
        """
        try:
            db = get_db()
            
            # Get race summary
            races_df = db.get_races()
            race_info = races_df[races_df['race_name'] == race_name]
            
            if race_info.empty:
                return jsonify({'error': 'Race not found'}), 404
            
            response = race_info.to_dict('records')[0]
            
            # Include results if requested
            if request.args.get('include_results', 'false').lower() == 'true':
                results_df = db.get_race_results(race_name=race_name)
                response['results'] = results_df.to_dict('records')
                response['results_count'] = len(results_df)
            
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/races/<race_name>/results', methods=['GET'])
    def get_race_results(race_name: str):
        """
        Get results for a specific race.
        
        Args:
            race_name: Name of the race
            
        Query parameters:
            year: Filter by specific year
            runner_name: Filter by runner name (partial match)
            club: Filter by club name (partial match)
            limit: Maximum number of results (default: 100, max: 1000)
            offset: Number of results to skip (for pagination)
            
        Returns:
            JSON object with results array and metadata
            
        Example:
            GET /api/races/Edinburgh%20Marathon/results?year=2024&limit=50
        """
        try:
            db = get_db()
            
            # Parse query parameters
            year = request.args.get('year', type=int)
            runner_name = request.args.get('runner_name')
            club = request.args.get('club')
            limit = min(
                request.args.get('limit', 100, type=int),
                app.config['API_CONFIG'].MAX_PAGE_SIZE
            )
            offset = request.args.get('offset', 0, type=int)
            
            # Query database
            results_df = db.get_race_results(
                race_name=race_name,
                year=year,
                runner_name=runner_name,
                club=club
            )
            
            if results_df.empty:
                return jsonify({
                    'results': [],
                    'count': 0,
                    'total': 0
                })
            
            # Apply pagination
            total = len(results_df)
            results_df = results_df.iloc[offset:offset + limit]
            
            return jsonify({
                'results': results_df.to_dict('records'),
                'count': len(results_df),
                'total': total,
                'offset': offset,
                'limit': limit
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/races/<race_name>/years/<int:year>', methods=['GET'])
    def get_race_year_results(race_name: str, year: int):
        """
        Get results for a specific race and year.
        
        Args:
            race_name: Name of the race
            year: Year of the race
            
        Returns:
            JSON object with results for that year
            
        Example:
            GET /api/races/Edinburgh%20Marathon/years/2024
        """
        try:
            db = get_db()
            results_df = db.get_race_results(race_name=race_name, year=year)
            
            if results_df.empty:
                return jsonify({
                    'error': 'No results found',
                    'race_name': race_name,
                    'year': year
                }), 404
            
            return jsonify({
                'race_name': race_name,
                'year': year,
                'results': results_df.to_dict('records'),
                'count': len(results_df)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/runner/<name>', methods=['GET'])
    def get_runner_history(name: str):
        """
        Get race history for a specific runner.
        
        Args:
            name: Runner name (partial match supported)
            
        Query parameters:
            race_name: Filter by specific race
            
        Returns:
            JSON object with runner's race history
            
        Example:
            GET /api/runner/John%20Smith
        """
        try:
            db = get_db()
            race_name = request.args.get('race_name')
            
            results_df = db.get_runner_history(
                runner_name=name,
                race_name=race_name
            )
            
            if results_df.empty:
                return jsonify({
                    'error': 'No results found for runner',
                    'runner_name': name
                }), 404
            
            return jsonify({
                'runner_name': name,
                'results': results_df.to_dict('records'),
                'count': len(results_df),
                'races': results_df['race_name'].unique().tolist()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/results', methods=['POST'])
    @require_api_key
    def add_results():
        """
        Add new race results to the database.
        
        Requires API key authentication via X-API-Key header or api_key query parameter.
        
        Request body should be JSON with:
            - race_name: Name of the race (required)
            - race_year: Year of the race (optional)
            - race_category: Category of race (optional)
            - results: Array of result objects (required)
            - column_mapping: Optional mapping of column names (if results use non-standard fields)
            
        Each result object should contain standard fields like:
            - name, position_overall, finish_time_seconds, club, etc.
            
        Returns:
            JSON object with status and count of results added
            
        Example:
            POST /api/results
            Headers: X-API-Key: your-api-key-here
            Body:
            {
                "race_name": "Test Race",
                "race_year": 2024,
                "race_category": "10k",
                "results": [
                    {
                        "name": "John Smith",
                        "position_overall": 1,
                        "finish_time_seconds": 1800,
                        "club": "Running Club"
                    }
                ]
            }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            race_name = data.get('race_name')
            if not race_name:
                return jsonify({'error': 'race_name is required'}), 400
            
            results_data = data.get('results')
            if not results_data:
                return jsonify({'error': 'results array is required'}), 400
            
            if not isinstance(results_data, list):
                return jsonify({'error': 'results must be an array'}), 400
            
            # Parse optional parameters
            race_year = data.get('race_year')
            race_category = data.get('race_category')
            source_url = data.get('source_url')
            
            # Convert results to NormalizedRaceResult objects
            try:
                # If column_mapping is provided, use it
                column_mapping = data.get('column_mapping')
                if column_mapping:
                    mapping = ColumnMapping(**column_mapping)
                    df = pd.DataFrame(results_data)
                    normalized_results = normalize_race_results(
                        df,
                        mapping=mapping,
                        race_name=race_name,
                        race_year=race_year,
                        race_category=race_category
                    )
                else:
                    # Assume results are already in standard format
                    # Validate each result using Pydantic
                    normalized_results = []
                    for i, result in enumerate(results_data):
                        try:
                            normalized_results.append(NormalizedRaceResult(**result))
                        except Exception as e:
                            return jsonify({
                                'error': f'Invalid result data at index {i}',
                                'message': str(e),
                                'result': result
                            }), 400
            except Exception as e:
                return jsonify({
                    'error': 'Invalid result data',
                    'message': str(e)
                }), 400
            
            # Add to database
            db = get_db()
            count = db.add_results(
                results=normalized_results,
                race_name=race_name,
                race_year=race_year,
                race_category=race_category,
                source_url=source_url
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Added {count} results',
                'race_name': race_name,
                'race_year': race_year,
                'count': count
            }), 201
            
        except Exception as e:
            return jsonify({
                'error': 'Failed to add results',
                'message': str(e)
            }), 500


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'The request was invalid'
        }), 400


def get_app() -> Flask:
    """
    Get or create the Flask application instance.
    
    This is useful for WSGI servers and FastCGI deployment.
    
    Returns:
        Flask application instance
    """
    return create_app()


# For FastCGI/WSGI deployment (e.g., on DreamHost)
application = get_app()


if __name__ == '__main__':
    # Development server - DO NOT use in production!
    # For production, use a WSGI server like Gunicorn or FastCGI
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
