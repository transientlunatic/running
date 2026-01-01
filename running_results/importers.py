"""
Import race results from various sources (URLs, files).

Provides functionality to fetch and parse race results from:
- Web pages (HTML tables)
- Text files (CSV, TSV, space-delimited)
- APIs (when available)
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import io
import re


class ResultsImporter:
    """
    Base class for importing race results from various sources.

    Example:
        >>> importer = ResultsImporter()
        >>> df = importer.from_url('https://example.com/results')
        >>> df = importer.from_file('results.txt')
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        Initialize importer.

        Args:
            encoding: Default text encoding for files
        """
        self.encoding = encoding
        self.session = requests.Session()
        # Ensure User-Agent contains project identifier for tests and etiquette
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; running-results/1.0; +https://github.com/transientlunatic/running)"
            }
        )

    def from_url(
        self, url: str, table_index: int = 0, selector: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Import results from a URL.

        Automatically detects and parses HTML tables.

        Args:
            url: URL to fetch results from
            table_index: Which table to extract (0 = first table)
            selector: CSS selector for the table (optional, overrides table_index)

        Returns:
            DataFrame with results

        Example:
            >>> df = importer.from_url('https://example.com/tinto-2024-results')
            >>> df = importer.from_url('https://example.com/results', selector='table.results')
        """
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        # Try to parse as HTML table
        soup = BeautifulSoup(response.content, "html.parser")

        if selector:
            # Use CSS selector
            tables = soup.select(selector)
            if not tables:
                raise ValueError(f"No tables found with selector '{selector}'")
            table = tables[0]
            df = self._parse_html_table(table)
        else:
            # Find all tables and use table_index
            tables = soup.find_all("table")
            if not tables:
                raise ValueError("No tables found in HTML")
            if table_index >= len(tables):
                raise ValueError(
                    f"Table index {table_index} out of range (found {len(tables)} tables)"
                )
            df = self._parse_html_table(tables[table_index])

        # Store source URL as metadata
        df.attrs["source_url"] = url

        return df

    def from_file(
        self, file_path: Union[str, Path], format: Optional[str] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Import results from a file.

        Automatically detects file format (CSV, TSV, Excel, HTML).

        Args:
            file_path: Path to the file
            format: Force specific format ('csv', 'tsv', 'excel', 'html', 'txt')
            **kwargs: Additional arguments passed to pandas read function

        Returns:
            DataFrame with results

        Example:
            >>> df = importer.from_file('tinto-2024.csv')
            >>> df = importer.from_file('results.txt', format='tsv')
            >>> df = importer.from_file('results.xlsx')
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect format from extension if not specified
        if format is None:
            ext = file_path.suffix.lower()
            format_map = {
                ".csv": "csv",
                ".tsv": "tsv",
                ".txt": "txt",
                ".xlsx": "excel",
                ".xls": "excel",
                ".html": "html",
                ".htm": "html",
            }
            format = format_map.get(ext, "txt")

        # Read based on format
        if format == "csv":
            df = pd.read_csv(file_path, encoding=self.encoding, **kwargs)
        elif format == "tsv":
            df = pd.read_csv(file_path, sep="\t", encoding=self.encoding, **kwargs)
        elif format == "excel":
            df = pd.read_excel(file_path, **kwargs)
        elif format == "html":
            tables = pd.read_html(file_path, **kwargs)
            df = tables[0] if tables else pd.DataFrame()
        elif format == "txt":
            # Try to auto-detect delimiter
            df = self._parse_text_file(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Store source file as metadata
        df.attrs["source_file"] = str(file_path)

        return df

    def from_text(self, text: str, delimiter: Optional[str] = None) -> pd.DataFrame:
        """
        Import results from a text string.

        Args:
            text: Text containing results
            delimiter: Column delimiter (auto-detected if None)

        Returns:
            DataFrame with results
        """
        if delimiter is None:
            delimiter = self._detect_delimiter(text)

        return pd.read_csv(io.StringIO(text), sep=delimiter)

    def _parse_html_table(self, table) -> pd.DataFrame:
        """Parse an HTML table element into a DataFrame."""
        # Extract headers
        headers = []
        header_row = table.find("thead")
        if header_row:
            headers = [
                th.get_text(strip=True) for th in header_row.find_all(["th", "td"])
            ]
        else:
            # Try first row
            first_row = table.find("tr")
            if first_row:
                headers = [
                    th.get_text(strip=True) for th in first_row.find_all(["th", "td"])
                ]

        # Extract data rows
        rows = []
        tbody = table.find("tbody")
        row_elements = tbody.find_all("tr") if tbody else table.find_all("tr")

        # Skip header row if we already got headers
        start_idx = 1 if not tbody and headers else 0

        for row in row_elements[start_idx:]:
            cells = row.find_all(["td", "th"])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:  # Skip empty rows
                rows.append(row_data)

        # Create DataFrame
        if headers and len(headers) == len(rows[0]) if rows else False:
            df = pd.DataFrame(rows, columns=headers)
        else:
            df = pd.DataFrame(rows)

        return df

    def _parse_text_file(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Parse a text file with auto-detected delimiter."""
        with open(file_path, "r", encoding=self.encoding) as f:
            content = f.read()

        delimiter = self._detect_delimiter(content)

        return pd.read_csv(file_path, sep=delimiter, encoding=self.encoding, **kwargs)

    def _detect_delimiter(self, text: str) -> str:
        """Auto-detect delimiter in text."""
        # Sample first few lines
        lines = text.split("\n")[:5]
        sample = "\n".join(lines)

        # Try common delimiters
        delimiters = [",", "\t", "|", ";", " "]

        for delim in delimiters:
            # Count occurrences in each line
            counts = [line.count(delim) for line in lines if line.strip()]
            if counts and all(c == counts[0] and c > 0 for c in counts):
                return delim

        # Default to whitespace
        return r"\s+"


from .models import ColumnMapping


class SmartImporter:
    """
    High-level importer that automatically handles normalization.

    Combines ResultsImporter with auto-detection and normalization.

    Example:
        >>> importer = SmartImporter()
        >>> results = importer.import_and_normalize(
        ...     'https://example.com/tinto-2024',
        ...     race_name='Tinto',
        ...     race_year=2024
        ... )
    """

    def __init__(self):
        self.importer = ResultsImporter()

    def import_and_normalize(
        self,
        source: Union[str, Path, io.StringIO],
        race_name: Optional[str] = None,
        race_year: Optional[int] = None,
        race_category: Optional[str] = None,
        mapping: Optional[Dict[str, str]] = None,
        column_mapping: Optional[ColumnMapping] = None,
        auto_detect: bool = True,
        **kwargs,
    ):
        """
        Import and normalize results in one step.

        Args:
            source: URL or file path
            race_name: Name of the race
            race_year: Year of the race
            race_category: Race category
            mapping: Manual column mapping (optional)
            auto_detect: Auto-detect column mappings
            **kwargs: Additional arguments for importer

        Returns:
            List of NormalizedRaceResult objects
        """
        from .models import RaceResultsNormalizer, ColumnMapping, RaceCategory

        # Import data
        source_url = None
        source_file = None
        # Determine input type
        if isinstance(source, io.StringIO):
            df = self.importer.from_text(source.getvalue())
        elif isinstance(source, (str, Path)):
            s = str(source)
            if s.startswith("http://") or s.startswith("https://"):
                df = self.importer.from_url(s, **kwargs)
                source_url = s
            else:
                df = self.importer.from_file(s, **kwargs)
                source_file = s
        else:
            raise TypeError(
                "Unsupported source type; expected URL, file path, or StringIO"
            )

        # Create normalizer
        col_mapping = None
        # Prefer explicit ColumnMapping, else mapping dict
        if column_mapping is not None:
            col_mapping = column_mapping
        elif mapping:
            col_mapping = ColumnMapping(**mapping)

        normalizer = RaceResultsNormalizer(
            mapping=col_mapping,
            auto_detect=auto_detect,
            race_name=race_name,
            race_year=race_year,
            race_category=race_category,
        )

        # Normalize
        results_df = normalizer.normalize(df, return_dataframe=True)

        # Attach source metadata
        # Attach source metadata to DataFrame attrs
        if source_url:
            results_df.attrs["source_url"] = source_url
        if source_file:
            results_df.attrs["source_file"] = source_file

        return results_df
