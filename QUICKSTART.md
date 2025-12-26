# Quick Start: Race Results Normalization

## 60-Second Example

```python
import pandas as pd
from running_results import normalize_race_results, ColumnMapping

# 1. Load your race data
df = pd.read_csv('my_race_results.csv')

# 2. Tell it which columns map to standard fields
mapping = ColumnMapping(
    position_overall='Pos',
    name='Name',
    club='Club',
    finish_time_minutes='Time (min)'
)

# 3. Normalize to standard schema
normalized = normalize_race_results(
    df,
    mapping=mapping,
    race_name='My Race 2024',
    race_year=2024,
    race_category='marathon',
    return_dataframe=True
)

# 4. Now analyze with general-purpose code
print(f"Average time: {normalized['finish_time_minutes'].mean():.0f} min")
print(f"Clubs: {normalized['club'].nunique()}")
```

## For Multiple Races

```python
from running_results import normalize_race_results, ColumnMapping, RaceCategory

# Race 1
df1 = pd.read_csv('edinburgh_marathon.csv')
mapping1 = ColumnMapping(
    position_overall='Position (Overall)',
    name='Name Number',
    chip_time_seconds='Chip Time (seconds)',
    club='Club'
)
norm1 = normalize_race_results(
    df1, mapping1, race_name='Edinburgh Marathon 2024', 
    race_year=2024, race_category='marathon', return_dataframe=True
)

# Race 2 (different format)
df2 = pd.read_csv('gsr_10k.csv')
mapping2 = ColumnMapping(
    position_overall='Pos',
    name='Name',
    finish_time_minutes='Finish Time'
)
norm2 = normalize_race_results(
    df2, mapping2, race_name='Great Scottish Run 2022',
    race_year=2022, race_category='10k', return_dataframe=True
)

# Same analysis code works for both!
for name, df in [('Edinburgh', norm1), ('GSR', norm2)]:
    time_col = 'chip_time_minutes' if 'chip_time_minutes' in df.columns \
               else 'finish_time_minutes'
    print(f"{name}: {df[time_col].mean():.0f} min average")
```

## What Each Parameter Does

```python
mapping = ColumnMapping(
    position_overall='Pos',           # Maps 'Pos' column to 'position_overall'
    position_category='Category Pos',  # Optional: position within age category
    name='Athlete',                    # Participant name
    bib_number='Bib',                 # Race bib number
    gender='Sex',                      # 'M', 'F', 'N', 'U'
    age_category='Age Group',          # e.g., '35-39', 'V40', '40M'
    club='Team',                       # Running club
    finish_time_seconds='Time (s)',    # Finish time in seconds
    finish_time_minutes='Time (min)',  # Finish time in minutes
    chip_time_seconds='Chip (s)',      # Electronic timing in seconds
    chip_time_minutes='Chip (min)',    # Electronic timing in minutes
    gun_time_seconds='Gun (s)',        # From start gun in seconds
    gun_time_minutes='Gun (min)',      # From start gun in minutes
)

# Then create a normalizer
normalizer = normalize_race_results(
    df,
    mapping=mapping,
    race_name='My Race 2024',           # Name of the event
    race_year=2024,                     # Year of the event
    race_category='marathon',           # 'marathon', '10k', '5k', 'parkrun', etc.
    return_dataframe=True               # True for DataFrame, False for list of models
)
```

## Auto-Detection (For Clean Data)

If your data is well-formatted with standard column names:

```python
from running_results import RaceResultsNormalizer

# No need to specify mapping!
normalizer = RaceResultsNormalizer(
    race_name='My Race 2024',
    race_year=2024,
    auto_detect=True  # Let it figure out the columns
)

normalized = normalizer.normalize(df, return_dataframe=True)
```

It looks for columns like:
- Position: "position", "pos", "place", "rank"
- Name: "name", "runner", "participant"
- Time: "chip.*second", "finish.*minute", etc.

## Different Time Formats

```python
from running_results import RaceResultsNormalizer, TimeParser, ColumnMapping

# If your times are HH:MM:SS
mapping = ColumnMapping(
    position_overall='Pos',
    name='Name',
    finish_time_minutes='Time'  # "02:30:45" format
)

normalizer = RaceResultsNormalizer(
    mapping=mapping,
    time_parser=TimeParser(format='HH:MM:SS'),  # Specify format
    race_name='Marathon 2024',
    race_year=2024
)

normalized = normalizer.normalize(df, return_dataframe=True)
# Now has both finish_time_seconds and finish_time_minutes
```

Time format options:
- `'HH:MM:SS'` - Hours:Minutes:Seconds
- `'MM:SS'` - Minutes:Seconds
- `'seconds'` - Already in seconds (just convert to float)

## Using Normalized Data

```python
# Simple statistics
normalized['chip_time_minutes'].mean()      # Average time
normalized['chip_time_minutes'].std()       # Standard deviation
normalized['club'].value_counts()           # Clubs represented
normalized['age_category'].unique()         # Age groups in race

# Filtering
sub_60 = normalized[normalized['chip_time_minutes'] < 60]
print(f"{len(sub_60)} runners finished under 60 minutes")

# Grouping
by_club = normalized.groupby('club')['chip_time_minutes'].agg(['mean', 'median', 'count'])
print(by_club)

# Export normalized data
normalized.to_csv('normalized_results.csv', index=False)
```

## Accessing Extra Fields

If your data has columns not in the standard mapping, they're preserved:

```python
# If source data has 'BibColor' column
normalized['BibColor']  # Still available

# All unmapped columns are preserved in the returned DataFrame
```

## Common Patterns

### Pattern 1: Combine Multiple Races
```python
races = []
for race_data in race_data_list:
    norm = normalize_race_results(
        race_data['df'],
        mapping=race_data['mapping'],
        race_name=race_data['name'],
        race_year=race_data['year'],
        race_category=race_data['category'],
        return_dataframe=True
    )
    races.append(norm)

# Combine all races
combined = pd.concat(races, ignore_index=True)

# Now analyze across all races
combined.groupby('race_name')['chip_time_minutes'].mean()
```

### Pattern 2: Bulk Processing
```python
import glob

for csv_file in glob.glob('races/*.csv'):
    df = pd.read_csv(csv_file)
    normalized = normalize_race_results(
        df,
        mapping=my_mapping,
        race_year=2024,
        race_name=csv_file.stem,
        return_dataframe=True
    )
    normalized.to_csv(f'normalized/{csv_file.stem}.csv')
```

### Pattern 3: Pipeline Integration
```python
from running_results import RaceStatistics, RacePlotter

# Normalize
normalized = normalize_race_results(df, mapping, race_name='...', return_dataframe=True)

# Analyze
stats = RaceStatistics(normalized)
quantiles = stats.quantiles('chip_time_minutes')

# Plot
plotter = RacePlotter(normalized)
plotter.time_distribution()
```

## Troubleshooting

**Q: "KeyError: 'Position (Overall)'"**
- A: Your mapping column name doesn't match. Check exact spelling (case-sensitive)

**Q: Times look wrong (1000 minutes instead of 100)**
- A: Wrong time format. Check if format should be 'MM:SS' not 'HH:MM:SS'

**Q: Some fields are None**
- A: That's OK! Optional fields become None if not in source data

**Q: I don't know what columns I have**
- A: Run this first:
  ```python
  df = pd.read_csv('race.csv')
  print(df.columns.tolist())
  print(df.head(2))
  ```

## Next Steps

1. Run the interactive notebook: `Race Results Normalization.ipynb`
2. Check the example script: `examples/normalization_example.py`
3. Read the full guide: `NORMALIZATION_GUIDE.md`

## API Quick Reference

```python
# Main functions
from running_results import (
    normalize_race_results,           # Convenience function
    RaceResultsNormalizer,            # Main class
    ColumnMapping,                    # Define column mappings
    TimeParser,                       # Handle time formats
    NormalizedRaceResult,             # Data model
    RaceCategory,                     # Enum: 'marathon', '10k', etc.
    Gender                            # Enum: 'M', 'F', 'N', 'U'
)

# Basic usage
normalized = normalize_race_results(
    df,
    mapping=ColumnMapping(...),
    race_name='Race Name',
    race_year=2024,
    race_category='marathon',
    return_dataframe=True
)
```
