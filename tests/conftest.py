"""
Test fixtures and utilities shared across test modules.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_race_data():
    """Sample race results data for testing."""
    return pd.DataFrame(
        {
            "Position": [1, 2, 3, 4, 5],
            "Name": [
                "John Smith",
                "Jane Doe",
                "Bob Wilson",
                "Alice Brown",
                "Charlie Davis",
            ],
            "Club": [
                "Edinburgh AC",
                "Carnethy HRC",
                "U/A",
                "Highland Harriers",
                "Gala",
            ],
            "Time": ["31:45", "32:10", "33:20", "DNF", "35:45"],
            "Category": ["V", "FV", "SV", "M", "J"],
        }
    )


@pytest.fixture
def sample_malformed_data():
    """Race data with common formatting issues."""
    return pd.DataFrame(
        {
            "Pos": [1, 2, 3, 4],
            "Name": ["Runner One", "Runner Two", "Runner Three", "Runner Four"],
            "Club": ["Test AC", "Test HRC", None, "Unattached"],
            "Time": ["42::51", ":40:56", "1:23:45:", "DNS"],
            "Cat": ["V", "FV", "SSV", "J"],
        }
    )


@pytest.fixture
def temp_database():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing file imports."""
    return """Position,Name,Club,Time,Category
1,John Smith,Edinburgh AC,31:45,V
2,Jane Doe,Carnethy HRC,32:10,FV
3,Bob Wilson,Highland,33:20,SV
4,Alice Brown,Gala,DNF,M
5,Charlie Davis,Lothian,35:45,J
"""


@pytest.fixture
def sample_csv_file(tmp_path, sample_csv_content):
    """Create a sample CSV file for testing."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(sample_csv_content)
    return csv_file


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database file."""
    db_file = tmp_path / "test.db"
    return db_file


@pytest.fixture
def populated_db(temp_db, sample_csv_file):
    """Create a database with sample data."""
    from running_results import RaceResultsManager

    manager = RaceResultsManager(str(temp_db))
    manager.add_from_file(
        str(sample_csv_file),
        race_name="Test Race",
        race_year=2024,
        race_category="fell_race",
    )

    return temp_db
