"""
Data fetching module for race results.

This module provides classes and functions to fetch race results from various sources
including web pages with HTML tables and CSV files.
"""

import pandas as pd
import requests
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from tqdm.auto import tqdm


class RaceDataSource(ABC):
    """Abstract base class for race data sources."""
    
    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Fetch and return race data as a pandas DataFrame."""
        pass


class RaceDataFetcher(RaceDataSource):
    """
    Fetches race results from web pages containing HTML tables.
    
    This is a flexible fetcher that can handle various URL patterns and
    pagination schemes commonly found in race result websites.
    
    Example:
        >>> fetcher = RaceDataFetcher(
        ...     url_template="https://example.com/results?page={page}",
        ...     url_params={'page': range(1, 10)}
        ... )
        >>> data = fetcher.fetch()
    """
    
    def __init__(
        self, 
        url_template: str,
        url_params: Optional[Dict[str, Any]] = None,
        table_index: int = -1,
        headers: Optional[Dict[str, str]] = None,
        progress_bar: bool = True
    ):
        """
        Initialize the race data fetcher.
        
        Args:
            url_template: URL string with format placeholders (e.g., "{page}", "{year}")
            url_params: Dictionary mapping parameter names to values or iterables
            table_index: Which HTML table to extract (-1 for last table, 0 for first)
            headers: HTTP headers for requests (defaults to Mozilla user agent)
            progress_bar: Whether to show progress bar for multiple requests
        """
        self.url_template = url_template
        self.url_params = url_params or {}
        self.table_index = table_index
        self.headers = headers or {'User-agent': 'Mozilla/5.0'}
        self.progress_bar = progress_bar
        
    def fetch(self) -> pd.DataFrame:
        """
        Fetch race data from the configured URL(s).
        
        Returns:
            DataFrame containing the combined race results
        """
        # If no params, fetch single URL
        if not self.url_params:
            return self._fetch_single(self.url_template)
        
        # Handle multiple parameter combinations
        return self._fetch_multiple()
    
    def _fetch_single(self, url: str) -> pd.DataFrame:
        """Fetch data from a single URL."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            tables = pd.read_html(response.text)
            
            if not tables:
                raise ValueError(f"No tables found at {url}")
                
            return tables[self.table_index]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from {url}: {str(e)}")
    
    def _fetch_multiple(self) -> pd.DataFrame:
        """Fetch data from multiple URLs based on parameter combinations."""
        all_data = []
        
        # Generate all parameter combinations
        param_combinations = self._generate_param_combinations()
        
        # Iterate with optional progress bar
        iterator = tqdm(param_combinations) if self.progress_bar else param_combinations
        
        for params in iterator:
            try:
                url = self.url_template.format(**params)
                df = self._fetch_single(url)
                
                # Check for empty results (pagination end detection)
                if len(df) == 0:
                    break
                    
                # Add metadata columns for the parameters used
                for key, value in params.items():
                    df[f'_fetch_{key}'] = value
                    
                all_data.append(df)
            except Exception as e:
                if self.progress_bar:
                    tqdm.write(f"Error fetching {params}: {str(e)}")
                continue
        
        if not all_data:
            raise RuntimeError("No data was successfully fetched")
            
        return pd.concat(all_data, ignore_index=True)
    
    def _generate_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate all combinations of URL parameters."""
        # Simple case: all params are single values or ranges
        import itertools
        
        param_names = list(self.url_params.keys())
        param_values = []
        
        for name in param_names:
            value = self.url_params[name]
            # Convert to list if it's iterable (but not string)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                param_values.append(list(value))
            else:
                param_values.append([value])
        
        # Generate all combinations
        combinations = []
        for values in itertools.product(*param_values):
            combinations.append(dict(zip(param_names, values)))
            
        return combinations


class PaginatedRaceDataFetcher(RaceDataFetcher):
    """
    Specialized fetcher for paginated race results.
    
    Automatically detects when pagination ends by looking for empty tables.
    
    Example:
        >>> fetcher = PaginatedRaceDataFetcher(
        ...     url_template="https://edinburghmarathon.com/results?page={page}&gender={gender}",
        ...     page_start=1,
        ...     max_pages=1000,
        ...     other_params={'gender': ['M', 'F']}
        ... )
        >>> data = fetcher.fetch()
    """
    
    def __init__(
        self,
        url_template: str,
        page_start: int = 1,
        max_pages: int = 1000,
        page_param_name: str = 'page',
        other_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize paginated fetcher.
        
        Args:
            url_template: URL with {page} placeholder
            page_start: Starting page number
            max_pages: Maximum pages to fetch
            page_param_name: Name of the page parameter in URL
            other_params: Other URL parameters (e.g., gender, event)
            **kwargs: Passed to parent RaceDataFetcher
        """
        params = {page_param_name: range(page_start, page_start + max_pages)}
        if other_params:
            params.update(other_params)
            
        super().__init__(url_template, params, **kwargs)


class CSVRaceData(RaceDataSource):
    """
    Loads race data from CSV file(s).
    
    Example:
        >>> loader = CSVRaceData("race_results.csv")
        >>> data = loader.fetch()
    """
    
    def __init__(
        self, 
        file_path: str,
        **read_csv_kwargs
    ):
        """
        Initialize CSV data loader.
        
        Args:
            file_path: Path to CSV file
            **read_csv_kwargs: Additional arguments passed to pd.read_csv
        """
        self.file_path = file_path
        self.read_csv_kwargs = read_csv_kwargs
        
    def fetch(self) -> pd.DataFrame:
        """Load data from CSV file."""
        return pd.read_csv(self.file_path, **self.read_csv_kwargs)


class MultiYearRaceData:
    """
    Fetches race data across multiple years.
    
    Useful for historical analysis of the same race event.
    
    Example:
        >>> fetcher = MultiYearRaceData(
        ...     url_template="https://example.com/race_{year}.htm",
        ...     years=range(2000, 2024)
        ... )
        >>> data = fetcher.fetch()
    """
    
    def __init__(
        self,
        url_template: str,
        years: range,
        table_index: int = -1,
        on_error: str = 'warn'  # 'warn', 'ignore', or 'raise'
    ):
        """
        Initialize multi-year fetcher.
        
        Args:
            url_template: URL with {year} placeholder
            years: Range of years to fetch
            table_index: Which table to extract from each page
            on_error: How to handle errors ('warn', 'ignore', 'raise')
        """
        self.url_template = url_template
        self.years = years
        self.table_index = table_index
        self.on_error = on_error
        
    def fetch(self) -> pd.DataFrame:
        """Fetch data for all years."""
        all_data = []
        failed_years = []
        
        for year in tqdm(self.years, desc="Fetching years"):
            try:
                fetcher = RaceDataFetcher(
                    url_template=self.url_template,
                    url_params={'year': year},
                    table_index=self.table_index,
                    progress_bar=False
                )
                df = fetcher.fetch()
                df['year'] = year
                all_data.append(df)
            except Exception as e:
                failed_years.append(year)
                if self.on_error == 'raise':
                    raise
                elif self.on_error == 'warn':
                    tqdm.write(f"Failed to fetch year {year}: {str(e)}")
                    
        if not all_data:
            raise RuntimeError("No data was successfully fetched for any year")
            
        if failed_years and self.on_error == 'warn':
            print(f"\nFailed years: {failed_years}")
            
        return pd.concat(all_data, ignore_index=True)
