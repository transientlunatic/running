"""
Tests for running_results.manager module.
Integration tests for the unified manager interface.
"""
import pytest
import pandas as pd
from running_results.manager import RaceResultsManager
from running_results.models import NormalizedRaceResult, RaceCategory


class TestRaceResultsManager:
    """Test the RaceResultsManager class."""

    def test_create_manager(self, temp_database):
        """Test creating a manager instance."""
        manager = RaceResultsManager(temp_database)
        assert manager.db_path == temp_database
        manager.close()

    def test_context_manager(self, temp_database):
        """Test using manager as context manager."""
        with RaceResultsManager(temp_database) as manager:
            assert manager.db is not None

    def test_add_results_directly(self, temp_database):
        """Test adding pre-normalized results."""
        with RaceResultsManager(temp_database) as manager:
            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name='John Smith',
                    club='Edinburgh',
                    finish_time_seconds=1800
                ),
                NormalizedRaceResult(
                    position_overall=2,
                    name='Jane Doe',
                    club='Carnethy',
                    finish_time_seconds=1900
                )
            ]

            count = manager.add_results(
                results,
                race_name='Test Race',
                year=2024,
                race_category='fell_race'
            )

            assert count == 2

    def test_add_from_file(self, temp_database, temp_csv_file, sample_csv_content):
        """Test adding results from a file."""
        # Write CSV content
        with open(temp_csv_file, 'w') as f:
            f.write(sample_csv_content)

        with RaceResultsManager(temp_database) as manager:
            count = manager.add_from_file(
                file_path=temp_csv_file,
                race_name='Test Race',
                year=2024,
                race_category='fell_race',
                column_mapping={
                    'Position': 'position_overall',
                    'Name': 'name',
                    'Club': 'club',
                    'Time': 'finish_time'
                }
            )

            assert count == 5

    def test_get_race(self, temp_database):
        """Test retrieving race results."""
        with RaceResultsManager(temp_database) as manager:
            # Add results
            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name='John Smith',
                    finish_time_seconds=1800
                )
            ]
            manager.add_results(results, 'Test Race', 2024, 'fell_race')

            # Retrieve results
            df = manager.get_race('Test Race', year=2024)
            assert len(df) == 1
            assert df.loc[0, 'name'] == 'John Smith'

    def test_get_race_all_years(self, temp_database):
        """Test retrieving race results across multiple years."""
        with RaceResultsManager(temp_database) as manager:
            # Add results for multiple years
            for year in [2022, 2023, 2024]:
                results = [
                    NormalizedRaceResult(
                        position_overall=1,
                        name=f'Runner {year}',
                        finish_time_seconds=1800
                    )
                ]
                manager.add_results(results, 'Test Race', year, 'fell_race')

            # Get all years
            df = manager.get_race('Test Race')
            assert len(df) == 3

    def test_get_runner_history(self, temp_database):
        """Test retrieving runner history."""
        with RaceResultsManager(temp_database) as manager:
            # Add same runner across multiple years
            for year in [2022, 2023, 2024]:
                results = [
                    NormalizedRaceResult(
                        position_overall=1,
                        name='John Smith',
                        finish_time_seconds=1800 + (year - 2022) * 100
                    )
                ]
                manager.add_results(results, 'Test Race', year, 'fell_race')

            # Get history
            history = manager.get_runner_history('John Smith', 'Test Race')
            assert len(history) == 3
            assert all(history['name'] == 'John Smith')

    def test_search_results_by_club(self, temp_database):
        """Test searching results by club."""
        with RaceResultsManager(temp_database) as manager:
            # Add results with different clubs
            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name='Runner 1',
                    club='Carnethy',
                    finish_time_seconds=1800
                ),
                NormalizedRaceResult(
                    position_overall=2,
                    name='Runner 2',
                    club='Edinburgh',
                    finish_time_seconds=1900
                ),
                NormalizedRaceResult(
                    position_overall=3,
                    name='Runner 3',
                    club='Carnethy',
                    finish_time_seconds=2000
                )
            ]
            manager.add_results(results, 'Test Race', 2024, 'fell_race')

            # Search by club
            carnethy_results = manager.search_results(club='Carnethy')
            assert len(carnethy_results) == 2
            assert all(carnethy_results['club'] == 'Carnethy')

    def test_search_results_with_year_range(self, temp_database):
        """Test searching results with year filters."""
        with RaceResultsManager(temp_database) as manager:
            # Add results across multiple years
            for year in range(2020, 2025):
                results = [
                    NormalizedRaceResult(
                        position_overall=1,
                        name=f'Runner {year}',
                        club='Test Club',
                        finish_time_seconds=1800
                    )
                ]
                manager.add_results(results, 'Test Race', year, 'fell_race')

            # Search with year range
            results_2022_2024 = manager.search_results(
                race_name='Test Race',
                min_year=2022,
                max_year=2024
            )
            years = results_2022_2024['race_year'].unique()
            assert len(years) == 3
            assert all(2022 <= year <= 2024 for year in years)

    def test_list_races(self, temp_database):
        """Test listing all races."""
        with RaceResultsManager(temp_database) as manager:
            # Add multiple races
            for race_num in range(1, 4):
                results = [
                    NormalizedRaceResult(
                        position_overall=1,
                        name='Runner',
                        finish_time_seconds=1800
                    )
                ]
                manager.add_results(
                    results,
                    f'Race {race_num}',
                    2024,
                    'fell_race'
                )

            # List races
            races = manager.list_races()
            assert len(races) == 3
            assert 'race_name' in races.columns
            assert 'total_results' in races.columns

    def test_add_multiple_years_same_race(self, temp_database):
        """Test adding multiple years of the same race."""
        with RaceResultsManager(temp_database) as manager:
            for year in range(2020, 2025):
                results = [
                    NormalizedRaceResult(
                        position_overall=i,
                        name=f'Runner {i}',
                        finish_time_seconds=1800 + i * 100
                    )
                    for i in range(1, 11)  # 10 runners per year
                ]
                manager.add_results(results, 'Annual Race', year, 'fell_race')

            # Verify all years are present
            all_results = manager.get_race('Annual Race')
            assert len(all_results) == 50  # 10 runners × 5 years

            # Verify individual years
            results_2024 = manager.get_race('Annual Race', year=2024)
            assert len(results_2024) == 10

    def test_empty_database_queries(self, temp_database):
        """Test querying empty database."""
        with RaceResultsManager(temp_database) as manager:
            races = manager.list_races()
            assert len(races) == 0

            results = manager.get_race('Nonexistent Race')
            assert len(results) == 0

            history = manager.get_runner_history('Nonexistent Runner')
            assert len(history) == 0

    def test_add_results_with_metadata(self, temp_database):
        """Test adding results with race metadata."""
        with RaceResultsManager(temp_database) as manager:
            results = [
                NormalizedRaceResult(
                    position_overall=1,
                    name='John Smith',
                    finish_time_seconds=1800
                )
            ]

            count = manager.add_results(
                results,
                race_name='Test Race',
                year=2024,
                race_category='marathon',
                race_date='2024-06-15',
                metadata={'distance': '42.2km', 'elevation': '100m'}
            )

            assert count == 1

    def test_integration_workflow(self, temp_database, temp_csv_file, sample_csv_content):
        """Test a complete workflow: import, query, analyze."""
        # Write CSV file
        with open(temp_csv_file, 'w') as f:
            f.write(sample_csv_content)

        with RaceResultsManager(temp_database) as manager:
            # 1. Import data
            count = manager.add_from_file(
                temp_csv_file,
                race_name='Annual Race',
                year=2024,
                race_category='fell_race'
            )
            assert count == 5

            # 2. Query results
            results = manager.get_race('Annual Race', year=2024)
            assert len(results) == 5

            # 3. Analyze
            finishers = results[results['race_status'] == 'FINISHED']
            assert len(finishers) == 4  # One DNF in sample data

            # 4. Get club stats
            club_counts = results['club'].value_counts()
            assert len(club_counts) > 0

            # 5. List all races
            races = manager.list_races()
            assert len(races) == 1
            assert races.loc[0, 'race_name'] == 'Annual Race'
