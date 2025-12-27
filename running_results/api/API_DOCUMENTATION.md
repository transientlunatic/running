# Race Results REST API Documentation

## Overview

The Race Results REST API provides programmatic access to running race results stored in a SQLite database. The API supports querying race results, runner histories, and adding new results with API key authentication.

## Base URL

```
http://your-domain.com/api
```

For local development:
```
http://localhost:5000/api
```

## Authentication

Protected endpoints (currently only `POST /api/results`) require API key authentication. The API key can be provided in two ways:

1. **X-API-Key Header** (recommended):
   ```
   X-API-Key: your-api-key-here
   ```

2. **Authorization Bearer Token**:
   ```
   Authorization: Bearer your-api-key-here
   ```

3. **Query Parameter** (DEPRECATED - security risk):
   ```
   ?api_key=your-api-key-here
   ```
   **⚠️ Security Warning:** Passing API keys in query parameters is strongly discouraged because URLs (including query strings) are logged in browser history, server logs, and intermediary proxies, potentially exposing your API key. Use the `X-API-Key` header or the `Authorization` header instead.

## Endpoints

### GET /

Returns API information and available endpoints.

**Response:**
```json
{
  "name": "Race Results API",
  "version": "1.0.0",
  "description": "RESTful API for managing and querying running race results",
  "endpoints": { ... }
}
```

### GET /api/health

Health check endpoint to verify API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00",
  "database": "connected"
}
```

### GET /api/races

List all races in the database.

**Response:**
```json
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
```

### GET /api/races/{race_name}

Get details about a specific race.

**Parameters:**
- `race_name` (path): Name of the race (URL-encoded)

**Query Parameters:**
- `include_results` (optional): Set to `true` to include all results

**Example:**
```
GET /api/races/Edinburgh%20Marathon
```

**Response:**
```json
{
  "race_name": "Edinburgh Marathon",
  "race_category": "marathon",
  "num_years": 3,
  "first_year": 2022,
  "last_year": 2024,
  "total_results": 15000
}
```

### GET /api/races/{race_name}/results

Get results for a specific race.

**Parameters:**
- `race_name` (path): Name of the race (URL-encoded)

**Query Parameters:**
- `year` (optional, integer): Filter by specific year
- `runner_name` (optional, string): Filter by runner name (partial match)
- `club` (optional, string): Filter by club name (partial match)
- `limit` (optional, integer): Maximum results to return (default: 100, max: 1000)
- `offset` (optional, integer): Number of results to skip (for pagination)

**Example:**
```
GET /api/races/Edinburgh%20Marathon/results?year=2024&limit=50
```

**Response:**
```json
{
  "results": [
    {
      "race_name": "Edinburgh Marathon",
      "race_year": 2024,
      "position_overall": 1,
      "name": "John Smith",
      "club": "Edinburgh AC",
      "finish_time_seconds": 8892,
      "finish_time_minutes": 148.2,
      "gender": "M",
      "age_category": "M40"
    }
  ],
  "count": 50,
  "total": 15000,
  "offset": 0,
  "limit": 50
}
```

### GET /api/races/{race_name}/years/{year}

Get results for a specific race and year.

**Parameters:**
- `race_name` (path): Name of the race (URL-encoded)
- `year` (path, integer): Year of the race

**Example:**
```
GET /api/races/Edinburgh%20Marathon/years/2024
```

**Response:**
```json
{
  "race_name": "Edinburgh Marathon",
  "year": 2024,
  "results": [...],
  "count": 15000
}
```

### GET /api/runner/{name}

Get race history for a specific runner.

**Parameters:**
- `name` (path): Runner name (partial match supported, URL-encoded)

**Query Parameters:**
- `race_name` (optional): Filter by specific race

**Example:**
```
GET /api/runner/John%20Smith
```

**Response:**
```json
{
  "runner_name": "John Smith",
  "results": [
    {
      "race_name": "Edinburgh Marathon",
      "race_year": 2024,
      "position_overall": 1,
      "finish_time_minutes": 148.2,
      "club": "Edinburgh AC"
    }
  ],
  "count": 5,
  "races": ["Edinburgh Marathon", "Great Scottish Run"]
}
```

### POST /api/results

Add new race results to the database. **Requires API key authentication.**

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "race_name": "Test Race",
  "race_year": 2024,
  "race_category": "10k",
  "source_url": "https://example.com/results",
  "results": [
    {
      "name": "John Smith",
      "position_overall": 1,
      "finish_time_seconds": 1800,
      "club": "Running Club",
      "gender": "M",
      "age_category": "M40"
    },
    {
      "name": "Jane Doe",
      "position_overall": 2,
      "finish_time_seconds": 1850,
      "club": "Athletics Club",
      "gender": "F",
      "age_category": "F35"
    }
  ]
}
```

**Optional Field - Column Mapping:**

If your data uses non-standard column names, provide a `column_mapping` object:

```json
{
  "race_name": "Test Race",
  "race_year": 2024,
  "column_mapping": {
    "position_overall": "Pos",
    "name": "Runner Name",
    "finish_time_seconds": "Time (sec)",
    "club": "Team"
  },
  "results": [...]
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Added 2 results",
  "race_name": "Test Race",
  "race_year": 2024,
  "count": 2
}
```

**Response (Error - No API Key):**
```json
{
  "error": "API key required",
  "message": "Provide API key via X-API-Key header, api_key query parameter, or Authorization Bearer token"
}
```
HTTP Status: 401

**Response (Error - Invalid API Key):**
```json
{
  "error": "Invalid API key",
  "message": "The provided API key is not valid"
}
```
HTTP Status: 403

## Error Responses

All endpoints may return error responses with appropriate HTTP status codes:

### 400 Bad Request
```json
{
  "error": "Bad request",
  "message": "The request was invalid"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "message": "The requested resource was not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

### 503 Service Unavailable
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T12:00:00",
  "error": "Database connection failed"
}
```

## Data Models

### Race Result Object

Standard fields for race results:

- `position_overall` (integer, optional): Overall finishing position
- `position_gender` (integer, optional): Position within gender category
- `position_category` (integer, optional): Position within age category
- `name` (string, optional): Runner name
- `bib_number` (string, optional): Race bib number
- `gender` (string, optional): M, F, N, or U
- `age_category` (string, optional): Age category (e.g., M40, F35)
- `club` (string, optional): Running club
- `race_status` (string, optional): finished, dnf, dns, or dsq
- `finish_time_seconds` (float, optional): Finish time in seconds
- `finish_time_minutes` (float, optional): Finish time in minutes
- `chip_time_seconds` (float, optional): Chip time in seconds
- `chip_time_minutes` (float, optional): Chip time in minutes
- `gun_time_seconds` (float, optional): Gun time in seconds
- `gun_time_minutes` (float, optional): Gun time in minutes

### Race Categories

Valid race category values:
- `ultra`
- `marathon`
- `half_marathon`
- `10k`
- `5k`
- `parkrun`
- `fell_race`
- `road_race`
- `unknown`

## Configuration

### Environment Variables

Configure the API using environment variables:

- `RACE_DB_PATH`: Path to SQLite database file (default: `race_results.db`)
- `RACE_API_KEYS`: Comma-separated list of valid API keys
- `RACE_API_CORS`: Enable CORS (default: `true`)
- `RACE_API_DEBUG`: Enable debug mode (default: `false`, should be `false` in production)
- `RACE_API_SECRET_KEY`: Flask secret key (required for production)

Example:
```bash
export RACE_DB_PATH=/path/to/race_results.db
export RACE_API_KEYS=key1,key2,key3
export RACE_API_SECRET_KEY=your-secret-key-here
export RACE_API_DEBUG=false
```

### Configuration File

Alternatively, create a Python configuration file:

```python
# config.py
DATABASE_PATH = '/path/to/race_results.db'
API_KEYS = {'key1', 'key2', 'key3'}
SECRET_KEY = 'your-secret-key-here'
DEBUG = False
CORS_ENABLED = True
```

Load it in your application:
```python
from running_results.api import create_app, APIConfig

config = APIConfig.from_file('config.py')
app = create_app(config=config)
```

## Deployment

### Local Development

```bash
# Install dependencies
pip install -e .

# Set environment variables
export RACE_DB_PATH=race_results.db
export RACE_API_KEYS=dev-key-123

# Run the development server
python -m running_results.api.app

# Or use Flask CLI
export FLASK_APP=running_results.api.app
flask run
```

### Production (WSGI)

Use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn 'running_results.api.app:application'
```

### DreamHost Shared Hosting (FastCGI)

1. Upload files to your web directory
2. Install flup: `pip install flup`
3. Make api.fcgi executable: `chmod +x api.fcgi`
4. Create .htaccess file:

```apache
RewriteEngine On
RewriteBase /
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ api.fcgi/$1 [QSA,L]

SetEnv RACE_DB_PATH /home/username/race_results.db
SetEnv RACE_API_KEYS your-api-key-here
SetEnv RACE_API_SECRET_KEY your-secret-key
```

## Usage Examples

### Python

```python
import requests

API_BASE = 'http://localhost:5000'
API_KEY = 'your-api-key-here'

# List all races
response = requests.get(f'{API_BASE}/api/races')
races = response.json()

# Get race results
response = requests.get(
    f'{API_BASE}/api/races/Edinburgh Marathon/results',
    params={'year': 2024, 'limit': 100}
)
results = response.json()

# Add new results
new_results = {
    'race_name': 'Test Race',
    'race_year': 2024,
    'results': [
        {
            'name': 'John Smith',
            'position_overall': 1,
            'finish_time_seconds': 1800,
            'club': 'Running Club'
        }
    ]
}

response = requests.post(
    f'{API_BASE}/api/results',
    json=new_results,
    headers={'X-API-Key': API_KEY}
)
print(response.json())
```

### cURL

```bash
# List races
curl http://localhost:5000/api/races

# Get specific race results
curl "http://localhost:5000/api/races/Edinburgh%20Marathon/results?year=2024&limit=50"

# Add results (with API key)
curl -X POST http://localhost:5000/api/results \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "race_name": "Test Race",
    "race_year": 2024,
    "results": [
      {
        "name": "John Smith",
        "position_overall": 1,
        "finish_time_seconds": 1800
      }
    ]
  }'
```

### JavaScript (Browser/Node.js)

```javascript
const API_BASE = 'http://localhost:5000';
const API_KEY = 'your-api-key-here';

// List races
fetch(`${API_BASE}/api/races`)
  .then(response => response.json())
  .then(data => console.log(data));

// Get race results with filters
fetch(`${API_BASE}/api/races/Edinburgh Marathon/results?year=2024&limit=50`)
  .then(response => response.json())
  .then(data => console.log(data));

// Add new results
fetch(`${API_BASE}/api/results`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    race_name: 'Test Race',
    race_year: 2024,
    results: [
      {
        name: 'John Smith',
        position_overall: 1,
        finish_time_seconds: 1800,
        club: 'Running Club'
      }
    ]
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Rate Limiting

Currently, the API does not implement rate limiting. For production deployments, consider:

1. Using a reverse proxy (nginx, Apache) with rate limiting
2. Implementing rate limiting at the application level
3. Using a CDN with rate limiting features

## Security Considerations

1. **API Keys**: Keep your API keys secret and never commit them to version control
2. **HTTPS**: Always use HTTPS in production to encrypt API key transmission
3. **Database Backups**: Regularly backup your database
4. **Input Validation**: The API validates input data using Pydantic models
5. **SQL Injection**: The API uses parameterized queries to prevent SQL injection

## Support

For issues, questions, or contributions, please visit the GitHub repository:
https://github.com/transientlunatic/running
