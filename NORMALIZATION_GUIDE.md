# Race Results Normalization Guide

## Overview

The `running_results.models` module provides a Pydantic-based system for normalizing race results data from any source into a consistent, validated schema. This enables writing general-purpose analysis code that works across different races, events, and data formats.

## Why Normalization Matters

When collecting race results from different sources, you encounter:
- **Different column names**: "Position", "Pos", "Place", "Rank", etc.
- **Different data formats**: Times as "HH:MM:SS", minutes, seconds, or mixed
- **Different schemas**: Some races have chip times, some have gun times, some have neither
- **Missing data**: Different races provide different fields

Without normalization, analysis code becomes complex with numerous conditional branches for each data source.

**With normalization**, you write analysis code once and it works for all races.

## Core Components

### 1. `NormalizedRaceResult`

The standard schema that all race results are normalized to. Key fields:

```python
class NormalizedRaceResult(BaseModel):
    # Position fields
    position_overall: Optional[int]
    position_gender: Optional[int]
    position_category: Optional[int]
    
    # Participant info
    name: Optional[str]
    bib_number: Optional[str]
    gender: Optional[Gender]  # 'M', 'F', 'N', 'U'
    age_category: Optional[str]  # '35M', 'V40', etc.
    club: Optional[str]
    
    # Time fields (automatic conversion between formats)
    finish_time_seconds: Optional[float]
    finish_time_minutes: Optional[float]
    chip_time_seconds: Optional[float]
    chip_time_minutes: Optional[float]
    gun_time_seconds: Optional[float]
    gun_time_minutes: Optional[float]
    
    # Metadata
    race_name: Optional[str]
    race_date: Optional[str]
    race_year: Optional[int]
    race_category: Optional[RaceCategory]  # 'marathon', '10k', 'parkrun', etc.
    
    # Additional fields from source
    metadata: Dict[str, Any]
```

### 2. `ColumnMapping`

Defines how columns in your source DataFrame map to normalized fields:

```python
mapping = ColumnMapping(
    position_overall='Position (Overall)',
    name='Name Number',
    club='Club',
    chip_time_seconds='Chip Time (seconds)',
    age_category='Category'
)
```

### 3. `TimeParser`

Handles parsing of time strings into seconds:

```python
# Default HH:MM:SS format
parser = TimeParser(format='HH:MM:SS')
seconds = parser.parse('02:23:12')  # Returns 8592.0

# MM:SS format
parser = TimeParser(format='MM:SS')
seconds = parser.parse('23:12')  # Returns 1392.0

# Already in seconds
parser = TimeParser(format='seconds')
seconds = parser.parse('8592')  # Returns 8592.0
```

### 4. `RaceResultsNormalizer`

The main class that orchestrates the normalization:

```python
normalizer = RaceResultsNormalizer(
    mapping=mapping,
    time_parser=TimeParser(format='HH:MM:SS'),
    race_name='Edinburgh Marathon 2024',
    race_year=2024,
    race_category=RaceCategory.MARATHON,
    strict=False,  # Warnings instead of errors on validation issues
    auto_detect=True  # Try to auto-detect column mappings
)

# Normalize to list of models
results: List[NormalizedRaceResult] = normalizer.normalize(df)

# Or as DataFrame
normalized_df: pd.DataFrame = normalizer.normalize(df, return_dataframe=True)
```

## Usage Examples

### Example 1: Basic Normalization

```python
import pandas as pd
from running_results import ColumnMapping, RaceResultsNormalizer, RaceCategory

# Load your data
df = pd.read_csv('race_results.csv')

# Define mapping
mapping = ColumnMapping(
    position_overall='Position',
    name='Name',
    club='Club',
    chip_time_seconds='Time (seconds)'
)

# Normalize
normalizer = RaceResultsNormalizer(
    mapping=mapping,
    race_name='My Race 2024',
    race_year=2024,
    race_category=RaceCategory.MARATHON
)

normalized = normalizer.normalize(df, return_dataframe=True)

# Now all results have consistent structure
print(normalized[['name', 'club', 'chip_time_minutes']].head())
```

### Example 2: Convenience Function

```python
from running_results import normalize_race_results, ColumnMapping

df = pd.read_csv('race_results.csv')

mapping = ColumnMapping(
    position_overall='Pos',
    name='Athlete',
    finish_time_minutes='Time'
)

normalized = normalize_race_results(
    df,
    mapping=mapping,
    race_name='5K Run 2024',
    race_year=2024,
    race_category='5k',
    return_dataframe=True
)
```

### Example 3: Time Format Parsing

```python
from running_results import TimeParser, RaceResultsNormalizer, ColumnMapping

# Data with HH:MM:SS format
mapping = ColumnMapping(
    position_overall='Pos',
    name='Name',
    finish_time_minutes='Time'  # Source has "02:30:45"
)

normalizer = RaceResultsNormalizer(
    mapping=mapping,
    time_parser=TimeParser(format='HH:MM:SS'),
    race_name='Marathon 2024',
    race_year=2024,
    race_category='marathon'
)

# Times automatically converted to seconds and minutes
normalized = normalizer.normalize(df, return_dataframe=True)
print(normalized['finish_time_seconds'].head())  # 9045.0, etc.
```

### Example 4: Working with Normalized Data

Once normalized, you can write general analysis code:

```python
def get_race_summary(normalized_df: pd.DataFrame) -> dict:
    """Works with ANY normalized race results."""
    
    # Time analysis (works whether times are chip or gun times)
    time_col = 'chip_time_minutes' if 'chip_time_minutes' in normalized_df.columns \
               else 'finish_time_minutes'
    times = normalized_df[time_col].dropna()
    
    return {
        'finishers': len(normalized_df),
        'mean_time': times.mean(),
        'median_time': times.median(),
        'clubs': normalized_df['club'].nunique(),
        'categories': normalized_df['age_category'].nunique()
    }

# Same function works for all races
edin_summary = get_race_summary(edinburgh_normalized)
gsr_summary = get_race_summary(gsr_normalized)
parkrun_summary = get_race_summary(parkrun_normalized)
```

## Auto-Detection

The normalizer can automatically detect column mappings for well-formatted data:

```python
normalizer = RaceResultsNormalizer(
    auto_detect=True  # Try to match columns automatically
    # Don't specify mapping
)

normalized = normalizer.normalize(df)
```

Auto-detection looks for common patterns:
- Position: "position", "pos", "place", "rank"
- Name: "name", "runner", "participant"
- Time: "chip.*second", "gun.*minute", "finish.*second", etc.
- Club: "club", "team"

## Advanced Features

### Custom Validators

Extend `NormalizedRaceResult` for race-specific validation:

```python
from pydantic import field_validator
from running_results.models import NormalizedRaceResult

class MarathonResult(NormalizedRaceResult):
    @field_validator('chip_time_minutes')
    def validate_marathon_time(cls, v):
        if v and v < 120:  # Less than 2 hours
            raise ValueError("Impossible marathon time")
        return v
```

### Handling Missing Data

All fields are optional. Missing data becomes `None`:

```python
# Some races don't have chip times
if result.chip_time_minutes is None:
    # Fall back to gun/finish time
    time = result.gun_time_minutes or result.finish_time_minutes
```

### Accessing Unmapped Fields

Extra columns from source data are preserved in metadata:

```python
normalized = normalizer.normalize(df, return_dataframe=True)

# Original columns that weren't mapped are in metadata
# Access as regular columns in returned DataFrame
print(normalized[['name', 'my_custom_field']].head())
```

## Validations Provided

Pydantic automatically validates:

1. **Type conversion**: Numbers are coerced to int/float automatically
2. **Enum validation**: Gender values must match defined options
3. **Field validators**: Time fields are auto-computed if only one format provided
4. **Optional fields**: Missing data is allowed and returns None

## Common Issues

### Issue: "Column not found"
Solution: Check that column names in ColumnMapping match exactly (case-sensitive).

### Issue: Times are wrong format
Solution: Specify the correct format in TimeParser:
```python
parser = TimeParser(format='MM:SS')  # or 'HH:MM:SS', 'seconds'
```

### Issue: Only some races have a field
Solution: That's fine! Optional fields will be None for races that don't have them:
```python
if result.chip_time_seconds:
    print(f"Chip time: {result.chip_time_seconds}")
```

## Integration with Existing Code

The normalized DataFrames work seamlessly with existing analysis code:

```python
from running_results import RaceStatistics, RacePlotter

# Normalize your data
normalized_df = normalize_race_results(df, mapping, race_name='...')

# Use with existing tools
stats = RaceStatistics(normalized_df)
plotter = RacePlotter(normalized_df)

# Everything works because all DataFrames have the same schema!
```

## Performance

For large datasets (10,000+ rows):
- Normalization is fast: typically <1 second for 10k rows
- Pydantic validation is optimized in v2+
- Consider using `return_dataframe=True` for bulk operations (avoids creating individual model objects)

## See Also

- `Race Results Normalization.ipynb` - Interactive examples
- `examples/normalization_example.py` - Practical usage scripts
- `running_results/models.py` - Full source code with extensive docstrings
