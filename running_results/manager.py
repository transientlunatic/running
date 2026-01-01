"""
High-level race results manager.

Provides a simple API for managing race results:
- Import from URLs or files
- Store in database
- Query and analyze results
"""

from typing import Optional, List, Union
from pathlib import Path
import pandas as pd

from .database import RaceResultsDatabase
from .importers import SmartImporter
from .models import RaceCategory


class RaceResultsManager:
    """
    Unified interface for managing race results.

    This is the main entry point for working with race results.
    It handles importing, storing, and querying results.

    Example:
        >>> # Initialize manager with database
        >>> manager = RaceResultsManager('my_races.db')
        >>>
        >>> # Add results from URL
        >>> manager.add_from_url(
        ...     'https://example.com/tinto-2024-results',
        ...     race_name='Tinto',
        ...     race_year=2024,
        ...     race_category='fell_race'
        ... )
        >>>
        >>> # Add results from file
        >>> manager.add_from_file(
        ...     'edinburgh-marathon-2024.csv',
        ...     race_name='Edinburgh Marathon',
        ...     race_year=2024
        ... )
        >>>
        >>> # Query results
        >>> tinto_results = manager.get_race('Tinto')
        >>> my_results = manager.get_runner_history('John Smith')
        >>>
        >>> # List all races
        >>> races = manager.list_races()
    """

    def __init__(self, db_path: str = "race_results.db"):
        """
        Initialize race results manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = str(db_path)
        self.db = RaceResultsDatabase(self.db_path)
        self.importer = SmartImporter()

    def add_from_url(
        self,
        url: str,
        race_name: Optional[str] = None,
        year: Optional[int] = None,
        race_category: Optional[str] = None,
        mapping: Optional[dict] = None,
        column_mapping: Optional[dict] = None,
        table_index: int = 0,
        selector: Optional[str] = None,
        auto_detect: bool = True,
    ) -> int:
        """
        Import and store results from a URL.

        Args:
            url: URL of the results page
            race_name: Name of the race
            race_year: Year of the race
            race_category: Category (e.g., 'marathon', 'fell_race')
            mapping: Manual column mapping dict (optional)
            table_index: Which table to extract from page (default: 0)
            selector: CSS selector for table (optional)
            auto_detect: Auto-detect column mappings

        Returns:
            Number of results added

        Example:
            >>> count = manager.add_from_url(
            ...     'https://example.com/tinto-2024',
            ...     race_name='Tinto',
            ...     race_year=2024,
            ...     race_category='fell_race'
            ... )
            >>> print(f"Added {count} results")
        """
        # Prepare mapping: support reversed dict {source_col: normalized_field}
        mapping_to_use = None
        if column_mapping:
            mapping_to_use = {v: k for k, v in column_mapping.items()}
        elif mapping:
            # Assume mapping is already normalized_field -> source_col
            mapping_to_use = mapping

        # Import and normalize to DataFrame
        results_df = self.importer.import_and_normalize(
            url,
            race_name=race_name,
            race_year=year,
            race_category=race_category,
            mapping=mapping_to_use,
            auto_detect=auto_detect,
            table_index=table_index,
            selector=selector,
        )

        # Store in database
        # Convert DataFrame rows to NormalizedRaceResult
        from .models import NormalizedRaceResult

        allowed = set(NormalizedRaceResult.model_fields.keys())
        records = results_df.to_dict(orient="records")
        results = [
            NormalizedRaceResult(**{k: v for k, v in rec.items() if k in allowed})
            for rec in records
        ]

        # Source URL from DataFrame attrs
        source_url = results_df.attrs.get("source_url")

        count = self.db.add_results(
            results,
            race_name=race_name or "",
            race_year=year,
            race_category=race_category,
            source_url=source_url,
        )

        return count

    def add_from_file(
        self,
        file_path: Union[str, Path],
        race_name: Optional[str] = None,
        year: Optional[int] = None,
        race_category: Optional[str] = None,
        mapping: Optional[dict] = None,
        column_mapping: Optional[dict] = None,
        format: Optional[str] = None,
        auto_detect: bool = True,
        **kwargs,
    ) -> int:
        """
        Import and store results from a file.

        Args:
            file_path: Path to the file
            race_name: Name of the race
            race_year: Year of the race
            race_category: Category (e.g., 'marathon', 'fell_race')
            mapping: Manual column mapping dict (optional)
            format: File format ('csv', 'tsv', 'excel', etc.)
            auto_detect: Auto-detect column mappings
            **kwargs: Additional arguments for file reader

        Returns:
            Number of results added

        Example:
            >>> count = manager.add_from_file(
            ...     'tinto-2024.csv',
            ...     race_name='Tinto',
            ...     race_year=2024,
            ...     race_category='fell_race'
            ... )
        """
        # Import and normalize
        # Reconcile year from kwargs if provided to avoid duplicate arguments
        kw_year = kwargs.pop("race_year", None)
        if year is None:
            year = kw_year

        # Prepare mapping: support reversed dict {source_col: normalized_field}
        mapping_to_use = None
        if column_mapping:
            mapping_to_use = {v: k for k, v in column_mapping.items()}
        elif mapping:
            mapping_to_use = mapping

        results_df = self.importer.import_and_normalize(
            str(file_path),
            race_name=race_name,
            race_year=year,
            race_category=race_category,
            mapping=mapping_to_use,
            auto_detect=auto_detect,
            format=format,
            **kwargs,
        )

        # Store in database
        # Convert DataFrame rows to NormalizedRaceResult
        from .models import NormalizedRaceResult

        allowed = set(NormalizedRaceResult.model_fields.keys())
        records = results_df.to_dict(orient="records")
        results = [
            NormalizedRaceResult(**{k: v for k, v in rec.items() if k in allowed})
            for rec in records
        ]

        source_file = results_df.attrs.get("source_file")

        count = self.db.add_results(
            results,
            race_name=race_name or "",
            race_year=year,
            race_category=race_category,
            source_file=source_file,
        )

        return count

    def add_results(
        self,
        results: List,
        race_name: str,
        year: Optional[int] = None,
        race_category: Optional[str] = None,
        race_date: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Add already-normalized results directly.

        Args:
            results: List of NormalizedRaceResult objects
            race_name: Name of the race
            race_year: Year of the race
            race_category: Race category

        Returns:
            Number of results added
        """
        # metadata and race_date accepted for API compatibility but not stored here
        return self.db.add_results(
            results, race_name=race_name, race_year=year, race_category=race_category
        )

    def get_race(self, race_name: str, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get results for a specific race.

        Args:
            race_name: Name of the race
            year: Optional year filter

        Returns:
            DataFrame with race results

        Example:
            >>> # All Tinto results across all years
            >>> tinto_all = manager.get_race('Tinto')
            >>>
            >>> # Just 2024 results
            >>> tinto_2024 = manager.get_race('Tinto', year=2024)
        """
        return self.db.get_race_results(race_name=race_name, year=year)

    def get_runner_history(
        self, runner_name: str, race_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get a runner's results history.

        Args:
            runner_name: Runner name (partial match OK)
            race_name: Optional filter by specific race

        Returns:
            DataFrame with runner's results over time

        Example:
            >>> # All results for a runner
            >>> results = manager.get_runner_history('John Smith')
            >>>
            >>> # Just their Tinto results
            >>> tinto_results = manager.get_runner_history('John Smith', 'Tinto')
        """
        return self.db.get_runner_history(runner_name, race_name)

    def search_results(
        self,
        race_name: Optional[str] = None,
        year: Optional[int] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        runner_name: Optional[str] = None,
        club: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Search results with flexible filters.

        Args:
            race_name: Filter by race name
            year: Filter by year
            runner_name: Filter by runner name (partial match)
            club: Filter by club (partial match)

        Returns:
            DataFrame with matching results

        Example:
            >>> # All Carnethy runners in 2024
            >>> results = manager.search_results(year=2024, club='Carnethy')
        """
        df = self.db.get_race_results(
            race_name=race_name, year=year, runner_name=runner_name, club=club
        )
        if min_year is not None:
            df = df[df["race_year"] >= min_year]
        if max_year is not None:
            df = df[df["race_year"] <= max_year]
        return df

    def list_races(self) -> pd.DataFrame:
        """
        Get summary of all races in database.

        Returns:
            DataFrame with race statistics

        Example:
            >>> races = manager.list_races()
            >>> print(races[['race_name', 'num_years', 'total_results']])
        """
        return self.db.get_races()

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
