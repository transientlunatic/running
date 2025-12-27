"""
Tests for the REST API module.
"""
import pytest
import json
from running_results.api import create_app, APIConfig
from running_results.database import RaceResultsDatabase
from running_results.models import NormalizedRaceResult, RaceCategory


@pytest.fixture
def api_config(temp_database):
    """Create API configuration for testing."""
    config = APIConfig()
    config.DATABASE_PATH = temp_database
    config.API_KEYS = {'test-api-key', 'another-key'}
    config.SECRET_KEY = 'test-secret-key'
    config.DEBUG = True
    return config


@pytest.fixture
def app(api_config):
    """Create Flask test application."""
    app = create_app(config=api_config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_results():
    """Create sample race results for testing."""
    return [
        NormalizedRaceResult(
            position_overall=1,
            name='John Smith',
            club='Running Club',
            gender='M',
            age_category='M40',
            finish_time_seconds=1800,
            race_status='finished'
        ),
        NormalizedRaceResult(
            position_overall=2,
            name='Jane Doe',
            club='Athletics Club',
            gender='F',
            age_category='F35',
            finish_time_seconds=1850,
            race_status='finished'
        ),
    ]


@pytest.fixture
def populated_db(temp_database, sample_results):
    """Create a database with sample data."""
    with RaceResultsDatabase(temp_database) as db:
        db.add_results(
            results=sample_results,
            race_name='Test Race',
            race_year=2024,
            race_category=RaceCategory.ROAD_RACE
        )
    return temp_database


class TestAPIBasics:
    """Test basic API functionality."""
    
    def test_index_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'name' in data
        assert 'version' in data
        assert 'endpoints' in data
        assert data['name'] == 'Race Results API'
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['database'] == 'connected'
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data


class TestRaceEndpoints:
    """Test race-related endpoints."""
    
    def test_list_races_empty(self, client):
        """Test listing races when database is empty."""
        response = client.get('/api/races')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'races' in data
        assert 'count' in data
        assert isinstance(data['races'], list)
    
    def test_list_races_with_data(self, client, api_config, populated_db):
        """Test listing races with data in database."""
        # Update app to use populated database
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['count'] == 1
        assert len(data['races']) == 1
        assert data['races'][0]['race_name'] == 'Test Race'
    
    def test_get_race(self, client, populated_db):
        """Test getting a specific race."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['race_name'] == 'Test Race'
        assert 'total_results' in data
    
    def test_get_nonexistent_race(self, client):
        """Test getting a race that doesn't exist."""
        response = client.get('/api/races/Nonexistent%20Race')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_race_with_results(self, client, populated_db):
        """Test getting race with results included."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race?include_results=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'results' in data
        assert 'results_count' in data
        assert len(data['results']) == 2


class TestResultsEndpoints:
    """Test results query endpoints."""
    
    def test_get_race_results(self, client, populated_db):
        """Test getting race results."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/results')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'results' in data
        assert 'count' in data
        assert 'total' in data
        assert len(data['results']) == 2
    
    def test_get_race_results_with_year(self, client, populated_db):
        """Test filtering race results by year."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/results?year=2024')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['results']) == 2
    
    def test_get_race_results_with_pagination(self, client, populated_db):
        """Test pagination of race results."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/results?limit=1&offset=0')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['total'] == 2
        assert data['limit'] == 1
        assert data['offset'] == 0

    def test_get_race_results_with_negative_limit(self, client, populated_db):
        """Test that negative limit is handled gracefully."""
        client.application.config["DATABASE_PATH"] = populated_db

        response = client.get("/api/races/Test%20Race/results?limit=-1")
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should use default page size, not the negative value
        assert data["count"] >= 0

    def test_get_race_results_with_negative_offset(self, client, populated_db):
        """Test that negative offset is handled gracefully."""
        client.application.config["DATABASE_PATH"] = populated_db

        response = client.get("/api/races/Test%20Race/results?offset=-10")
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should use offset of 0
        assert data["offset"] == 0
    
    def test_get_race_results_by_runner(self, client, populated_db):
        """Test filtering results by runner name."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/results?runner_name=John')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['results'][0]['name'] == 'John Smith'
    
    def test_get_race_results_by_club(self, client, populated_db):
        """Test filtering results by club."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/results?club=Running')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['results'][0]['club'] == 'Running Club'
    
    def test_get_race_year_results(self, client, populated_db):
        """Test getting results for specific race and year."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/years/2024')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['race_name'] == 'Test Race'
        assert data['year'] == 2024
        assert len(data['results']) == 2
    
    def test_get_race_year_results_not_found(self, client, populated_db):
        """Test getting results for year with no data."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/races/Test%20Race/years/2023')
        assert response.status_code == 404


class TestRunnerEndpoints:
    """Test runner history endpoints."""
    
    def test_get_runner_history(self, client, populated_db):
        """Test getting runner history."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/runner/John%20Smith')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['runner_name'] == 'John Smith'
        assert len(data['results']) == 1
        assert data['count'] == 1
        assert 'races' in data
    
    def test_get_runner_history_not_found(self, client):
        """Test getting history for nonexistent runner."""
        response = client.get('/api/runner/Nonexistent%20Runner')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_runner_history_filtered_by_race(self, client, populated_db):
        """Test filtering runner history by race."""
        client.application.config['DATABASE_PATH'] = populated_db
        
        response = client.get('/api/runner/John%20Smith?race_name=Test%20Race')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['results']) == 1


class TestAddResultsEndpoint:
    """Test adding results via API."""
    
    def test_add_results_without_api_key(self, client):
        """Test that adding results without API key fails."""
        response = client.post('/api/results', json={
            'race_name': 'Test Race',
            'results': []
        })
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'API key required'
    
    def test_add_results_with_invalid_api_key(self, client):
        """Test that adding results with invalid API key fails."""
        response = client.post('/api/results',
            json={'race_name': 'Test Race', 'results': []},
            headers={'X-API-Key': 'invalid-key'}
        )
        assert response.status_code == 403
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Invalid API key'
    
    def test_add_results_with_api_key_header(self, client):
        """Test adding results with valid API key in header."""
        new_results = {
            'race_name': 'New Race',
            'race_year': 2024,
            'race_category': '10k',
            'results': [
                {
                    'name': 'Test Runner',
                    'position_overall': 1,
                    'finish_time_seconds': 1800,
                    'club': 'Test Club'
                }
            ]
        }
        
        response = client.post('/api/results',
            json=new_results,
            headers={'X-API-Key': 'test-api-key'}
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 1
        assert data['race_name'] == 'New Race'
    
    def test_add_results_with_api_key_query_param(self, client):
        """Test adding results with API key in query parameter."""
        new_results = {
            'race_name': 'New Race',
            'results': [
                {'name': 'Test Runner', 'position_overall': 1}
            ]
        }
        
        response = client.post('/api/results?api_key=test-api-key',
            json=new_results
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_add_results_with_bearer_token(self, client):
        """Test adding results with Bearer token."""
        new_results = {
            'race_name': 'New Race',
            'results': [
                {'name': 'Test Runner', 'position_overall': 1}
            ]
        }
        
        response = client.post('/api/results',
            json=new_results,
            headers={'Authorization': 'Bearer test-api-key'}
        )
        assert response.status_code == 201
    
    def test_add_results_missing_race_name(self, client):
        """Test that adding results without race_name fails."""
        response = client.post('/api/results',
            json={'results': []},
            headers={'X-API-Key': 'test-api-key'}
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_results_missing_results_array(self, client):
        """Test that adding results without results array fails."""
        response = client.post('/api/results',
            json={'race_name': 'Test Race'},
            headers={'X-API-Key': 'test-api-key'}
        )
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_results_with_column_mapping(self, client):
        """Test adding results with custom column mapping."""
        new_results = {
            'race_name': 'Mapped Race',
            'race_year': 2024,
            'column_mapping': {
                'position_overall': 'Pos',
                'name': 'Runner',
                'finish_time_seconds': 'Time'
            },
            'results': [
                {
                    'Pos': 1,
                    'Runner': 'Test Runner',
                    'Time': 1800
                }
            ]
        }
        
        response = client.post('/api/results',
            json=new_results,
            headers={'X-API-Key': 'test-api-key'}
        )
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['count'] == 1
    
    def test_add_results_invalid_data(self, client):
        """Test that adding results with invalid data fails gracefully."""
        new_results = {
            'race_name': 'Bad Race',
            'results': [
                {'invalid_field': 'value'}
            ]
        }
        
        # Should succeed but with empty/partial data
        response = client.post('/api/results',
            json=new_results,
            headers={'X-API-Key': 'test-api-key'}
        )
        # Should either succeed with partial data or fail with 400
        assert response.status_code in [201, 400]

    def test_add_results_with_large_array(self, client):
        """Test that large result arrays are rejected."""
        # Create a large array exceeding the limit
        large_results = [
            {"name": f"Runner {i}", "position_overall": i}
            for i in range(10001)  # Exceeds MAX_RESULTS_PER_REQUEST
        ]

        response = client.post(
            "/api/results",
            json={"race_name": "Large Race", "results": large_results},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "Too many results" in data["error"]


class TestAPISecurityFeatures:
    """Test security features of the API."""

    def test_api_key_timing_safe_comparison(self, api_config):
        """Test that API key comparison uses timing-safe method."""
        api_config.add_api_key("valid-key")

        # This test verifies the function works correctly
        # Timing attack resistance can't be easily tested in unit tests
        assert api_config.is_valid_api_key("valid-key")
        assert not api_config.is_valid_api_key("invalid-key")

    def test_config_path_traversal_protection(self, tmp_path):
        """Test that config loading prevents path traversal."""
        import os
        from running_results.api import APIConfig

        # Create a directory structure for testing
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        unsafe_dir = tmp_path / "unsafe"
        unsafe_dir.mkdir()

        # Create a config file outside the safe directory
        unsafe_config = unsafe_dir / "bad_config.py"
        unsafe_config.write_text("API_KEYS = {'hacked'}")

        # Save current directory
        original_dir = os.getcwd()
        try:
            # Change to safe directory
            os.chdir(safe_dir)

            # Try to load config from outside directory using relative path
            # Calculate relative path from safe_dir to unsafe_config
            relative_path = os.path.relpath(unsafe_config, safe_dir)

            # This should fail because it tries to access outside current working directory
            with pytest.raises(ValueError, match="current working directory"):
                APIConfig.from_file(str(relative_path))
        finally:
            # Restore original directory
            os.chdir(original_dir)

    def test_sanitized_error_messages(self, client):
        """Test that error messages don't expose internal details."""
        # Force an error by querying non-existent race
        response = client.get("/api/races/NonexistentRace")
        assert response.status_code == 404

        data = json.loads(response.data)
        # Error message should be generic, not exposing database internals
        assert "error" in data
        assert "stack" not in str(data).lower()
        assert "traceback" not in str(data).lower()


class TestAPIConfig:
    """Test API configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = APIConfig()
        assert config.DATABASE_PATH is not None
        assert isinstance(config.API_KEYS, set)
        assert config.CORS_ENABLED is not None
    
    def test_add_api_key(self):
        """Test adding API key."""
        config = APIConfig()
        config.add_api_key('new-key')
        assert 'new-key' in config.API_KEYS
    
    def test_remove_api_key(self):
        """Test removing API key."""
        config = APIConfig()
        config.add_api_key('test-key')
        config.remove_api_key('test-key')
        assert 'test-key' not in config.API_KEYS
    
    def test_is_valid_api_key(self):
        """Test API key validation."""
        config = APIConfig()
        config.add_api_key('valid-key')
        assert config.is_valid_api_key('valid-key')
        assert not config.is_valid_api_key('invalid-key')
