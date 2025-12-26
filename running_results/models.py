"""
Pydantic models for normalizing and validating race results data.

This module provides a flexible schema system using Pydantic to ensure that
race results from different sources can be standardized into a consistent format,
enabling more general analysis code.

Example:
    >>> from running_results.models import normalize_race_results
    >>> # From a pandas DataFrame with arbitrary column names
    >>> normalized = normalize_race_results(df, source_type='marathon')
    >>> # Now all results have consistent field names
"""

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime
from enum import Enum


class RaceCategory(str, Enum):
    """Standard race categories."""
    ULTRA = "ultra"
    MARATHON = "marathon"
    HALF_MARATHON = "half_marathon"
    TEN_K = "10k"
    FIVE_K = "5k"
    PARKRUN = "parkrun"
    FELL_RACE = "fell_race"
    ROAD_RACE = "road_race"
    UNKNOWN = "unknown"


class Gender(str, Enum):
    """Standard gender categories."""
    MALE = "M"
    FEMALE = "F"
    NON_BINARY = "N"
    UNKNOWN = "U"


class NormalizedRaceResult(BaseModel):
    """
    Standard normalized race result schema.
    
    All race results, regardless of source, should conform to this schema.
    This enables analysis code to be written once and work across all data sources.
    """
    
    position_overall: Optional[int] = Field(
        None, description="Overall finishing position"
    )
    position_gender: Optional[int] = Field(
        None, description="Position within gender category"
    )
    position_category: Optional[int] = Field(
        None, description="Position within age/time category"
    )
    
    name: Optional[str] = Field(
        None, description="Participant name"
    )
    bib_number: Optional[str] = Field(
        None, description="Race bib/race number"
    )
    
    gender: Optional[Gender] = Field(
        None, description="Participant gender"
    )
    age_category: Optional[str] = Field(
        None, description="Age category (e.g., 'V35', '40M', 'U35F')"
    )
    
    club: Optional[str] = Field(
        None, description="Running club affiliation"
    )
    
    finish_time_seconds: Optional[float] = Field(
        None, description="Finish time in seconds"
    )
    finish_time_minutes: Optional[float] = Field(
        None, description="Finish time in minutes"
    )
    
    chip_time_seconds: Optional[float] = Field(
        None, description="Chip time in seconds (electronic timing)"
    )
    chip_time_minutes: Optional[float] = Field(
        None, description="Chip time in minutes"
    )
    
    gun_time_seconds: Optional[float] = Field(
        None, description="Gun time in seconds (from start signal)"
    )
    gun_time_minutes: Optional[float] = Field(
        None, description="Gun time in minutes"
    )
    
    # Metadata
    race_name: Optional[str] = Field(
        None, description="Name of the race event"
    )
    race_date: Optional[str] = Field(
        None, description="Date of the race (ISO format)"
    )
    race_year: Optional[int] = Field(
        None, description="Year of the race"
    )
    race_category: Optional[RaceCategory] = Field(
        None, description="Type of race (marathon, 10k, etc.)"
    )
    
    # Additional flexible fields for source-specific data
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional fields from source data"
    )
    
    class Config:
        use_enum_values = True
    
    @field_validator('bib_number', mode='before')
    @classmethod
    def convert_bib_number(cls, v):
        """Convert bib_number to string (accepts int or str)."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(int(v))
        return str(v) if v else None
    
    @field_validator('finish_time_minutes', mode='after')
    @classmethod
    def compute_finish_time_minutes(cls, v, info: ValidationInfo):
        """Compute finish_time_minutes from finish_time_seconds if not provided."""
        if v is None and 'finish_time_seconds' in info.data:
            seconds = info.data.get('finish_time_seconds')
            if seconds is not None:
                return seconds / 60
        return v
    
    @field_validator('chip_time_minutes', mode='after')
    @classmethod
    def compute_chip_time_minutes(cls, v, info: ValidationInfo):
        """Compute chip_time_minutes from chip_time_seconds if not provided."""
        if v is None and 'chip_time_seconds' in info.data:
            seconds = info.data.get('chip_time_seconds')
            if seconds is not None:
                return seconds / 60
        return v
    
    @field_validator('gun_time_minutes', mode='after')
    @classmethod
    def compute_gun_time_minutes(cls, v, info: ValidationInfo):
        """Compute gun_time_minutes from gun_time_seconds if not provided."""
        if v is None and 'gun_time_seconds' in info.data:
            seconds = info.data.get('gun_time_seconds')
            if seconds is not None:
                return seconds / 60
        return v


class ColumnMapping(BaseModel):
    """
    Maps source DataFrame columns to normalized schema fields.
    
    Specify which columns in your source data map to standard fields.
    Supports flexible matching including partial matches and transformations.
    
    Example:
        >>> mapping = ColumnMapping(
        ...     position_overall='Position (Overall)',
        ...     name='Name',
        ...     club='Club',
        ...     chip_time_seconds='Chip Time (seconds)',
        ...     age_category='Category'
        ... )
    """
    
    position_overall: Optional[str] = None
    position_gender: Optional[str] = None
    position_category: Optional[str] = None
    name: Optional[str] = None
    bib_number: Optional[str] = None
    gender: Optional[str] = None
    age_category: Optional[str] = None
    club: Optional[str] = None
    finish_time_seconds: Optional[str] = None
    finish_time_minutes: Optional[str] = None
    chip_time_seconds: Optional[str] = None
    chip_time_minutes: Optional[str] = None
    gun_time_seconds: Optional[str] = None
    gun_time_minutes: Optional[str] = None
    race_name: Optional[str] = None
    race_date: Optional[str] = None
    race_year: Optional[str] = None
    race_category: Optional[str] = None
    
    def get_mapping_dict(self) -> Dict[str, str]:
        """Return mapping as a dictionary, excluding None values."""
        return {k: v for k, v in self.dict().items() if v is not None}


class TimeParser(BaseModel):
    """
    Configuration for parsing time strings into seconds.
    
    Example:
        >>> # Parse "02:23:12" format (HH:MM:SS)
        >>> parser = TimeParser(format='HH:MM:SS')
        >>> seconds = parser.parse('02:23:12')  # Returns 8592
    """
    
    format: str = Field(
        default='HH:MM:SS',
        description="Time format: 'HH:MM:SS', 'MM:SS', or 'seconds'"
    )
    
    def parse(self, time_str: Any) -> Optional[float]:
        """
        Parse time string to seconds.
        
        Args:
            time_str: Time string or numeric value
            
        Returns:
            Time in seconds, or None if parsing fails
        """
        if time_str is None or (isinstance(time_str, float) and pd.isna(time_str)):
            return None
        
        # If already numeric, return as-is
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        time_str = str(time_str).strip()
        
        if self.format == 'seconds':
            try:
                return float(time_str)
            except (ValueError, TypeError):
                return None
        
        parts = time_str.split(':')
        
        try:
            if self.format == 'HH:MM:SS':
                if len(parts) == 3:
                    h, m, s = map(float, parts)
                    return h * 3600 + m * 60 + s
                elif len(parts) == 2:
                    # Assume MM:SS
                    m, s = map(float, parts)
                    return m * 60 + s
            elif self.format == 'MM:SS':
                if len(parts) == 2:
                    m, s = map(float, parts)
                    return m * 60 + s
                elif len(parts) == 3:
                    # Handle HH:MM:SS
                    h, m, s = map(float, parts)
                    return h * 3600 + m * 60 + s
        except (ValueError, TypeError, IndexError):
            pass
        
        return None


class RaceResultsNormalizer:
    """
    Normalize race results from various sources into a standard schema.
    
    This class handles the complexity of different data formats and column names,
    allowing you to write analysis code once that works across all data sources.
    
    Example:
        >>> # Load data from a CSV with arbitrary column names
        >>> df = pd.read_csv('edinburgh_marathon.csv')
        >>> 
        >>> # Define how your data maps to standard schema
        >>> mapping = ColumnMapping(
        ...     position_overall='Position (Overall)',
        ...     chip_time_seconds='Chip Time (seconds)',
        ...     name='Name Number',
        ...     club='Club',
        ...     age_category='Category'
        ... )
        >>> 
        >>> # Normalize all results at once
        >>> normalizer = RaceResultsNormalizer(mapping=mapping)
        >>> normalized_results = normalizer.normalize(df)
        >>> 
        >>> # All results now have consistent field names
        >>> for result in normalized_results:
        ...     print(f"{result.name}: {result.chip_time_minutes:.2f} minutes")
    """
    
    def __init__(
        self,
        mapping: Optional[ColumnMapping] = None,
        time_parser: Optional[TimeParser] = None,
        race_name: Optional[str] = None,
        race_year: Optional[int] = None,
        race_category: Optional[RaceCategory] = None,
        strict: bool = False,
        auto_detect: bool = True
    ):
        """
        Initialize the normalizer.
        
        Args:
            mapping: ColumnMapping specifying source to standard field mapping
            time_parser: TimeParser for parsing time strings
            race_name: Default race name to assign to all results
            race_year: Default race year
            race_category: Default race category type
            strict: If True, raise errors on validation issues
            auto_detect: If True, try to auto-detect column mappings
        """
        self.mapping = mapping or ColumnMapping()
        self.time_parser = time_parser or TimeParser()
        self.race_name = race_name
        self.race_year = race_year
        self.race_category = race_category
        self.strict = strict
        self.auto_detect = auto_detect
    
    def normalize(
        self,
        df: pd.DataFrame,
        return_dataframe: bool = False
    ) -> List[NormalizedRaceResult] | pd.DataFrame:
        """
        Normalize a DataFrame of race results.
        
        Args:
            df: DataFrame with race results
            return_dataframe: If True, return as DataFrame instead of list of models
            
        Returns:
            List of NormalizedRaceResult objects, or DataFrame if return_dataframe=True
        """
        # Auto-detect mappings if not provided
        if self.auto_detect and not self.mapping.get_mapping_dict():
            detected = self._auto_detect_columns(df)
            if detected:
                self.mapping = detected
        
        mapping_dict = self.mapping.get_mapping_dict()
        
        results = []
        for idx, row in df.iterrows():
            result = self._normalize_row(row, mapping_dict)
            results.append(result)
        
        if return_dataframe:
            return self._results_to_dataframe(results)
        
        return results
    
    def _auto_detect_columns(self, df: pd.DataFrame) -> Optional[ColumnMapping]:
        """
        Attempt to auto-detect column mappings from DataFrame columns.
        
        Uses fuzzy matching to find likely candidates for standard fields.
        """
        columns = df.columns.tolist()
        mapping = ColumnMapping()
        
        # Define common column name patterns for each standard field
        patterns = {
            'position_overall': ['position.*overall', 'pos', 'place', 'rank'],
            'name': ['name', 'runner', 'participant'],
            'bib_number': ['bib', 'number', 'race.*number'],
            'club': ['club', 'team', 'affiliation'],
            'chip_time_seconds': ['chip.*second', 'elapsed.*second'],
            'chip_time_minutes': ['chip.*minute', 'elapsed.*minute'],
            'gun_time_seconds': ['gun.*second', 'start.*second'],
            'gun_time_minutes': ['gun.*minute', 'start.*minute'],
            'finish_time_seconds': ['finish.*second', 'time.*second'],
            'finish_time_minutes': ['finish.*minute', 'time.*minute'],
            'age_category': ['category', 'age.*cat', 'age.*group'],
            'gender': ['gender', 'sex'],
            'race_year': ['year'],
        }
        
        import re
        
        for field, patterns_list in patterns.items():
            for col in columns:
                col_lower = col.lower()
                for pattern in patterns_list:
                    if re.search(pattern, col_lower):
                        setattr(mapping, field, col)
                        break
        
        return mapping if mapping.get_mapping_dict() else None
    
    def _normalize_row(
        self,
        row: pd.Series,
        mapping_dict: Dict[str, str]
    ) -> NormalizedRaceResult:
        """Normalize a single row to NormalizedRaceResult."""
        data = {}
        
        # Map columns to standard fields
        for field, column in mapping_dict.items():
            if column in row.index:
                value = row[column]
                data[field] = self._convert_value(field, value)
        
        # Parse time fields - handle both seconds and minutes fields
        time_fields = {
            'chip_time_seconds': None,
            'chip_time_minutes': 'chip_time_seconds',
            'gun_time_seconds': None,
            'gun_time_minutes': 'gun_time_seconds',
            'finish_time_seconds': None,
            'finish_time_minutes': 'finish_time_seconds'
        }
        
        for field, seconds_field in time_fields.items():
            if field in data and isinstance(data[field], str):
                # Parse string to seconds
                parsed_seconds = self.time_parser.parse(data[field])
                if field.endswith('_seconds'):
                    data[field] = parsed_seconds
                else:
                    # For minutes fields, store seconds in corresponding seconds field
                    if parsed_seconds is not None:
                        data[field] = parsed_seconds / 60
                        if seconds_field:
                            data[seconds_field] = parsed_seconds
        
        # Add metadata
        if self.race_name:
            data['race_name'] = self.race_name
        if self.race_year:
            data['race_year'] = self.race_year
        if self.race_category:
            data['race_category'] = self.race_category
        
        # Store unmapped columns as metadata
        mapped_cols = set(mapping_dict.values())
        for col, value in row.items():
            if col not in mapped_cols and not pd.isna(value):
                data.setdefault('metadata', {})[col] = value
        
        try:
            return NormalizedRaceResult(**data)
        except Exception as e:
            if self.strict:
                raise
            # Return partially valid result
            return NormalizedRaceResult(**{k: v for k, v in data.items()
                                          if k != 'metadata'})
    
    def _convert_value(self, field: str, value: Any) -> Any:
        """Convert a value to the appropriate type for the field."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        if field in ['position_overall', 'position_gender', 'position_category', 'race_year']:
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None
        
        elif field == 'gender':
            str_val = str(value).strip().upper()
            for g in Gender:
                if g.value == str_val or g.name == str_val:
                    return g.value
            return None
        
        elif field in ['chip_time_seconds', 'gun_time_seconds', 'finish_time_seconds']:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        return value
    
    def _results_to_dataframe(
        self,
        results: List[NormalizedRaceResult]
    ) -> pd.DataFrame:
        """Convert list of results to DataFrame."""
        records = []
        for result in results:
            record = result.model_dump(exclude={'metadata'})
            # Flatten metadata into top level
            record.update(result.metadata)
            records.append(record)
        
        return pd.DataFrame(records)


def normalize_race_results(
    df: pd.DataFrame,
    mapping: Optional[ColumnMapping] = None,
    race_name: Optional[str] = None,
    race_year: Optional[int] = None,
    race_category: Optional[str] = None,
    return_dataframe: bool = False,
    **normalizer_kwargs
) -> List[NormalizedRaceResult] | pd.DataFrame:
    """
    Convenience function to normalize race results in one call.
    
    Args:
        df: DataFrame with race results
        mapping: ColumnMapping for source columns
        race_name: Name of the race
        race_year: Year of the race
        race_category: Type of race
        return_dataframe: Return as DataFrame instead of list
        **normalizer_kwargs: Additional arguments for RaceResultsNormalizer
        
    Returns:
        Normalized race results
        
    Example:
        >>> df = pd.read_csv('race_results.csv')
        >>> mapping = ColumnMapping(
        ...     position_overall='Position',
        ...     chip_time_seconds='Chip (seconds)',
        ...     name='Participant Name'
        ... )
        >>> normalized = normalize_race_results(
        ...     df,
        ...     mapping=mapping,
        ...     race_name='Edinburgh Marathon 2024',
        ...     race_year=2024
        ... )
    """
    if race_category and isinstance(race_category, str):
        try:
            race_category = RaceCategory(race_category)
        except ValueError:
            race_category = None
    
    normalizer = RaceResultsNormalizer(
        mapping=mapping,
        race_name=race_name,
        race_year=race_year,
        race_category=race_category,
        **normalizer_kwargs
    )
    
    return normalizer.normalize(df, return_dataframe=return_dataframe)
