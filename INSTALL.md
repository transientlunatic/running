# Running Results Package - Installation & Quick Start

## Package Structure

```
running_results/
├── running_results/           # Main package directory
│   ├── __init__.py           # Package initialization with main exports
│   ├── data.py               # Data fetching from web and files
│   ├── transform.py          # Data transformation utilities
│   ├── plotting.py           # Visualization with Kentigern style
│   └── stats.py              # Statistical analysis functions
├── examples/                 # Example scripts
│   ├── tinto_example.py     # Tinto Hill Race analysis
│   ├── edinburgh_example.py # Edinburgh Marathon analysis
│   └── comparison_example.py # Multi-race comparison
├── setup.py                  # Package installation script
├── requirements.txt          # Package dependencies
├── README_PACKAGE.md         # Full package documentation
├── Package Demo.ipynb        # Interactive demo notebook
├── test_package.py          # Basic test suite
└── LICENSE                   # MIT License

```

## Installation

### Option 1: Install in development mode (recommended for local use)

This allows you to edit the package code and immediately see changes:

```bash
cd /home/daniel/projects/running-results
pip install -e .
```

### Option 2: Install dependencies only

If you just want to use the package in this directory:

```bash
pip install -r requirements.txt
```

### Option 3: Install as a regular package

```bash
cd /home/daniel/projects/running-results
pip install .
```

## Quick Test

After installation, verify everything works:

```bash
python test_package.py
```

## Usage

### In Python scripts:

```python
from running_results import (
    RaceDataFetcher,
    TimeConverter,
    RacePlotter,
    RaceStatistics
)
```

### In Jupyter notebooks:

See [Package Demo.ipynb](Package%20Demo.ipynb) for interactive examples.

### Run example scripts:

```bash
# Analyze Tinto Hill Race data
python examples/tinto_example.py

# Analyze Edinburgh Marathon data
python examples/edinburgh_example.py

# Compare multiple races
python examples/comparison_example.py
```

## What This Package Does

Based on your Edinburgh Marathon and Tinto notebooks, this package extracts the common patterns into reusable components:

### 1. Data Fetching (`running_results.data`)
- `RaceDataFetcher`: Generic web scraper for HTML tables
- `PaginatedRaceDataFetcher`: Handles paginated results automatically
- `MultiYearRaceData`: Fetch multiple years of the same race
- `CSVRaceData`: Load from CSV files

### 2. Data Transformation (`running_results.transform`)
- `TimeConverter`: HH:MM:SS ↔ seconds/minutes conversion
- `NameParser`: Parse runner names (using nameparser library)
- `ColumnStandardizer`: Map different column names to standard names
- `RaceDataTransformer`: Pipeline for complex transformations

### 3. Visualization (`running_results.plotting`)
- `KentigernPlot`: Your signature plotting style as a context manager
- `RacePlotter`: Ready-to-use plotting functions:
  - Finish time distributions (KDE)
  - Gender comparisons
  - Cumulative distributions
  - Histograms
  - Club vs non-club comparisons

### 4. Statistics (`running_results.stats`)
- `RaceStatistics`: Calculate race stats:
  - Quantiles and percentiles
  - Category breakdowns
  - Gender comparisons
  - Club comparisons
  - Top performers
- `RaceComparison`: Compare multiple races/years

## Extending the Package

The package is designed to be extensible:

```python
# Add custom data source
class MyRaceData(RaceDataSource):
    def fetch(self):
        # Your custom fetching logic
        return dataframe

# Add custom transformation
from running_results import RaceDataTransformer

class MyTransformer(RaceDataTransformer):
    @staticmethod
    def add_pace(df, distance_km):
        df['Pace'] = df['FinishTime (minutes)'] / distance_km
        return df

# Add custom statistics
from running_results import RaceStatistics

class MyStats(RaceStatistics):
    def calculate_splits(self):
        # Your custom statistics
        pass
```

## Next Steps

1. Install the package: `pip install -e .`
2. Run the test suite: `python test_package.py`
3. Open [Package Demo.ipynb](Package%20Demo.ipynb) to see interactive examples
4. Try the example scripts in `examples/`
5. Adapt for your own race analyses!

## Migrating Existing Notebooks

To update your existing notebooks to use this package:

**Before:**
```python
# Lots of repeated code for fetching, transforming, plotting
for year in years:
    data_url = url.format(year=year)
    extract = pandas.read_html(requests.get(data_url).text)
    # ... more transformation code
```

**After:**
```python
from running_results import MultiYearRaceData, RaceDataTransformer, RacePlotter

fetcher = MultiYearRaceData(url_template, years)
data = fetcher.fetch()
data = transformer.transform(data)
plotter.plot_finish_time_distribution(data)
```

Much cleaner and reusable!
