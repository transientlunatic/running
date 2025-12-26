# Test Suite

This directory contains unit and integration tests for the running_results package.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=running_results

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestNormalizedRaceResult

# Run with verbose output
pytest -v
```

## Test Files

- `conftest.py` - Shared fixtures and test utilities
- `test_models.py` - Tests for data models and normalization (56 tests)
- `test_database.py` - Tests for database storage (18 tests)
- `test_importers.py` - Tests for data import utilities (11 tests)
- `test_manager.py` - Integration tests for manager interface (15 tests)

## Test Coverage

Current coverage: ~47%

Key areas covered:
- Data normalization and validation
- Time parsing and malformed data correction
- Club name normalization  
- Age category parsing
- Database CRUD operations
- File import (CSV, TSV)
- Manager integration workflows

## Known Issues

Some tests may fail due to API differences between test assumptions and actual implementation:
- Database method signatures use `year` instead of `race_year`
- Some methods may not be fully implemented yet
- Mock data may not match exact production data formats

## Continuous Integration

Tests run automatically on:
- Push to master/main/develop branches
- Pull requests
- Manual workflow dispatch

See `.github/workflows/tests.yml` for CI configuration.
