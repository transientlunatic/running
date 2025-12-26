Running Results Documentation
==============================

A Python package for normalizing, analyzing, and storing running race results.

.. image:: https://img.shields.io/badge/Python-3.7%2B-blue
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-green.svg
   :alt: License

Overview
--------

**running-results** is a comprehensive framework for working with race results data. It provides:

* **Data Normalization**: Pydantic-based validation and standardization of race results from diverse sources
* **Database Storage**: SQLite-based persistent storage for tracking races across multiple years
* **Data Import**: Web scraping and file import capabilities with automatic format detection
* **Analysis Tools**: Built-in functions for statistical analysis and data transformation
* **Visualization**: Plotting utilities for race results visualization

Features
--------

Data Normalization
~~~~~~~~~~~~~~~~~~

* Validates and standardizes race results with 23+ optional fields
* Auto-corrects malformed time formats (e.g., ``42::51`` → ``42:51``)
* Normalizes club names (removes common suffixes, standardizes variations)
* Parses age categories (e.g., ``V`` → ``M40``, ``FV`` → ``F40``)
* Handles DNF/DNS/DSQ statuses with enumerated types
* Supports multiple time formats (HH:MM:SS, MM:SS, seconds)

Database Storage
~~~~~~~~~~~~~~~~

* SQLite-based persistent storage
* Track results across multiple years and race editions
* Fast queries with indexed searches
* Runner history tracking
* Club and category analysis

Data Import
~~~~~~~~~~~

* Web scraping from HTML tables with CSS selector support
* File import (CSV, TSV, Excel, HTML)
* Automatic format and delimiter detection
* Column mapping with intelligent defaults
* Direct text import with customizable parsing

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

* Add results from files or URLs
* Generate comprehensive HTML/PDF reports
* Query and filter race data
* Multi-year comparison reports
* Runner history tracking
* Powered by otter-report for professional output

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install -e .

Basic Usage
~~~~~~~~~~~

**Normalize race results:**

.. code-block:: python

   from running_results import RaceResultsNormalizer, ColumnMapping
   import pandas as pd

   # Load raw data
   df = pd.read_csv('race_results.csv')

   # Define column mapping
   mapping = ColumnMapping(
       position_overall='Pos',
       name='Name',
       club='Club',
       finish_time='Time'
   )

   # Normalize
   normalizer = RaceResultsNormalizer(mapping)
   normalized_df = normalizer.normalize(df)

**Use the database:**

.. code-block:: python

   from running_results import RaceResultsManager

   # Initialize manager
   manager = RaceResultsManager('race_results.db')

   # Import from URL
   manager.add_from_url(
       'https://example.com/results.html',
       race_name='Edinburgh Marathon',
       race_year=2024,
       race_category='marathon'
   )

   # Query results
   results_df = manager.get_race('Edinburgh Marathon', race_year=2024)
   runner_history = manager.get_runner_history('John Smith')

   # Search by club
   club_results = manager.search_results(club='Carnethy')

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   cli
   normalization_guide
   database_guide
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/models
   api/database
   api/importers
   api/manager
   api/data
   api/plotting
   api/stats
   api/transform

.. toctree::
   :maxdepth: 1
   :caption: Additional Information

   changelog
   contributing
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
