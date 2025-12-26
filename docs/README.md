# Documentation

This directory contains the Sphinx documentation for the running-results package.

## Building Documentation Locally

### Prerequisites

Install documentation dependencies:

```bash
pip install -e ".[docs]"
```

This installs:
- sphinx>=4.0
- sphinx-kentigern>=0.1.0

### Build HTML Documentation

```bash
cd docs
make html
```

The built documentation will be in `_build/html/`. Open `_build/html/index.html` in your browser.

### Other Formats

```bash
make latexpdf  # Build PDF (requires LaTeX)
make epub      # Build EPUB
make help      # See all available formats
```

## Documentation Structure

- `index.rst` - Main documentation index
- `installation.rst` - Installation guide
- `quickstart.rst` - Quick start guide
- `normalization_guide.rst` - Data normalization guide
- `database_guide.rst` - Database usage guide
- `examples.rst` - Usage examples
- `api/` - API reference documentation
  - `models.rst` - Data models and normalization
  - `database.rst` - Database storage
  - `importers.rst` - Data import utilities
  - `manager.rst` - Unified manager interface
  - `data.rst`, `plotting.rst`, `stats.rst`, `transform.rst` - Other modules
- `changelog.rst` - Version history
- `contributing.rst` - Contributing guidelines
- `license.rst` - License information

## Auto-build to GitHub Pages

Documentation is automatically built and deployed to GitHub Pages via GitHub Actions whenever changes are pushed to the master branch.

The workflow is defined in `.github/workflows/docs.yml`.

View the published documentation at: https://transientlunatic.github.io/running/

## Theme

Documentation uses the [Kentigern](https://github.com/transientlunatic/kentigern) Sphinx theme.
