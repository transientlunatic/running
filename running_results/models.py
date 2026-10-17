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


class RaceStatus(str, Enum):
    """Race completion status."""

    FINISHED = "finished"
    DNF = "dnf"  # Did Not Finish
    DNS = "dns"  # Did Not Start
    DSQ = "dsq"  # Disqualified
    UNKNOWN = "unknown"


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

    name: Optional[str] = Field(None, description="Participant name")
    bib_number: Optional[str] = Field(None, description="Race bib/race number")

    gender: Optional[Gender] = Field(None, description="Participant gender")
    age_category: Optional[str] = Field(
        None, description="Age category (e.g., 'V35', '40M', 'U35F')"
    )

    club: Optional[str] = Field(None, description="Running club affiliation")

    # Race completion status
    race_status: Optional[RaceStatus] = Field(
        None, description="Race completion status (finished, dnf, dns, dsq)"
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
    chip_time_minutes: Optional[float] = Field(None, description="Chip time in minutes")

    gun_time_seconds: Optional[float] = Field(
        None, description="Gun time in seconds (from start signal)"
    )
    gun_time_minutes: Optional[float] = Field(None, description="Gun time in minutes")

    # Metadata
    race_name: Optional[str] = Field(None, description="Name of the race event")
    race_date: Optional[str] = Field(None, description="Date of the race (ISO format)")
    race_year: Optional[int] = Field(None, description="Year of the race")
    race_category: Optional[RaceCategory] = Field(
        None, description="Type of race (marathon, 10k, etc.)"
    )

    # Additional flexible fields for source-specific data
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional fields from source data"
    )

    class Config:
        use_enum_values = True
    
    @field_validator('position_overall', 'position_gender', 'position_category', mode='before')
    @classmethod
    def validate_position(cls, v):
        """Clean up position fields - convert NaN to None."""
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return v
    
    @field_validator('race_status', mode='before')
    @classmethod
    def parse_race_status(cls, v):
        """Parse race status from various formats (DNF, DNS, etc.)."""
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None

        # If an Enum instance is provided, return its value (lowercase)
        if isinstance(v, RaceStatus):
            return v.value

        v_str = str(v).strip().upper()

        # Handle common DNF/DNS/DSQ variations
        status_map = {
            "DNF": RaceStatus.DNF,
            "DID NOT FINISH": RaceStatus.DNF,
            "DID-NOT-FINISH": RaceStatus.DNF,
            "DNS": RaceStatus.DNS,
            "DID NOT START": RaceStatus.DNS,
            "DID-NOT-START": RaceStatus.DNS,
            "DSQ": RaceStatus.DSQ,
            "DISQUALIFIED": RaceStatus.DSQ,
            "FINISHED": RaceStatus.FINISHED,
            "FINISH": RaceStatus.FINISHED,
        }

        if v_str in status_map:
            # Return standardized enum value (lowercase)
            return status_map[v_str].value

        return None

    @field_validator(
        "finish_time_seconds", "chip_time_seconds", "gun_time_seconds", mode="before"
    )
    @classmethod
    def validate_time_seconds(cls, v):
        """Validate that time fields contain actual numeric times, not status strings."""
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None

        # Check for DNF/DNS/DSQ status strings in time fields
        if isinstance(v, str):
            v_stripped = v.strip()
            v_upper = v_stripped.upper()

            # Check for status terms
            dnf_terms = [
                "DNF",
                "DNS",
                "DSQ",
                "DID NOT FINISH",
                "DID NOT START",
                "DISQUALIFIED",
                "N/A",
                "NA",
                "--",
                "---",
            ]
            if any(term in v_upper for term in dnf_terms):
                return None

            # Reject strings that are too long to be times (likely text notes)
            if len(v_stripped) > 20:
                return None

            # Check if it looks like a valid time format
            # Valid formats: "MM:SS", "HH:MM:SS", or pure numbers
            import re

            if not re.match(r"^[\d:\.]+$", v_stripped):
                # Contains non-time characters, reject it
                return None

            # Return the fixed string for further parsing
            return v_stripped

        # If it's a number, validate it's reasonable (> 0, < 24 hours for most races)
        try:
            numeric_val = float(v)
            if numeric_val <= 0:
                return None
            # Sanity check: most races finish under 24 hours (86400 seconds)
            # Ultra races might be longer, but we'll accept anything reasonable
            if numeric_val > 864000:  # 10 days - clearly invalid
                return None
            return numeric_val
        except (ValueError, TypeError):
            # Not a valid number, leave as string to be handled by parser
            return v

    @field_validator(
        "finish_time_minutes", "chip_time_minutes", "gun_time_minutes", mode="before"
    )
    @classmethod
    def validate_time_minutes(cls, v):
        """Validate that time fields contain actual numeric times, not status strings."""
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None

        # Check for DNF/DNS/DSQ status strings in time fields
        if isinstance(v, str):
            v_stripped = v.strip()
            v_upper = v_stripped.upper()

            # Check for status terms
            dnf_terms = [
                "DNF",
                "DNS",
                "DSQ",
                "DID NOT FINISH",
                "DID NOT START",
                "DISQUALIFIED",
                "N/A",
                "NA",
                "--",
                "---",
            ]
            if any(term in v_upper for term in dnf_terms):
                return None

            # Reject strings that are too long to be times (likely text notes)
            if len(v_stripped) > 20:
                return None

            # Check if it looks like a valid time format
            # Valid formats: "MM:SS", "HH:MM:SS", or pure numbers
            import re

            if not re.match(r"^[\d:\.]+$", v_stripped):
                # Contains non-time characters, reject it
                return None

            # Return the fixed string for further parsing
            return v_stripped

        # If it's a number, validate it's reasonable
        try:
            numeric_val = float(v)
            if numeric_val <= 0:
                return None
            # Sanity check: most races finish under 1440 minutes (24 hours)
            if numeric_val > 14400:  # 10 days - clearly invalid
                return None
            return numeric_val
        except (ValueError, TypeError):
            # Not a valid number, leave as string to be handled by parser
            return v

    @field_validator("bib_number", mode="before")
    @classmethod
    def convert_bib_number(cls, v):
        """Convert bib_number to string (accepts int or str)."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(int(v))
        return str(v) if v else None

    @field_validator("finish_time_minutes", mode="after")
    @classmethod
    def compute_finish_time_minutes(cls, v, info: ValidationInfo):
        """Compute finish_time_minutes from finish_time_seconds if not provided."""
        if v is None and "finish_time_seconds" in info.data:
            seconds = info.data.get("finish_time_seconds")
            if seconds is not None:
                return seconds / 60
        return v

    @field_validator("chip_time_minutes", mode="after")
    @classmethod
    def compute_chip_time_minutes(cls, v, info: ValidationInfo):
        """Compute chip_time_minutes from chip_time_seconds if not provided."""
        if v is None and "chip_time_seconds" in info.data:
            seconds = info.data.get("chip_time_seconds")
            if seconds is not None:
                return seconds / 60
        return v

    @field_validator("gun_time_minutes", mode="after")
    @classmethod
    def compute_gun_time_minutes(cls, v, info: ValidationInfo):
        """Compute gun_time_minutes from gun_time_seconds if not provided."""
        if v is None and "gun_time_seconds" in info.data:
            seconds = info.data.get("gun_time_seconds")
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
    # Generic finish time which will be treated as seconds after parsing
    finish_time: Optional[str] = None
    finish_time_minutes: Optional[str] = None
    chip_time_seconds: Optional[str] = None
    chip_time_minutes: Optional[str] = None
    gun_time_seconds: Optional[str] = None
    gun_time_minutes: Optional[str] = None
    race_name: Optional[str] = None
    race_date: Optional[str] = None
    race_year: Optional[str] = None
    race_category: Optional[str] = None
    race_status: Optional[str] = None

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
        default="HH:MM:SS", description="Time format: 'HH:MM:SS', 'MM:SS', or 'seconds'"
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

        # Fix malformed times before parsing
        time_str = fix_malformed_time(time_str)
        if not time_str:
            return None

        if self.format == "seconds":
            try:
                return float(time_str)
            except (ValueError, TypeError):
                return None

        parts = time_str.split(":")

        try:
            if self.format == "HH:MM:SS":
                if len(parts) == 3:
                    h, m, s = map(float, parts)
                    return h * 3600 + m * 60 + s
                elif len(parts) == 2:
                    # Assume MM:SS
                    m, s = map(float, parts)
                    return m * 60 + s
            elif self.format == "MM:SS":
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


def fix_malformed_time(time_str: str) -> Optional[str]:
    """
    Attempt to fix common time string errors.

    Examples:
        "42::51" -> "42:51"
        ":40:56" -> "40:56"
        "1:2:3:" -> "1:2:3"
    """
    if not isinstance(time_str, str):
        return time_str
    
    # Treat dot-separated segments as times, e.g. "1.00.24" -> "1:00:24"
    fixed = time_str.strip()
    if ':' not in fixed and '.' in fixed:
        dot_parts = fixed.split('.')
        if 2 <= len(dot_parts) <= 3 and all(part.isdigit() for part in dot_parts):
            fixed = ':'.join(dot_parts)

    # Remove consecutive colons
    while '::' in fixed:
        fixed = fixed.replace('::', ':')
    
    # Remove leading/trailing colons
    fixed = fixed.strip(":")

    return fixed if fixed else None


def normalize_club_name(club: Optional[str]) -> Optional[str]:
    """
    Normalize club names to handle variations.

    Examples:
        "Carnethy HRC" -> "Carnethy"
        "Edinburgh AC " -> "Edinburgh AC"
        "U/A" -> None (unattached)
    """
    if not club or not isinstance(club, str):
        return None

    club = club.strip()
    
    # Handle unattached runners first
    if club.upper() in ['U/A', 'N/A', 'UNATTACHED', 'UA', 'NA', '']:
        return None
    
    # Canonical synonyms and abbreviations
    # Map common variants to a single canonical club name
    synonyms = {
        # Westerlands
        'westies': 'Westerlands CCC',
        'westerlands': 'Westerlands CCC',
        'westerlands ccc': 'Westerlands CCC',
        'westerlands cross country club': 'Westerlands CCC',
        
        # Hunters Bog Trotters
        'hbt': 'Hunters Bog Trotters',
        'hunters bog trotters': 'Hunters Bog Trotters',
        
        # Ochil Hill Runners
        'ochil hr': 'Ochil Hill Runners',
        'ochils hr': 'Ochil Hill Runners',
        'ochil hill runners': 'Ochil Hill Runners',
        'ochils hill runners': 'Ochil Hill Runners',
        
        # Lothian variants
        'lothian rc': 'Lothian RC',
        'lothian': 'Lothian RC',
        
        # Lochtayside variants
        'lochtayside': 'Lochtayside',
        'lochtay': 'Lochtayside',
        
        # North Ayrshire variants
        'north ayrshire': 'North Ayrshire AC',
        'north ayrshire ac': 'North Ayrshire AC',
        'north ayrshire athletics club': 'North Ayrshire AC',
        
        # Carnegie Harriers, etc. (identity mappings for consistency)
        'carnegie harriers': 'Carnegie Harriers',
        'shettleston harriers': 'Shettleston Harriers',
        'deeside runners': 'Deeside Runners',
        'bellahouston road runners': 'Bellahouston Road Runners',
        'dumfries rc': 'Dumfries RC',
        'dumfries running club': 'Dumfries RC',
        'galloway harriers': 'Galloway Harriers',
        'hunters bog trotters': 'Hunters Bog Trotters',
        'moorfoot runners': 'Moorfoot Runners',
        'penicuik harriers': 'Penicuik Harriers',
        'portobello rrc': 'Portobello RRC',
        'tinto hill runners': 'Tinto Hill Runners',
        'teviotdale harriers': 'Teviotdale Harriers',
        'fife ac': 'Fife AC',
    }
    
    key = club.lower().replace('.', '').strip()
    if key in synonyms:
        return synonyms[key]
    
    # Common suffixes to remove for normalization
    suffixes = [
        " HRC",
        " H.R.C.",
        " Hill Running Club",
        " AC",
        " A.C.",
        " Athletic Club",
        " Harriers",
        " RC",
        " R.C.",
        " Running Club",
        " AAC",
        " A.A.C.",
    ]

    normalized = club
    # Remove suffixes (case-insensitive)
    for suffix in suffixes:
        suffix_upper = suffix.upper()
        if normalized.upper().endswith(suffix_upper):
            normalized = normalized[:-len(suffix)].strip()
            break
    
    # Title-case for consistency: capitalize each word
    normalized = ' '.join(word.capitalize() for word in normalized.split())
    
    return normalized if normalized else None


def parse_age_category(
    category: Optional[str], gender: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Parse age category codes into standardized format.

    Common conventions:
        V/VM/M40 = Male Over 40
        SV/M50 = Male Over 50
        SSV/M60 = Male Over 60
        FV/F40 = Female Over 40
        FSV/F50 = Female Over 50
        U20/J = Junior/Under 20

    Returns:
        Dict with 'age_category' (standardized) and 'gender' (if detected)
    """
    result = {"age_category": None, "gender": gender}

    if not category or not isinstance(category, str):
        return result

    cat = category.strip().upper()

    # Map common patterns
    category_map = {
        # Male veterans
        "V": "M40",
        "VM": "M40",
        "MV": "M40",
        "M40": "M40",
        "V40": "M40",
        "SV": "M50",
        "MSV": "M50",
        "M50": "M50",
        "V50": "M50",
        "SSV": "M60",
        "M60": "M60",
        "V60": "M60",
        "M70": "M70",
        "V70": "M70",
        # Female veterans
        "FV": "F40",
        "F40": "F40",
        "VF": "F40",
        "LV": "F40",  # Lady Veteran
        "FSV": "F50",
        "F50": "F50",
        "FSSV": "F60",
        "F60": "F60",
        # Juniors
        "J": "U20",
        "JNR": "U20",
        "JUNIOR": "U20",
        "U20": "U20",
        # Gender only
        "M": "M",
        "F": "F",
        "L": "F",  # Lady
    }

    if cat in category_map:
        result["age_category"] = category_map[cat]

        # Extract gender from category if not provided
        if not result["gender"]:
            if cat.startswith("F") or cat.startswith("L"):
                result["gender"] = "F"
            elif cat.startswith("M") or cat in ["V", "VM", "SV", "SSV"]:
                result["gender"] = "M"
    else:
        # Keep original if we don't recognize it
        result["age_category"] = category

    return result


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
        auto_detect: bool = True,
        default_age_category: Optional[str] = None,
        default_gender: Optional[str] = None
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
        self.default_age_category = default_age_category
        self.default_gender = default_gender
    
    def normalize(
        self, df: pd.DataFrame, return_dataframe: bool = False
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
        # Support generic 'finish_time' by remapping to seconds for parsing
        if "finish_time" in mapping_dict and "finish_time_seconds" not in mapping_dict:
            mapping_dict["finish_time_seconds"] = mapping_dict.pop("finish_time")

        results = []
        for idx, row in df.iterrows():
            result = self._normalize_row(row, mapping_dict)
            results.append(result)
        
        # Auto-calculate position_gender and position_category if not already set
        results = self._calculate_positions(results)
        
        if return_dataframe:
            return self._results_to_dataframe(results)

        return results
    
    def _calculate_positions(self, results: List[NormalizedRaceResult]) -> List[NormalizedRaceResult]:
        """
        Calculate position_gender and position_category for results that don't have them.
        
        Groups by gender and age_category, sorting by position_overall or finish_time_seconds.
        """
        if not results:
            return results
        
        # Convert to dicts for easier mutation
        results_data = [r.model_dump() for r in results]
        
        # Filter to only finished results for position calculations
        finished_indices = [i for i, r in enumerate(results_data) 
                           if r.get('race_status') == RaceStatus.FINISHED.value]
        
        # Sort by position_overall if available, else by finish_time_seconds
        def sort_key(idx):
            r = results_data[idx]
            if r.get('position_overall') is not None:
                return (0, r['position_overall'])
            elif r.get('finish_time_seconds') is not None:
                return (1, r['finish_time_seconds'])
            else:
                return (2, 0)
        
        finished_sorted = sorted(finished_indices, key=sort_key)
        
        # Calculate position_gender
        gender_positions = {}
        for idx in finished_sorted:
            r = results_data[idx]
            if r.get('position_gender') is None and r.get('gender'):
                gender = r['gender']
                if gender not in gender_positions:
                    gender_positions[gender] = 0
                gender_positions[gender] += 1
                r['position_gender'] = gender_positions[gender]
        
        # Calculate position_category
        category_positions = {}
        for idx in finished_sorted:
            r = results_data[idx]
            if r.get('position_category') is None and r.get('age_category'):
                category = r['age_category']
                if category not in category_positions:
                    category_positions[category] = 0
                category_positions[category] += 1
                r['position_category'] = category_positions[category]
        
        # Convert back to NormalizedRaceResult objects
        return [NormalizedRaceResult(**data) for data in results_data]
    
    def _auto_detect_columns(self, df: pd.DataFrame) -> Optional[ColumnMapping]:
        """
        Attempt to auto-detect column mappings from DataFrame columns.

        Uses fuzzy matching to find likely candidates for standard fields.
        Special handling: If both Firstname and Surname columns exist,
        don't map either to 'name' - they'll be combined during normalization.
        """
        columns = df.columns.tolist()
        columns_lower = [str(c).lower() for c in columns]
        mapping = ColumnMapping()
        
        # Check if we have separate firstname and surname columns
        has_firstname = any('firstname' in c for c in columns_lower)
        has_surname = any('surname' in c for c in columns_lower)
        
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
            'finish_time_seconds': ['finish.*second', 'time.*second', '^time$', 'final.*time'],
            'finish_time_minutes': ['finish.*minute', 'time.*minute', '^time$', 'final.*time'],
            'age_category': ['category', 'age.*cat', 'age.*group', '^cat:?$','cat'],
            'gender': ['gender', 'sex'],
            'race_year': ['year'],
            'race_status': ['status', 'result', 'dnf', 'dns'],
        }

        import re

        for field, patterns_list in patterns.items():
            # Skip mapping 'name' if we have separate firstname/surname columns
            if field == 'name' and has_firstname and has_surname:
                continue
            
            for col in columns:
                col_lower = str(col).lower()
                for pattern in patterns_list:
                    if re.search(pattern, col_lower):
                        setattr(mapping, field, col)
                        break

        return mapping if mapping.get_mapping_dict() else None

    def _normalize_row(
        self, row: pd.Series, mapping_dict: Dict[str, str]
    ) -> NormalizedRaceResult:
        """Normalize a single row to NormalizedRaceResult."""
        data = {}

        # Map columns to standard fields
        for field, column in mapping_dict.items():
            if column in row.index:
                value = row[column]
                # Detect explicit status tokens from raw values
                if isinstance(value, str):
                    raw_upper = value.strip().upper()
                    if "DNF" in raw_upper and "race_status" not in data:
                        data["race_status"] = RaceStatus.DNF
                    elif "DNS" in raw_upper and "race_status" not in data:
                        data["race_status"] = RaceStatus.DNS
                    elif "DSQ" in raw_upper and "race_status" not in data:
                        data["race_status"] = RaceStatus.DSQ
                data[field] = self._convert_value(field, value)
        
        # Combine firstname and surname if both are available but name is not
        # This handles sources with separate Firstname/Surname columns
        if 'name' not in data or not data['name']:
            firstname = None
            surname = None
            
            # Look for firstname and surname columns in the raw row
            for col in row.index:
                col_lower = str(col).lower()
                if 'firstname' in col_lower:
                    fn = row[col]
                    firstname = str(fn).strip() if not (isinstance(fn, float) and pd.isna(fn)) else None
                elif 'surname' in col_lower:
                    sn = row[col]
                    surname = str(sn).strip() if not (isinstance(sn, float) and pd.isna(sn)) else None
            
            # Combine them: prefer "Surname Firstname" format
            if surname or firstname:
                parts = [p for p in [surname, firstname] if p]
                if parts:
                    data['name'] = ' '.join(parts)
        
        # Parse time fields - handle both seconds and minutes fields
        time_fields = {
            "chip_time_seconds": None,
            "chip_time_minutes": "chip_time_seconds",
            "gun_time_seconds": None,
            "gun_time_minutes": "gun_time_seconds",
            "finish_time_seconds": None,
            "finish_time_minutes": "finish_time_seconds",
        }

        for field, seconds_field in time_fields.items():
            if field in data and isinstance(data[field], str):
                # Parse string to seconds
                parsed_seconds = self.time_parser.parse(data[field])
                if field.endswith("_seconds"):
                    data[field] = parsed_seconds
                else:
                    # For minutes fields, store seconds in corresponding seconds field
                    if parsed_seconds is not None:
                        data[field] = parsed_seconds / 60
                        if seconds_field:
                            data[seconds_field] = parsed_seconds

        # Auto-detect race status if not explicitly set
        if "race_status" not in data:
            # Check if all time fields are None/missing
            has_time = any(
                [
                    data.get("finish_time_seconds"),
                    data.get("finish_time_minutes"),
                    data.get("chip_time_seconds"),
                    data.get("chip_time_minutes"),
                    data.get("gun_time_seconds"),
                    data.get("gun_time_minutes"),
                ]
            )

            if not has_time:
                # If no time detected and no explicit status, assume DNF
                data["race_status"] = RaceStatus.DNF
            else:
                data["race_status"] = RaceStatus.FINISHED

        # Normalize club names
        if "club" in data:
            data["club"] = normalize_club_name(data["club"])

        # Parse age category and potentially extract gender
        if "age_category" in data:
            cat_result = parse_age_category(data["age_category"], data.get("gender"))
            data["age_category"] = cat_result["age_category"]
            # Update gender if it was extracted from category and not already set
            if cat_result['gender'] and not data.get('gender'):
                data['gender'] = cat_result['gender']

        # If no category provided, default to senior male
        # - If gender is unknown or missing, set gender='M' and age_category='M'
        # - If gender is explicitly male, set age_category='M'
        def _is_missing(val):
            return val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and val.strip() == '')

        if _is_missing(data.get('age_category')):
            default_cat = (self.default_age_category or 'M')
            # Normalize default_cat formatting
            default_cat = str(default_cat).strip()
            if _is_missing(data.get('gender')):
                # Prefer explicit default gender if provided, else infer from category
                if self.default_gender:
                    data['gender'] = str(self.default_gender).strip().upper()
                else:
                    first = default_cat[:1].upper() if default_cat else 'M'
                    if first in ['M', 'F', 'N']:
                        data['gender'] = first
                    else:
                        data['gender'] = Gender.MALE.value
                data['age_category'] = default_cat or 'M'
            else:
                if str(data.get('gender')).upper() == Gender.MALE.value and not default_cat:
                    data['age_category'] = 'M'
                else:
                    data['age_category'] = default_cat or data.get('age_category')
        
        # Add metadata
        if self.race_name:
            data["race_name"] = self.race_name
        if self.race_year:
            data["race_year"] = self.race_year
        if self.race_category:
            data["race_category"] = self.race_category

        # Store unmapped columns as metadata
        mapped_cols = set(mapping_dict.values())
        for col, value in row.items():
            if col not in mapped_cols and not pd.isna(value):
                data.setdefault("metadata", {})[col] = value

        try:
            return NormalizedRaceResult(**data)
        except Exception as e:
            if self.strict:
                raise
            # Return partially valid result
            return NormalizedRaceResult(
                **{k: v for k, v in data.items() if k != "metadata"}
            )

    def _convert_value(self, field: str, value: Any) -> Any:
        """Convert a value to the appropriate type for the field."""
        # Some sources yield duplicate column names, giving pandas.Series cells.
        if isinstance(value, pd.Series):
            non_null = value.dropna()
            value = non_null.iloc[0] if len(non_null) else None
        elif isinstance(value, (list, tuple)):
            non_null = [v for v in value if not (isinstance(v, float) and pd.isna(v))]
            value = non_null[0] if non_null else None

        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        if field in [
            "position_overall",
            "position_gender",
            "position_category",
            "race_year",
        ]:
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None

        elif field == "gender":
            str_val = str(value).strip().upper()
            for g in Gender:
                if g.value == str_val or g.name == str_val:
                    return g.value
            return None

        elif field in ["chip_time_seconds", "gun_time_seconds", "finish_time_seconds"]:
            # Preserve strings for parsing (e.g., 'MM:SS' or 'HH:MM:SS')
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return value.strip()
            return None

        return value

    def _results_to_dataframe(
        self, results: List[NormalizedRaceResult]
    ) -> pd.DataFrame:
        """Convert list of results to DataFrame."""
        records = []
        for result in results:
            record = result.model_dump(exclude={"metadata"})
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
    **normalizer_kwargs,
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
        **normalizer_kwargs,
    )

    return normalizer.normalize(df, return_dataframe=return_dataframe)
