#!/usr/bin/env python3
"""
Example script demonstrating the Race Results API usage.

This script shows how to:
1. Start the API server
2. Query race results
3. Add new results

Run this script to start a local development server:
    python examples/api_example.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import running_results
sys.path.insert(0, str(Path(__file__).parent.parent))

from running_results.api import create_app, APIConfig
from running_results.database import RaceResultsDatabase
from running_results.models import NormalizedRaceResult, RaceCategory


def setup_sample_database(db_path='example_race_results.db'):
    """Create a sample database with some test data."""
    print(f"Setting up sample database at {db_path}...")
    
    # Create sample results
    sample_results = [
        NormalizedRaceResult(
            position_overall=1,
            name='Alice Johnson',
            club='Edinburgh AC',
            gender='F',
            age_category='F35',
            finish_time_seconds=1980,  # 33:00
            race_status='finished'
        ),
        NormalizedRaceResult(
            position_overall=2,
            name='Bob Smith',
            club='Carnethy',
            gender='M',
            age_category='M40',
            finish_time_seconds=2040,  # 34:00
            race_status='finished'
        ),
        NormalizedRaceResult(
            position_overall=3,
            name='Carol Williams',
            club='Running Club',
            gender='F',
            age_category='F40',
            finish_time_seconds=2100,  # 35:00
            race_status='finished'
        ),
    ]
    
    # Add to database
    with RaceResultsDatabase(db_path) as db:
        db.add_results(
            results=sample_results,
            race_name='Example 10K',
            race_year=2024,
            race_category=RaceCategory.TEN_K
        )
    
    print(f"✓ Added {len(sample_results)} sample results to database")


def main():
    """Run the API server with sample data."""
    import os
    
    # Set up sample database
    db_path = 'example_race_results.db'
    if not os.path.exists(db_path):
        setup_sample_database(db_path)
    
    # Create API configuration
    config = APIConfig()
    config.DATABASE_PATH = db_path
    config.API_KEYS = {
        'demo-api-key-123',  # Example API key for testing
        'another-demo-key'
    }
    config.DEBUG = True
    
    # Create and run app
    app = create_app(config=config)
    
    print("\n" + "="*60)
    print("Race Results API - Example Server")
    print("="*60)
    print("\nServer starting at: http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  - GET  /                           API information")
    print("  - GET  /api/health                 Health check")
    print("  - GET  /api/races                  List all races")
    print("  - GET  /api/races/Example 10K      Get race details")
    print("  - GET  /api/races/Example 10K/results  Get race results")
    print("  - GET  /api/runner/Alice           Get runner history")
    print("  - POST /api/results                Add new results (requires API key)")
    print("\nAPI Keys for testing:")
    print("  - demo-api-key-123")
    print("  - another-demo-key")
    print("\nExample cURL commands:")
    print("\n  # List races")
    print("  curl http://localhost:5000/api/races")
    print("\n  # Get race results")
    print("  curl http://localhost:5000/api/races/Example%2010K/results")
    print("\n  # Add new results (with API key)")
    print("  curl -X POST http://localhost:5000/api/results \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -H 'X-API-Key: demo-api-key-123' \\")
    print("    -d '{")
    print('      "race_name": "Test Race",')
    print('      "race_year": 2024,')
    print('      "results": [')
    print('        {"name": "Test Runner", "position_overall": 1, "finish_time_seconds": 1800}')
    print('      ]')
    print("    }'")
    print("\n" + "="*60)
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the Flask development server
    # WARNING: This is for development/demo purposes only!
    # DO NOT use in production. Use a production WSGI server instead.
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
