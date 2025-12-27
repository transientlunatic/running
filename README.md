# Running Results Analysis

Analysis notebooks and tools for running race results, including Edinburgh Marathon, Tinto Hill Race, Great Scottish Run, and others.

## 🎉 New: Running Results Package!

This repository now includes a complete Python package that makes race analysis easier and more consistent. The package extracts common patterns from the analysis notebooks into reusable components.

### Quick Start

```bash
# Install the package
pip install -e .

# Run demo notebook
jupyter notebook "Package Demo.ipynb"

# Or use in your code
from running_results import RacePlotter, RaceStatistics
```

See **[INSTALL.md](INSTALL.md)** for installation instructions and **[PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md)** for a complete overview.

## Package Features

- 🔍 **Data Fetching**: Scrape race results from web sources or load from CSV
- 🔧 **Data Transformation**: Time conversion, name parsing, column standardization
- 📊 **Visualization**: Beautiful plots with the Kentigern style
- 📈 **Statistics**: Comprehensive race statistics and comparisons
- 🌐 **RESTful API**: Query and manage race results via HTTP API (NEW!)
- 💾 **Database**: Persistent storage with SQLite for multi-year tracking

### Example Usage

```python
from running_results import (
    PaginatedRaceDataFetcher,
    RacePlotter,
    RaceStatistics
)

# Fetch data
fetcher = PaginatedRaceDataFetcher(url_template, ...)
data = fetcher.fetch()

# Create visualizations
plotter = RacePlotter()
plotter.plot_finish_time_distribution(data, save_path='plot.png')

# Calculate statistics
stats = RaceStatistics(data)
print(stats.percentile_table())
```

## Repository Contents

### Analysis Notebooks
- **Edinburgh Marathon 2024.ipynb** - Edinburgh Marathon analysis
- **Tinto.ipynb** - Tinto Hill Race historical analysis  
- **Plot Data.ipynb** - Visualization examples
- **Parkrun.ipynb** - Parkrun data analysis
- **Package Demo.ipynb** - Interactive package demonstration

### The Running Results Package
- **running_results/** - Main package code
  - `data.py` - Data fetching utilities
  - `transform.py` - Data transformation tools
  - `plotting.py` - Visualization with Kentigern style
  - `stats.py` - Statistical analysis functions
  - `database.py` - SQLite database for persistent storage
  - `api/` - RESTful API with Flask
    - Full API documentation in `api/API_DOCUMENTATION.md`
    - DreamHost deployment guide in `DREAMHOST_DEPLOYMENT.md`

### Example Scripts
- **examples/tinto_example.py** - Tinto analysis workflow
- **examples/edinburgh_example.py** - Edinburgh Marathon workflow
- **examples/comparison_example.py** - Multi-race comparison
- **examples/api_example.py** - RESTful API demo server (NEW!)

### Data Files
- **tinto/** - Historical Tinto Hill Race results (CSV)
- **edinburgh-marathon-2024.csv** - Edinburgh Marathon 2024 results
- **gsr-results-*.csv** - Great Scottish Run results

## The Kentigern Plot Style

The package includes the distinctive Kentigern plotting style featuring:
- Dark blue background (#003B6B)
- Custom color palette (blues and earth tones)
- White text with outline effects for readability
- Consolas monospace font
- Minimal visual clutter

```python
from running_results import KentigernPlot

with KentigernPlot(1, 1) as fig:
    fig.axes[0].plot(x, y)
    fig.axes[0].set_xlabel("Time (minutes)")
```

## Installation

```bash
# Clone the repository
git clone https://github.com/transientlunatic/running.git
cd running

# Install the package and dependencies
pip install -e .
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Documentation

- **[PACKAGE_SUMMARY.md](PACKAGE_SUMMARY.md)** - Package overview and features
- **[README_PACKAGE.md](README_PACKAGE.md)** - Complete package documentation
- **[INSTALL.md](INSTALL.md)** - Installation guide
- **[Package Demo.ipynb](Package%20Demo.ipynb)** - Interactive tutorial
- **[API Documentation](running_results/api/API_DOCUMENTATION.md)** - RESTful API reference (NEW!)
- **[DreamHost Deployment](DREAMHOST_DEPLOYMENT.md)** - FastCGI deployment guide (NEW!)

## RESTful API (NEW!)

The package now includes a complete RESTful API for querying and managing race results:

```bash
# Start the API server
python examples/api_example.py

# Or use programmatically
from running_results.api import create_app, APIConfig

config = APIConfig()
config.API_KEYS = {'your-api-key'}
app = create_app(config=config)
app.run()
```

**Features:**
- Query races, results, and runner histories via HTTP
- Add new results with API key authentication
- FastCGI support for shared hosting (DreamHost)
- Comprehensive documentation with examples

**Example API calls:**
```bash
# List all races
curl http://localhost:5000/api/races

# Get race results
curl http://localhost:5000/api/races/Edinburgh%20Marathon/results?year=2024

# Add new results (requires API key)
curl -X POST http://localhost:5000/api/results \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"race_name": "Test Race", "results": [...]}'
```

See the [API Documentation](running_results/api/API_DOCUMENTATION.md) for complete details.

## Requirements

- Python 3.7+
- pandas
- numpy
- matplotlib
- nameparser
- requests
- tqdm
- pydantic
- flask (for API)
- flask-cors (for API)

All dependencies are listed in [requirements.txt](requirements.txt).

## Testing

Run the test suite to verify the package:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run specific test module
pytest tests/test_api.py
```

## Contributing

This package was designed based on analysis patterns from the Edinburgh Marathon and Tinto Hill Race notebooks. Contributions welcome for:
- Support for additional race result formats
- New statistical measures
- Additional visualization types
- Documentation improvements

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Daniel Williams ([@transientlunatic](https://github.com/transientlunatic))

## Acknowledgments

Data sources:
- Edinburgh Marathon Festival
- Carnethy Hill Running Club (Tinto results)
- Great Scottish Run
- Various Parkrun events
