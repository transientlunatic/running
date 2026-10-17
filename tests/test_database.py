"""
Tests for running_results.database module.
"""

import pytest
import pandas as pd
from running_results.database import RaceResultsDatabase
from running_results.models import NormalizedRaceResult, RaceCategory, RaceStatus


class TestRaceResultsDatabase:
    """Test the RaceResultsDatabase class."""

    def test_create_database(self, temp_database):
        """Test creating a new database."""
        db = RaceResultsDatabase(temp_database)
        assert db.db_path == temp_database
        db.close()

    def test_context_manager(self, temp_database):
        """Test using database as context manager."""
        with RaceResultsDatabase(temp_database) as db:
            assert db.conn is not None

    def test_add_race(self, temp_database):
        """Test adding a race."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race(
                race_name="Test Race", race_category=RaceCategory.FELL_RACE
            )
            assert race_id is not None
            assert isinstance(race_id, int)

    def test_add_duplicate_race(self, temp_database):
        """Test that adding duplicate race returns existing ID."""
        with RaceResultsDatabase(temp_database) as db:
            race_id_1 = db.add_race("Test Race", RaceCategory.MARATHON)
            race_id_2 = db.add_race("Test Race", RaceCategory.MARATHON)
            assert race_id_1 == race_id_2

    def test_add_race_edition(self, temp_database):
        """Test adding a race edition."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(
                race_id=race_id, year=2024, race_date="2024-06-15"
            )
            assert edition_id is not None
            assert isinstance(edition_id, int)

    def test_add_race_edition_with_metadata(self, temp_database):
        """Test adding race edition with metadata."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.MARATHON)
            metadata = {"distance": "42.2km", "weather": "sunny"}
            edition_id = db.add_race_edition(
                race_id=race_id, year=2024, metadata=metadata
            )
            assert edition_id is not None

    def test_add_results(self, temp_database):
        """Test adding race results."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(race_id, 2024)

            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name="John Smith",
                    club="Edinburgh",
                    finish_time_seconds=1800,
                ),
                NormalizedRaceResult(
                    position_overall=2,
                    name="Jane Doe",
                    club="Carnethy",
                    finish_time_seconds=1900,
                ),
            ]

            count = db.add_results(results, edition_id)
            assert count == 2

    def test_get_races(self, temp_database):
        """Test retrieving all races."""
        with RaceResultsDatabase(temp_database) as db:
            db.add_race("Race 1", RaceCategory.FELL_RACE)
            db.add_race("Race 2", RaceCategory.MARATHON)

            races = db.get_races()
            assert len(races) == 2
            assert "race_name" in races.columns

    def test_get_race_results(self, temp_database):
        """Test retrieving race results."""
        with RaceResultsDatabase(temp_database) as db:
            # Add race and results
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(race_id, 2024)

            results = [
                NormalizedRaceResult(
                    position_overall=1, name="John Smith", finish_time_seconds=1800
                ),
                NormalizedRaceResult(
                    position_overall=2, name="Jane Doe", finish_time_seconds=1900
                ),
            ]
            db.add_results(results, edition_id)

            # Retrieve results
            df = db.get_race_results("Test Race", year=2024)
            assert len(df) == 2
            assert df.loc[0, "name"] == "John Smith"
            assert df.loc[1, "name"] == "Jane Doe"

    def test_get_race_results_all_years(self, temp_database):
        """Test retrieving race results across all years."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)

            # Add results for multiple years
            for year in [2022, 2023, 2024]:
                edition_id = db.add_race_edition(race_id, year)
                results = [
                    NormalizedRaceResult(
                        position_overall=1,
                        name=f"Runner {year}",
                        finish_time_seconds=1800,
                    )
                ]
                db.add_results(results, edition_id)

            # Retrieve all years
            df = db.get_race_results("Test Race")
            assert len(df) == 3

    def test_get_runner_history(self, temp_database):
        """Test retrieving runner history."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)

            # Add multiple years for same runner
            for year in [2022, 2023, 2024]:
                edition_id = db.add_race_edition(race_id, year)
                results = [
                    NormalizedRaceResult(
                        position_overall=year - 2021,  # 1, 2, 3
                        name="John Smith",
                        finish_time_seconds=1800 + (year - 2022) * 100,
                    )
                ]
                db.add_results(results, edition_id)

            # Get history
            history = db.get_runner_history("John Smith", "Test Race")
            assert len(history) == 3
            assert all(history["name"] == "John Smith")

    def test_get_runner_history_all_races(self, temp_database):
        """Test getting runner history across all races."""
        with RaceResultsDatabase(temp_database) as db:
            # Add multiple races
            for race_num in [1, 2]:
                race_id = db.add_race(f"Race {race_num}", RaceCategory.FELL_RACE)
                edition_id = db.add_race_edition(race_id, 2024)
                results = [
                    NormalizedRaceResult(
                        position_overall=race_num,
                        name="John Smith",
                        finish_time_seconds=1800,
                    )
                ]
                db.add_results(results, edition_id)

            # Get history across all races
            history = db.get_runner_history("John Smith")
            assert len(history) == 2

    def test_results_with_dnf(self, temp_database):
        """Test storing and retrieving DNF results."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(race_id, 2024)

            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name="Finisher",
                    finish_time_seconds=1800,
                    race_status=RaceStatus.FINISHED,
                ),
                NormalizedRaceResult(name="DNF Runner", race_status=RaceStatus.DNF),
            ]
            db.add_results(results, edition_id)

            df = db.get_race_results("Test Race", year=2024)
            assert len(df) == 2
            assert df.loc[1, "race_status"] == "DNF"

    def test_results_with_club_filter(self, temp_database):
        """Test that results can be filtered by club."""
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(race_id, 2024)

            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name="Runner 1",
                    club="Carnethy",
                    finish_time_seconds=1800,
                ),
                NormalizedRaceResult(
                    position_overall=2,
                    name="Runner 2",
                    club="Edinburgh",
                    finish_time_seconds=1900,
                ),
            ]
            db.add_results(results, edition_id)

            # Get all results and filter by club
            df = db.get_race_results("Test Race", year=2024)
            carnethy_runners = df[df["club"] == "Carnethy"]
            assert len(carnethy_runners) == 1
            assert carnethy_runners.iloc[0]["name"] == "Runner 1"

    def test_empty_database(self, temp_database):
        """Test querying empty database."""
        with RaceResultsDatabase(temp_database) as db:
            races = db.get_races()
            assert len(races) == 0

            results = db.get_race_results("Nonexistent Race")
            assert len(results) == 0

    def test_database_persistence(self, temp_database):
        """Test that data persists across connections."""
        # Write data
        with RaceResultsDatabase(temp_database) as db:
            race_id = db.add_race("Test Race", RaceCategory.FELL_RACE)
            edition_id = db.add_race_edition(race_id, 2024)
            results = [
                NormalizedRaceResult(
                    position_overall=1, name="John Smith", finish_time_seconds=1800
                )
            ]
            db.add_results(results, edition_id)

        # Read data in new connection
        with RaceResultsDatabase(temp_database) as db:
            df = db.get_race_results("Test Race", year=2024)
            assert len(df) == 1
            assert df.loc[0, "name"] == "John Smith"
