# Running Results Package - Summary

## What Was Created

A complete Python package framework for analyzing running race results, based on the patterns in your Edinburgh Marathon and Tinto notebooks.

## Package Structure

```
running_results/
├── running_results/              # Main package
│   ├── __init__.py              # Package exports
│   ├── data.py                  # Data fetching (347 lines)
│   ├── transform.py             # Data transformation (315 lines)
│   ├── plotting.py              # Visualization (478 lines)
│   └── stats.py                 # Statistics (388 lines)
│
├── examples/                     # Example scripts
│   ├── tinto_example.py         # Tinto Hill Race workflow
│   ├── edinburgh_example.py     # Edinburgh Marathon workflow
│   └── comparison_example.py    # Multi-race comparison
│
├── Package Demo.ipynb           # Interactive demonstration
├── setup.py                     # Installation script
├── requirements.txt             # Dependencies
├── README_PACKAGE.md            # Full documentation (400+ lines)
├── INSTALL.md                   # Installation guide
├── test_package.py             # Test suite
└── LICENSE                      # MIT License
```

## Key Features

### 1. Data Fetching Module (`data.py`)

**Classes:**
- `RaceDataFetcher` - Generic HTML table scraper with flexible URL parameters
- `PaginatedRaceDataFetcher` - Auto-detects pagination end
- `MultiYearRaceData` - Fetch historical data across years
- `CSVRaceData` - Load from CSV files

**Example:**
```python
fetcher = PaginatedRaceDataFetcher(
    url_template="https://example.com?page={page}&gender={gender}",
    other_params={'gender': ['M', 'F']}
)
data = fetcher.fetch()
```

### 2. Transform Module (`transform.py`)

**Classes:**
- `TimeConverter` - Convert "HH:MM:SS" ↔ seconds/minutes
- `NameParser` - Parse names into first/last (uses nameparser library)
- `ColumnStandardizer` - Map variant column names to standard names
- `RaceDataTransformer` - Composable transformation pipeline

**Example:**
```python
# Convert times
data['seconds'] = data['Time'].apply(TimeConverter.to_seconds)

# Standardize columns
standardizer = ColumnStandardizer()
data = standardizer.standardize(data)

# Parse names
data = NameParser.add_name_columns(data, 'Name')
```

### 3. Plotting Module (`plotting.py`)

**Classes:**
- `KentigernPlot` - Your signature style as a context manager
  - Dark blue background (#003B6B)
  - Custom color palette
  - White text with outline effects
  - Consolas font
  
- `RacePlotter` - High-level plotting functions
  - `plot_finish_time_distribution()` - KDE plots
  - `plot_gender_comparison()` - Male/female comparisons
  - `plot_cumulative_distribution()` - Percentile curves
  - `plot_histogram()` - Time histograms
  - `plot_club_comparison()` - Club vs non-club

**Example:**
```python
# Use the style directly
with KentigernPlot(1, 1) as fig:
    fig.axes[0].plot(x, y)

# Or use high-level functions
plotter = RacePlotter()
plotter.plot_finish_time_distribution(data, save_path='plot.png')
```

### 4. Statistics Module (`stats.py`)

**Classes:**
- `RaceStatistics` - Comprehensive race analysis
  - Quantiles and percentiles
  - Category breakdowns
  - Gender/club comparisons
  - Top performers
  - Year-over-year trends
  
- `RaceComparison` - Compare multiple races

**Example:**
```python
stats = RaceStatistics(data)
print(stats.percentile_table())
print(stats.gender_comparison())
print(stats.top_performers(n=10))
```

## Design Principles

1. **Extensible** - Easy to subclass and add custom functionality
2. **Reusable** - Extract common patterns from notebooks
3. **Consistent** - Standardized column names and data formats
4. **Well-documented** - Docstrings, examples, and type hints
5. **Style-preserving** - Maintains your Kentigern plotting aesthetic

## Usage Workflow

### Typical Analysis Flow:

```python
from running_results import *

# 1. Fetch data
fetcher = MultiYearRaceData(url_template, years=range(2000, 2024))
data = fetcher.fetch()

# 2. Transform
transformer = RaceDataTransformer()
data = transformer.clean_header_row(data)
data = NameParser.add_name_columns(data, 'Name')
data = ColumnStandardizer().standardize(data)
data = transformer.add_time_conversions(data, 'FinishTime')

# 3. Analyze
stats = RaceStatistics(data)
print(stats.summary_statistics())

# 4. Visualize
plotter = RacePlotter()
plotter.plot_finish_time_distribution(data)
plotter.plot_gender_comparison(data)
```

## Comparison: Before vs After

### Before (in notebooks):
- Repeated code in each notebook
- Hard to maintain consistency
- Difficult to reuse across projects
- No standardization

### After (with package):
- Clean, reusable code
- Consistent styling and analysis
- Easy to extend and customize
- Standardized column names and workflows
- Production-ready

## Next Steps

1. **Install**: `pip install -e .`
2. **Test**: `python test_package.py`
3. **Explore**: Open `Package Demo.ipynb`
4. **Use**: Import in your notebooks:
   ```python
   from running_results import RacePlotter, RaceStatistics
   ```

## Migration Path

To update existing notebooks:

1. Replace data fetching code with `RaceDataFetcher` or `MultiYearRaceData`
2. Replace transformation code with `ColumnStandardizer` and `TimeConverter`
3. Replace plotting code with `RacePlotter` methods
4. Replace statistical calculations with `RaceStatistics` methods

Example migration for Tinto notebook:
- Lines 1-40 (fetching) → `MultiYearRaceData(...).fetch()`
- Lines 41-60 (transforming) → `RaceDataTransformer` pipeline
- Your existing plots → `plotter.plot_finish_time_distribution(...)`

## Extensibility Examples

### Custom Data Source:
```python
class MyRaceSource(RaceDataSource):
    def fetch(self):
        # Custom fetching logic
        return df
```

### Custom Statistic:
```python
class MyStats(RaceStatistics):
    def pace_analysis(self, distance_km):
        # Custom analysis
        return results
```

### Custom Plot:
```python
with KentigernPlot(2, 2) as fig:
    # Your custom multi-panel visualization
    pass
```

## Files Reference

- **INSTALL.md** - Installation instructions
- **README_PACKAGE.md** - Complete package documentation
- **Package Demo.ipynb** - Interactive tutorial
- **examples/** - Working examples for each race type
- **test_package.py** - Basic functionality tests

## Dependencies

All specified in `requirements.txt`:
- pandas (data manipulation)
- numpy (numerical operations)
- matplotlib (plotting)
- nameparser (name parsing)
- requests (HTTP requests)
- tqdm (progress bars)

Total: ~1,528 lines of well-documented, reusable code!
