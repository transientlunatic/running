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

from .data import RaceDataFetcher, CSVRaceData, PaginatedRaceDataFetcher, MultiYearRaceData
from .transform import TimeConverter, NameParser, ColumnStandardizer, RaceDataTransformer
from .plotting import KentigernPlot, RacePlotter
from .stats import RaceStatistics, RaceComparison
from .database import RaceResultsDatabase
from .importers import ResultsImporter, SmartImporter
from .manager import RaceResultsManager
from .ranking import RunnerRegistry, EloRanking
from .cli import cli
from .reporting import generate_race_report, generate_comparison_report, generate_runner_report
from .api import create_app, get_app, APIConfig

from .models import (
    NormalizedRaceResult,
    ColumnMapping,
    TimeParser,
    RaceResultsNormalizer,
    RaceCategory,
    Gender,
    RaceStatus,
    normalize_race_results,
    fix_malformed_time,
    normalize_club_name,
    parse_age_category,
)

__all__ = [
    'RaceDataFetcher',
    'CSVRaceData',
    'PaginatedRaceDataFetcher',
    'MultiYearRaceData',
    'TimeConverter',
    'NameParser',
    'ColumnStandardizer',
    'RaceDataTransformer',
    'KentigernPlot',
    'RacePlotter',
    'RaceStatistics',
    'RaceComparison',
    'NormalizedRaceResult',
    'ColumnMapping',
    'TimeParser',
    'RaceResultsNormalizer',
    'RaceCategory',
    'Gender',
    'RaceStatus',
    'normalize_race_results',
    'fix_malformed_time',
    'normalize_club_name',
    'parse_age_category',
    'RaceResultsDatabase',
    'ResultsImporter',
    'SmartImporter',
    'RaceResultsManager',
    'RunnerRegistry',
    'EloRanking',
    'cli',
    'generate_race_report',
    'generate_comparison_report',
    'generate_runner_report',
    'create_app',
    'get_app',
    'APIConfig',
]
