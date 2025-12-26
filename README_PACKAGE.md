# Running Results Analysis Package

A Python framework for analyzing and visualizing running race results data, designed to make race data analysis easier and more consistent.

## Features

- **Data Fetching**: Flexible fetchers for web-based race results (HTML tables, paginated results) and CSV files
- **Data Transformation**: Time conversion, name parsing, column standardization across different race formats
- **Visualization**: Consistent plotting style with KDE plots, histograms, and cumulative distributions
- **Statistics**: Comprehensive race statistics including quantiles, category breakdowns, and comparisons

## Installation

From the project directory:

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install pandas numpy matplotlib nameparser requests tqdm
```

## Quick Start

### Fetching Race Data

```python
from running_results import PaginatedRaceDataFetcher

# Fetch Edinburgh Marathon results
fetcher = PaginatedRaceDataFetcher(
    url_template="https://www.edinburghmarathon.com/results?event={event}&gender={gender}&page={page}",
    page_start=1,
    max_pages=700,
    other_params={'event': [1007], 'gender': ['M', 'F']}
)
data = fetcher.fetch()
```

### Transforming Data

```python
from running_results import TimeConverter, ColumnStandardizer, RaceDataTransformer

# Standardize column names
standardizer = ColumnStandardizer()
data = standardizer.standardize(data)

# Convert times to seconds/minutes
transformer = RaceDataTransformer()
data = transformer.add_time_conversions(data, time_column='ChipTime')
```

### Creating Visualizations

```python
from running_results import KentigernPlot, RacePlotter

# Use the Kentigern style directly
with KentigernPlot(1, 1) as fig:
    fig.axes[0].plot(x, y)
    fig.axes[0].set_xlabel("Time (minutes)")

# Or use high-level plotting functions
plotter = RacePlotter()
fig = plotter.plot_finish_time_distribution(data, save_path='finish_times.png')
fig = plotter.plot_gender_comparison(data, gender_column='Category')
fig = plotter.plot_cumulative_distribution(data)
```

### Calculating Statistics

```python
from running_results import RaceStatistics

stats = RaceStatistics(data)

# Get quantiles
quantiles = stats.quantiles()

# Compare genders
gender_comp = stats.gender_comparison(gender_column='Category')

# Get top performers
top_10 = stats.top_performers(n=10)

# Percentile table
percentiles = stats.percentile_table()
```

## Complete Example: Tinto Hill Race Analysis

```python
from running_results import (
    MultiYearRaceData, 
    ColumnStandardizer, 
    NameParser,
    RaceDataTransformer,
    RacePlotter,
    RaceStatistics
)

# Fetch multiple years of data
fetcher = MultiYearRaceData(
    url_template="https://carnethy.com/ri_results/tinto/t_{year}.htm",
    years=range(1985, 2004),
    table_index=-2
)
data = fetcher.fetch()

# Transform data
transformer = RaceDataTransformer()
data = transformer.clean_header_row(data, header_row_index=0)

# Parse names
data = NameParser.add_name_columns(data, name_column='Name')

# Standardize columns
standardizer = ColumnStandardizer({
    'Posn': 'RunnerPosition',
    'Cat.': 'RunnerCategory',
    'Time': 'FinishTime'
})
data = standardizer.standardize(data)

# Select relevant columns
data = transformer.select_columns(
    data, 
    ['RunnerPosition', 'Surname', 'Firstname', 'Club', 'RunnerCategory', 'FinishTime']
)

# Create visualizations
plotter = RacePlotter()
plotter.plot_finish_time_distribution(data)

# Calculate statistics
stats = RaceStatistics(data)
print(stats.summary_statistics())
```

## Complete Example: Edinburgh Marathon 2024

```python
from running_results import (
    PaginatedRaceDataFetcher,
    TimeConverter,
    RaceDataTransformer,
    RacePlotter,
    RaceStatistics
)

# Fetch data
fetcher = PaginatedRaceDataFetcher(
    url_template="https://www.edinburghmarathon.com/results?event={event}&gender={gender}&page={page}",
    page_start=1,
    max_pages=700,
    other_params={'event': [1007], 'gender': ['M', 'F', 'N']}
)
data = fetcher.fetch()

# Process every other row (site-specific quirk)
data = data[::2]

# Extract category from position
transformer = RaceDataTransformer()
data = transformer.extract_category_from_position(
    data,
    position_col='Position (Category)',
    category_col='Category'
)

# Convert times
data['Chip Time (seconds)'] = data['Chip Time'].apply(TimeConverter.to_seconds)
data['Chip Time (minutes)'] = data['Chip Time (seconds)'] / 60

# Create plots
plotter = RacePlotter()
plotter.plot_finish_time_distribution(
    data, 
    time_column='Chip Time (minutes)',
    bins=range(120, 500, 1),
    save_path='edinburgh-2024-finish-times.png'
)

plotter.plot_gender_comparison(
    data,
    time_column='Chip Time (minutes)',
    gender_column='Category',
    bins=range(120, 420, 1),
    save_path='edinburgh-2024-gender-comparison.png'
)

# Statistics
stats = RaceStatistics(data)
print("Median finish time:", stats.time_for_percentile(50), "minutes")
print("\nGender comparison:")
print(stats.gender_comparison(gender_column='Category', time_column='Chip Time (minutes)'))
```

## Module Overview

### `running_results.data`
- `RaceDataFetcher`: Flexible web scraper for race results
- `PaginatedRaceDataFetcher`: Specialized for paginated results
- `MultiYearRaceData`: Fetch multiple years of the same race
- `CSVRaceData`: Load results from CSV files

### `running_results.transform`
- `TimeConverter`: Convert between time formats (HH:MM:SS ↔ seconds/minutes)
- `NameParser`: Parse runner names into components
- `ColumnStandardizer`: Standardize column names across different formats
- `RaceDataTransformer`: Pipeline for data transformation

### `running_results.plotting`
- `KentigernPlot`: Context manager for consistent plot styling
- `RacePlotter`: High-level plotting functions for race data

### `running_results.stats`
- `RaceStatistics`: Calculate race statistics and summaries
- `RaceComparison`: Compare multiple races or datasets

## Extending the Framework

The package is designed to be extensible. You can:

1. **Add custom data sources**: Subclass `RaceDataSource`
2. **Create custom transformations**: Add methods to `RaceDataTransformer`
3. **Define custom statistics**: Extend `RaceStatistics`
4. **Customize plot styles**: Modify `KentigernPlot` or create new plotting classes

Example custom transformation:

```python
from running_results import RaceDataTransformer

class MyRaceTransformer(RaceDataTransformer):
    @staticmethod
    def add_pace_column(df, distance_km=21.1):
        """Add pace in min/km."""
        df['Pace (min/km)'] = df['FinishTime (minutes)'] / distance_km
        return df

# Use it
transformer = MyRaceTransformer()
data = transformer.add_pace_column(data, distance_km=42.195)
```

## The Kentigern Style

The plotting style is inspired by Scottish design aesthetics:
- Color palette: Blues and earth tones (#79C4F2, #3BBCD9, #038C8C, #BDBF7E, #8C3D20)
- Dark blue background (#003B6B) 
- White text with outline effects for readability
- Consolas monospace font
- Minimal visual clutter (hidden spines, subtle gridlines)

This creates professional, publication-ready visualizations perfect for race reports and analyses.

## Requirements

- Python 3.7+
- pandas
- numpy
- matplotlib
- nameparser
- requests
- tqdm

## License

MIT License - feel free to use and modify for your own race analyses!

## Contributing

This package was designed based on analysis patterns from the Edinburgh Marathon and Tinto Hill Race notebooks. Contributions are welcome to:
- Add support for more race result formats
- Implement additional statistical measures
- Create new visualization types
- Improve documentation and examples
