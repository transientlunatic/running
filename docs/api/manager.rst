manager - Unified Manager Interface
====================================

.. automodule:: running_results.manager
   :members:
   :undoc-members:
   :show-inheritance:

Main Class
----------

RaceResultsManager
~~~~~~~~~~~~~~~~~~

.. autoclass:: running_results.manager.RaceResultsManager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __enter__, __exit__

Examples
--------

Basic Setup
~~~~~~~~~~~

.. code-block:: python

   from running_results import RaceResultsManager

   # Create manager
   manager = RaceResultsManager('my_races.db')

   # Use as context manager (recommended)
   with RaceResultsManager('my_races.db') as manager:
       results = manager.list_races()

Adding Results from Files
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsManager('races.db') as manager:
       # Add from CSV
       count = manager.add_from_file(
           file_path='tinto_2024.csv',
           race_name='Tinto Hill Race',
           race_year=2024,
           race_category='fell_race'
       )
       print(f"Added {count} results")

       # With custom column mapping
       count = manager.add_from_file(
           file_path='marathon_2024.xlsx',
           race_name='Edinburgh Marathon',
           race_year=2024,
           race_category='marathon',
           column_mapping={
               'Position': 'position_overall',
               'Runner Name': 'name',
               'Gun Time': 'finish_time'
           }
       )

Adding Results from URLs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsManager('races.db') as manager:
       # Import from webpage
       count = manager.add_from_url(
           url='https://example.com/results.html',
           race_name='Local 5K',
           race_year=2024,
           race_category='road_race'
       )

       # Specify table selector
       count = manager.add_from_url(
           url='https://example.com/results.html',
           race_name='Park Run',
           race_year=2024,
           race_category='parkrun',
           table_selector='table.results-table'
       )

Adding Pre-normalized Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.models import NormalizedRaceResult

   results = [
       NormalizedRaceResult(
           position_overall=1,
           name='Alice Smith',
           club='Highland Runners',
           finish_time_seconds=1800
       ),
       NormalizedRaceResult(
           position_overall=2,
           name='Bob Jones',
           club='Carnethy',
           finish_time_seconds=1850
       )
   ]

   with RaceResultsManager('races.db') as manager:
       count = manager.add_results(
           results=results,
           race_name='Custom Race',
           race_year=2024,
           race_category='fell_race'
       )

Querying Results
~~~~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsManager('races.db') as manager:
       # Get specific race results
       df = manager.get_race('Tinto Hill Race', race_year=2024)

       # Get all years of a race
       df = manager.get_race('Tinto Hill Race')

       # Get runner history across all races
       history = manager.get_runner_history('John Smith')

       # Get runner history for specific race
       history = manager.get_runner_history(
           runner_name='John Smith',
           race_name='Tinto Hill Race'
       )

Searching Results
~~~~~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsManager('races.db') as manager:
       # Search by club
       club_results = manager.search_results(club='Carnethy')

       # Search by multiple criteria
       results = manager.search_results(
           race_name='Tinto Hill Race',
           club='Edinburgh',
           min_year=2020,
           max_year=2024
       )

       # Search by age category
       veterans = manager.search_results(age_category='M40')

Listing Races
~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsManager('races.db') as manager:
       # Get summary of all races
       races_df = manager.list_races()
       print(races_df)

       # Output includes:
       # - race_name
       # - race_category
       # - num_years (how many years of data)
       # - first_year
       # - last_year
       # - total_results

Complete Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results import RaceResultsManager

   # Initialize manager
   with RaceResultsManager('my_races.db') as manager:
       # Import multiple years
       for year in range(2020, 2025):
           try:
               count = manager.add_from_file(
                   f'tinto_{year}.csv',
                   race_name='Tinto Hill Race',
                   race_year=year,
                   race_category='fell_race'
               )
               print(f"{year}: {count} results added")
           except FileNotFoundError:
               print(f"{year}: No data file found")

       # Analyze results
       all_results = manager.get_race('Tinto Hill Race')
       
       # Get top performers
       top_10 = all_results.nsmallest(10, 'finish_time_seconds')
       
       # Analyze club participation
       club_stats = all_results.groupby('club').size().sort_values(ascending=False)
       
       # Track a specific runner
       runner = manager.get_runner_history('John Smith', 'Tinto Hill Race')
       print(f"Runner competed {len(runner)} times")

See Also
--------

* :doc:`models` - Data models and normalization
* :doc:`database` - Database storage
* :doc:`importers` - Import utilities
