"""
Data transformation utilities for race results.

This module provides classes for cleaning and standardizing race result data,
including time conversion, name parsing, and column standardization.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Callable, Any
from nameparser import HumanName


class TimeConverter:
    """
    Converts time strings to various formats.
    
    Handles common race time formats like "HH:MM:SS" or "MM:SS".
    """
    
    @staticmethod
    def to_seconds(time_str: str) -> int:
        """
        Convert time string to total seconds.
        
        Args:
            time_str: Time in format "HH:MM:SS" or "MM:SS"
            
        Returns:
            Total seconds as integer
            
        Example:
            >>> TimeConverter.to_seconds("1:23:45")
            5025
            >>> TimeConverter.to_seconds("23:45")
            1425
        """
        if pd.isna(time_str):
            return np.nan
            
        parts = str(time_str).split(":")
        
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(seconds) + 60 * int(minutes) + 3600 * int(hours)
        elif len(parts) == 2:
            minutes, seconds = parts
            return int(seconds) + 60 * int(minutes)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    @staticmethod
    def to_minutes(time_str: str) -> float:
        """
        Convert time string to total minutes.
        
        Args:
            time_str: Time in format "HH:MM:SS" or "MM:SS"
            
        Returns:
            Total minutes as float
        """
        seconds = TimeConverter.to_seconds(time_str)
        return seconds / 60.0 if not pd.isna(seconds) else np.nan
    
    @staticmethod
    def to_hours(time_str: str) -> float:
        """
        Convert time string to total hours.
        
        Args:
            time_str: Time in format "HH:MM:SS"
            
        Returns:
            Total hours as float
        """
        seconds = TimeConverter.to_seconds(time_str)
        return seconds / 3600.0 if not pd.isna(seconds) else np.nan
    
    @staticmethod
    def from_seconds(seconds: int) -> str:
        """
        Convert seconds back to time string.
        
        Args:
            seconds: Total seconds
            
        Returns:
            Time string in format "HH:MM:SS"
        """
        if pd.isna(seconds):
            return ""
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class NameParser:
    """
    Parses runner names into components (first name, last name, etc.).
    
    Uses the nameparser library to intelligently parse names.
    """
    
    @staticmethod
    def parse_name(name: str) -> Dict[str, str]:
        """
        Parse a full name into components.
        
        Args:
            name: Full name string
            
        Returns:
            Dictionary with 'first', 'last', 'middle', 'title', 'suffix'
        """
        if pd.isna(name) or not isinstance(name, str):
            return {
                'first': 'N/A',
                'last': 'N/A',
                'middle': '',
                'title': '',
                'suffix': ''
            }
            
        parsed = HumanName(name)
        return {
            'first': parsed.first or 'N/A',
            'last': parsed.last or 'N/A',
            'middle': parsed.middle,
            'title': parsed.title,
            'suffix': parsed.suffix
        }
    
    @staticmethod
    def add_name_columns(df: pd.DataFrame, name_column: str = 'Name') -> pd.DataFrame:
        """
        Add firstname and surname columns based on a name column.
        
        Args:
            df: DataFrame with name column
            name_column: Name of the column containing full names
            
        Returns:
            DataFrame with added 'Firstname' and 'Surname' columns
        """
        parsed_names = df[name_column].apply(NameParser.parse_name)
        df['Firstname'] = [name['first'] for name in parsed_names]
        df['Surname'] = [name['last'] for name in parsed_names]
        return df


class ColumnStandardizer:
    """
    Standardizes column names across different race result formats.
    
    Different races use different column names for the same data.
    This class provides mapping to standard names.
    """
    
    # Standard column mappings
    STANDARD_MAPPINGS = {
        # Position columns
        'Position': 'RunnerPosition',
        'Posn': 'RunnerPosition',
        'Pos': 'RunnerPosition',
        'Pos.': 'RunnerPosition',
        'Place': 'RunnerPosition',
        'Position (Overall)': 'OverallPosition',
        'Position (Gender)': 'GenderPosition',
        'Position (Category)': 'CategoryPosition',
        
        # Time columns
        'Time': 'FinishTime',
        'Tiime': 'FinishTime',  # Common typo
        'Chip Time': 'ChipTime',
        'Gun Time': 'GunTime',
        'Net Time': 'ChipTime',
        'Gross Time': 'GunTime',
        
        # Category columns
        'Category': 'RunnerCategory',
        'Cat': 'RunnerCategory',
        'Cat.': 'RunnerCategory',
        'Class': 'RunnerCategory',
        
        # Identifier columns
        'Race No.': 'RaceNumber',
        'Race No. ': 'RaceNumber',  # With trailing space
        'Bib': 'RaceNumber',
        'Number': 'RaceNumber',
        
        # Name columns
        'Surname': 'Surname',
        'Firstname': 'Firstname',
        'First Name': 'Firstname',
        'Last Name': 'Surname',
        'Name': 'Name',
        
        # Other columns
        'Club': 'Club',
        'Team': 'Club',
        'Gender': 'Gender',
        'Sex': 'Gender',
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize column standardizer.
        
        Args:
            custom_mappings: Additional custom column mappings to use
        """
        self.mappings = self.STANDARD_MAPPINGS.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)
    
    def standardize(self, df: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
        """
        Standardize column names in a DataFrame.
        
        Args:
            df: DataFrame to standardize
            strict: If True, raise error for unmapped columns
            
        Returns:
            DataFrame with standardized column names
        """
        # Create rename mapping for columns that exist
        rename_map = {}
        for col in df.columns:
            if col in self.mappings:
                rename_map[col] = self.mappings[col]
            elif strict:
                raise ValueError(f"No mapping found for column: {col}")
                
        return df.rename(columns=rename_map)
    
    def add_mapping(self, from_name: str, to_name: str):
        """Add a custom column mapping."""
        self.mappings[from_name] = to_name


class RaceDataTransformer:
    """
    Complete transformation pipeline for race data.
    
    Combines multiple transformation steps into a reusable pipeline.
    """
    
    def __init__(self):
        """Initialize the transformer with default settings."""
        self.standardizer = ColumnStandardizer()
        self.steps = []
        
    def add_step(self, func: Callable, **kwargs):
        """
        Add a transformation step to the pipeline.
        
        Args:
            func: Function that takes a DataFrame and returns a DataFrame
            **kwargs: Arguments to pass to the function
        """
        self.steps.append((func, kwargs))
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all transformation steps to a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Transformed DataFrame
        """
        result = df.copy()
        
        for func, kwargs in self.steps:
            result = func(result, **kwargs)
            
        return result
    
    @staticmethod
    def clean_header_row(df: pd.DataFrame, header_row_index: int = 0) -> pd.DataFrame:
        """
        Use a row as column headers and remove it from data.
        
        Common pattern where first row contains column names.
        
        Args:
            df: DataFrame
            header_row_index: Index of row to use as headers
            
        Returns:
            DataFrame with cleaned headers
        """
        df = df.rename(columns=df.iloc[header_row_index])
        df = df.drop(df.index[header_row_index])
        return df.reset_index(drop=True)
    
    @staticmethod
    def extract_category_from_position(
        df: pd.DataFrame, 
        position_col: str = 'Position (Category)',
        category_col: str = 'Category'
    ) -> pd.DataFrame:
        """
        Extract category from position string like "123 M40".
        
        Args:
            df: DataFrame
            position_col: Column with position and category
            category_col: Name for new category column
            
        Returns:
            DataFrame with extracted category
        """
        df = df.copy()
        df[category_col] = df[position_col].apply(
            lambda x: x.split()[1] if isinstance(x, str) and len(x.split()) > 1 else x
        )
        return df
    
    @staticmethod
    def add_time_conversions(
        df: pd.DataFrame,
        time_column: str = 'FinishTime',
        add_seconds: bool = True,
        add_minutes: bool = True
    ) -> pd.DataFrame:
        """
        Add time conversion columns.
        
        Args:
            df: DataFrame
            time_column: Name of time column to convert
            add_seconds: Add column with time in seconds
            add_minutes: Add column with time in minutes
            
        Returns:
            DataFrame with time conversion columns
        """
        df = df.copy()
        
        if add_seconds:
            df[f'{time_column} (seconds)'] = df[time_column].apply(TimeConverter.to_seconds)
            
        if add_minutes:
            df[f'{time_column} (minutes)'] = df[time_column].apply(TimeConverter.to_minutes)
            
        return df
    
    @staticmethod
    def select_columns(df: pd.DataFrame, columns: List[str], strict: bool = False) -> pd.DataFrame:
        """
        Select specific columns, optionally requiring all to exist.
        
        Args:
            df: DataFrame
            columns: List of column names to select
            strict: If True, raise error if any column missing
            
        Returns:
            DataFrame with selected columns
        """
        if strict:
            return df[columns]
        else:
            # Only select columns that exist
            existing_cols = [col for col in columns if col in df.columns]
            return df[existing_cols]
