# Race Results Database & Import System

## Overview

The running_results package now includes a complete system for managing race results across multiple years:

- **Database Storage**: SQLite-based persistent storage
- **Web Scraping**: Import results from URLs (HTML tables)
- **File Import**: Support for CSV, TSV, Excel, HTML files
- **Auto-normalization**: Automatic column detection and data cleaning
- **Multi-year Tracking**: Track the same race across multiple years
- **Easy Querying**: Simple API for searching and analyzing results

## Quick Start

```python
from running_results import RaceResultsManager

# Initialize manager with database
manager = RaceResultsManager('my_races.db')

# Add results from a URL
manager.add_from_url(
    'https://example.com/tinto-2024-results',
    race_name='Tinto',
    race_year=2024,
    race_category='fell_race'
)

# Add results from a file
manager.add_from_file(
    'tinto-2023.csv',
    race_name='Tinto',
    race_year=2023,
    race_category='fell_race'
)

# Query results
tinto_all = manager.get_race('Tinto')  # All years
tinto_2024 = manager.get_race('Tinto', year=2024)  # Specific year
my_results = manager.get_runner_history('John Smith')
carnethy_results = manager.search_results(club='Carnethy')

# List all races
races = manager.list_races()
```

## Features

### 1. Database Storage (`RaceResultsDatabase`)

Stores race results in SQLite with:
- Race registry (unique races)
- Race editions (specific years/dates)
- Individual results
- Source tracking (URL or file)

```python
from running_results import RaceResultsDatabase

db = RaceResultsDatabase('races.db')

# Add results
db.add_results(
    normalized_results,
    race_name='Tinto',
    race_year=2024
)

# Query
all_results = db.get_race_results('Tinto')
runner_history = db.get_runner_history('John Smith')
races = db.get_races()
```

### 2. Import from URLs (`ResultsImporter`)

Automatically fetch and parse HTML tables from web pages:

```python
from running_results import ResultsImporter

importer = ResultsImporter()

# Import from URL
df = importer.from_url('https://example.com/results')

# Specify which table (if multiple tables on page)
df = importer.from_url('https://example.com/results', table_index=1)

# Use CSS selector
df = importer.from_url('https://example.com/results', selector='table.results')
```

### 3. Import from Files

Support for multiple file formats:

```python
# CSV
df = importer.from_file('results.csv')

# TSV
df = importer.from_file('results.tsv')

# Excel
df = importer.from_file('results.xlsx')

# HTML
df = importer.from_file('results.html')

# Auto-detect delimiter in text files
df = importer.from_file('results.txt')
```

### 4. Smart Import & Normalization (`SmartImporter`)

Combines importing with automatic normalization:

```python
from running_results import SmartImporter

importer = SmartImporter()

# Import, normalize, and return NormalizedRaceResult objects
results, source_url, source_file = importer.import_and_normalize(
    'https://example.com/tinto-2024',
    race_name='Tinto',
    race_year=2024,
    race_category='fell_race',
    auto_detect=True  # Auto-detect column mappings
)
```

### 5. Unified Manager (`RaceResultsManager`)

Single interface for everything:

```python
from running_results import RaceResultsManager

manager = RaceResultsManager('my_races.db')

# Add results from any source
manager.add_from_url(url, race_name, race_year)
manager.add_from_file(file_path, race_name, race_year)
manager.add_results(normalized_results, race_name, race_year)

# Query in various ways
manager.get_race(race_name, year=None)
manager.get_runner_history(runner_name, race_name=None)
manager.search_results(race_name, year, runner_name, club)
manager.list_races()
```

## Data Normalization

All imports automatically apply normalization:

1. **Time Correction**: Fixes malformed times (`:40:56` → `40:56`, `42::51` → `42:51`)
2. **Club Standardization**: Removes suffixes, handles variations (`Carnethy HRC` → `Carnethy`)
3. **Age Category Parsing**: Converts codes to standard format:
   - `V`, `VM` → `M40` (Male Veteran/Over 40)
   - `SV` → `M50` (Senior Veteran/Over 50)
   - `SSV` → `M60` (Super Senior Veteran/Over 60)
   - `FV` → `F40` (Female Veteran)
   - `J`, `U20` → `U20` (Junior)
4. **Gender Extraction**: Infers gender from age category if not explicit
5. **Status Handling**: Recognizes DNF, DNS, DSQ automatically

## Database Schema

### Races Table
- `race_id`: Primary key
- `race_name`: Name of the race
- `race_category`: Category (marathon, fell_race, etc.)

### Race Editions Table
- `edition_id`: Primary key
- `race_id`: Foreign key to races
- `race_year`: Year of the race
- `race_date`: Date of the race
- `source_url`: URL where results came from
- `source_file`: File where results came from

### Results Table
- `result_id`: Primary key
- `edition_id`: Foreign key to race_editions
- All standard fields (position, name, times, etc.)

## Example Workflow

```python
from running_results import RaceResultsManager

# 1. Initialize
manager = RaceResultsManager('fell_races.db')

# 2. Import historical data from files
for year in range(1985, 2024):
    manager.add_from_file(
        f'tinto/{year}.csv',
        race_name='Tinto',
        race_year=year,
        race_category='fell_race'
    )

# 3. Add new year from web
manager.add_from_url(
    'https://tinto-hill-race.com/results-2024',
    race_name='Tinto',
    race_year=2024,
    race_category='fell_race'
)

# 4. Analyze results
# Get all Tinto results
all_years = manager.get_race('Tinto')

# Track a runner across years
history = manager.get_runner_history('John Smith', 'Tinto')
print(history[['race_year', 'position_overall', 'finish_time_minutes']])

# Find fastest times by club
carnethy = manager.search_results(club='Carnethy')
fastest = carnethy.nsmallest(10, 'finish_time_seconds')

# Year-on-year comparison
for year in range(2020, 2025):
    results = manager.get_race('Tinto', year=year)
    avg_time = results['finish_time_minutes'].mean()
    print(f"{year}: {len(results)} finishers, avg {avg_time:.1f} min")
```

## API Reference

### RaceResultsManager

Main interface for managing race results.

**Constructor:**
- `RaceResultsManager(db_path='race_results.db')`

**Methods:**
- `add_from_url(url, race_name, race_year, ...)` - Import from web
- `add_from_file(file_path, race_name, race_year, ...)` - Import from file
- `add_results(results, race_name, race_year)` - Add normalized results
- `get_race(race_name, year=None)` - Get race results
- `get_runner_history(runner_name, race_name=None)` - Track a runner
- `search_results(race_name, year, runner_name, club)` - Flexible search
- `list_races()` - Show all races in database

### RaceResultsDatabase

Low-level database operations.

**Methods:**
- `add_race(race_name, race_category)`
- `add_race_edition(race_id, race_year, ...)`
- `add_results(results, race_name, ...)`
- `get_race_results(race_name, year, runner_name, club)`
- `get_races()`
- `get_runner_history(runner_name, race_name)`

### ResultsImporter

Import data from various sources.

**Methods:**
- `from_url(url, table_index=0, selector=None)`
- `from_file(file_path, format=None, **kwargs)`
- `from_text(text, delimiter=None)`

### SmartImporter

Combined import and normalization.

**Methods:**
- `import_and_normalize(source, race_name, race_year, ...)`

## Installation

Requires additional dependencies for web scraping:

```bash
pip install beautifulsoup4 requests lxml
```

All other dependencies are already included in the package.
