Command Line Interface
======================

The running_results package includes a comprehensive command-line interface (CLI) for managing race results databases and generating reports.

Installation
------------

After installing the package, the CLI is available as the ``running-results`` command::

    pip install running_results
    running-results --help

Quick Start
-----------

Create and populate a new database::

    # Add results from a CSV file
    running-results add tinto_2024.csv --race-name "Tinto Hill Race" --race-year 2024

    # Import from a URL
    running-results import-url "https://example.com/results" --race-name "Example Race" --race-year 2024

    # List all races in database
    running-results list-races

    # Generate a race report
    running-results report --race-name "Tinto Hill Race" --year 2024 --output report.html

Commands
--------

Global Options
~~~~~~~~~~~~~~

All commands support the ``--db`` option to specify the database path::

    running-results --db /path/to/results.db list-races

If not specified, defaults to ``race_results.db`` in the current directory.

add
~~~

Add results from a file to the database.

**Usage**::

    running-results add <FILE> [OPTIONS]

**Arguments**:

* ``FILE``: Path to results file (CSV, TSV, Excel, or HTML)

**Options**:

* ``--race-name TEXT``: Name of the race (required)
* ``--race-year INTEGER``: Year of the race (required)
* ``--race-date TEXT``: Date of the race (YYYY-MM-DD)
* ``--distance FLOAT``: Race distance in kilometers
* ``--category TEXT``: Race category (road, trail, fell, ultra, parkrun)
* ``--location TEXT``: Race location
* ``--mapping TEXT``: Custom column mapping (JSON format)

**Examples**::

    # Basic usage
    running-results add results.csv --race-name "Edinburgh Marathon" --race-year 2024

    # With additional metadata
    running-results add results.csv \
        --race-name "West Highland Way Race" \
        --race-year 2024 \
        --race-date "2024-06-15" \
        --distance 154.0 \
        --category ultra \
        --location "Milngavie to Fort William"

    # With custom column mapping
    running-results add results.csv \
        --race-name "Local Race" \
        --race-year 2024 \
        --mapping '{"Runner": "name", "Club/Team": "club"}'

import-url
~~~~~~~~~~

Import results from a web page.

**Usage**::

    running-results import-url <URL> [OPTIONS]

**Arguments**:

* ``URL``: URL of the results page

**Options**:

* ``--race-name TEXT``: Name of the race (required)
* ``--race-year INTEGER``: Year of the race (required)
* ``--race-date TEXT``: Date of the race (YYYY-MM-DD)
* ``--distance FLOAT``: Race distance in kilometers
* ``--category TEXT``: Race category
* ``--location TEXT``: Race location
* ``--selector TEXT``: CSS selector for the results table
* ``--mapping TEXT``: Custom column mapping (JSON format)

**Examples**::

    # Import from URL with automatic table detection
    running-results import-url "https://example.com/results" \
        --race-name "Example Race" \
        --race-year 2024

    # Use CSS selector to target specific table
    running-results import-url "https://example.com/results" \
        --race-name "Example Race" \
        --race-year 2024 \
        --selector "table.results"

list-races
~~~~~~~~~~

List all races in the database.

**Usage**::

    running-results list-races

**Example Output**::

    Race Database Summary
    =====================
    
    Edinburgh Marathon (2 editions, 25,432 results)
      - 2023: 12,716 results
      - 2024: 12,716 results
    
    West Highland Way Race (5 editions, 1,245 results)
      - 2020: 245 results
      - 2021: 248 results
      - 2022: 251 results
      - 2023: 250 results
      - 2024: 251 results

query
~~~~~

Query and filter race results.

**Usage**::

    running-results query [OPTIONS]

**Options**:

* ``--race-name TEXT``: Filter by race name
* ``--year INTEGER``: Filter by year
* ``--runner TEXT``: Filter by runner name (partial match)
* ``--club TEXT``: Filter by club name (partial match)
* ``--output PATH``: Export results to CSV file

**Examples**::

    # Get all results for a specific race
    running-results query --race-name "Edinburgh Marathon"

    # Get results for a specific year
    running-results query --race-name "Edinburgh Marathon" --year 2024

    # Find a specific runner
    running-results query --runner "John Smith"

    # Find all runners from a club
    running-results query --club "Edinburgh AC"

    # Export to CSV
    running-results query --race-name "Edinburgh Marathon" --year 2024 --output results.csv

report
~~~~~~

Generate a comprehensive race report.

**Usage**::

    running-results report [OPTIONS]

**Options**:

* ``--race-name TEXT``: Name of the race (required)
* ``--year INTEGER``: Specific year (omit for all years)
* ``--output PATH``: Output file path (default: race_report.html)
* ``--format TEXT``: Output format - html or pdf (default: html)

The report includes:

* Race summary statistics (starters, finishers, DNF count, finish rate)
* Top 10 finishers
* Finish time distribution (histogram)
* Club participation analysis (top clubs by number of runners)
* Age category analysis (statistics by category)
* Gender distribution

**Examples**::

    # Generate HTML report for a single year
    running-results report --race-name "Edinburgh Marathon" --year 2024

    # Generate PDF report
    running-results report \
        --race-name "Edinburgh Marathon" \
        --year 2024 \
        --format pdf \
        --output marathon_2024.pdf

    # Report combining all years
    running-results report --race-name "Tinto Hill Race" --output tinto_all_years.html

compare
~~~~~~~

Generate a multi-year comparison report.

**Usage**::

    running-results compare --race-name <RACE> [OPTIONS]

**Options**:

* ``--race-name TEXT``: Name of the race (required)
* ``--output PATH``: Output file path (default: comparison_report.html)

The comparison report includes:

* Year-by-year statistics table (starters, finishers, DNF, times)
* Participation trend chart
* Winning time evolution chart
* Multi-year comparisons

**Example**::

    running-results compare --race-name "Tinto Hill Race" --output tinto_comparison.html

runner
~~~~~~

Generate a runner history report.

**Usage**::

    running-results runner <NAME> [OPTIONS]

**Arguments**:

* ``NAME``: Runner name to search for

**Options**:

* ``--output PATH``: Output file path (default: runner_report.html)

The runner report includes:

* Overall statistics (total races, finishes, DNF count)
* Best performance metrics (best time, average time, best position)
* Complete race history table
* Performance trend chart

**Example**::

    running-results runner "John Smith" --output john_smith_history.html

Report Features
---------------

All reports are generated using the otter-report framework, which produces clean, professional HTML and PDF documents.

HTML Reports
~~~~~~~~~~~~

HTML reports are self-contained files that can be:

* Opened directly in any web browser
* Shared via email or file sharing
* Published to websites
* Embedded in documentation

The HTML includes:

* Responsive design that works on mobile devices
* Interactive charts (zoom, pan, hover tooltips)
* Clean typography and professional styling
* Tables with sorting and filtering

PDF Reports
~~~~~~~~~~~

PDF reports can be generated by adding ``--format pdf``::

    running-results report --race-name "Example Race" --year 2024 --format pdf

PDF reports are ideal for:

* Printing and distribution
* Formal documentation
* Archival purposes

Customizing Reports
~~~~~~~~~~~~~~~~~~~

The reporting module (``running_results.reporting``) can be used programmatically for advanced customization::

    from running_results.reporting import generate_race_report
    import pandas as pd
    
    # Load your results
    results = pd.read_csv('results.csv')
    
    # Generate custom report
    generate_race_report(
        results=results,
        race_name="Custom Race",
        race_year=2024,
        output_path='custom_report.html',
        output_format='html'
    )

See the :doc:`examples` section for more customization examples.

Database Management
-------------------

The CLI uses SQLite for data storage, providing:

* Fast queries across years of data
* Automatic deduplication of results
* Consistent data normalization
* Easy backup (single .db file)

Database Location
~~~~~~~~~~~~~~~~~

By default, the database is created as ``race_results.db`` in your current directory. You can specify a custom location::

    running-results --db /path/to/my_results.db list-races

Or set an environment variable::

    export RACE_RESULTS_DB=/path/to/my_results.db
    running-results list-races

Backup and Export
~~~~~~~~~~~~~~~~~

The database is a single SQLite file that can be easily backed up::

    # Backup
    cp race_results.db race_results_backup.db

    # Export all results to CSV
    running-results query --output all_results.csv

Error Handling
--------------

The CLI provides helpful error messages:

* Missing required options
* Invalid file formats
* Database connection issues
* Missing otter-report installation

If you encounter errors, check:

1. All required dependencies are installed
2. Input files are in supported formats
3. Database file is not locked by another process
4. You have write permissions for output files

See Also
--------

* :doc:`database_guide` - Detailed database usage
* :doc:`api/manager` - RaceResultsManager API reference
* :doc:`api/importers` - Import utilities
* :doc:`examples` - Code examples and recipes
