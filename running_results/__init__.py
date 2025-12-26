"""
Running Results Analysis Package
=================================

A framework for analyzing and visualizing running race results data.

Modules:
    - data: Fetching race results from web sources and files
    - transform: Data cleaning and transformation utilities
    - plotting: Visualization tools with consistent styling
    - stats: Statistical analysis functions
"""

__version__ = "0.1.0"

from .data import RaceDataFetcher, CSVRaceData
from .transform import TimeConverter, NameParser, ColumnStandardizer
from .plotting import KentigernPlot, RacePlotter
from .stats import RaceStatistics

__all__ = [
    'RaceDataFetcher',
    'CSVRaceData',
    'TimeConverter',
    'NameParser',
    'ColumnStandardizer',
    'KentigernPlot',
    'RacePlotter',
    'RaceStatistics',
]
