database - Database Storage
============================

.. automodule:: running_results.database
   :members:
   :undoc-members:
   :show-inheritance:

Main Class
----------

RaceResultsDatabase
~~~~~~~~~~~~~~~~~~~

.. autoclass:: running_results.database.RaceResultsDatabase
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __enter__, __exit__

Examples
--------

Creating a Database
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.database import RaceResultsDatabase

   # Create/open database
   db = RaceResultsDatabase('my_races.db')

   # Use as context manager (recommended)
   with RaceResultsDatabase('my_races.db') as db:
       races = db.get_races()
       print(races)

Adding Races
~~~~~~~~~~~~

.. code-block:: python

   from running_results.database import RaceResultsDatabase
   from running_results.models import RaceCategory

   with RaceResultsDatabase('races.db') as db:
       # Add a race
       race_id = db.add_race(
           race_name='Tinto Hill Race',
           race_category=RaceCategory.FELL_RACE
       )

       # Add a race edition
       edition_id = db.add_race_edition(
           race_id=race_id,
           race_year=2024,
           race_date='2024-06-15',
           source_file='tinto_2024.csv'
       )

Adding Results
~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.models import NormalizedRaceResult
   from running_results.database import RaceResultsDatabase

   # Create results
   results = [
       NormalizedRaceResult(
           position_overall=1,
           name='John Smith',
           club='Carnethy',
           finish_time_seconds=1845
       ),
       NormalizedRaceResult(
           position_overall=2,
           name='Jane Doe',
           club='Edinburgh',
           finish_time_seconds=1920
       )
   ]

   with RaceResultsDatabase('races.db') as db:
       count = db.add_results(results, edition_id=1)
       print(f"Added {count} results")

Querying Results
~~~~~~~~~~~~~~~~

.. code-block:: python

   with RaceResultsDatabase('races.db') as db:
       # Get all results for a race
       results_df = db.get_race_results(
           race_name='Tinto Hill Race',
           race_year=2024
       )

       # Get runner history
       history_df = db.get_runner_history(
           runner_name='John Smith',
           race_name='Tinto Hill Race'
       )

       # List all races
       races_df = db.get_races()
       print(races_df)

Database Schema
---------------

The database consists of three main tables:

**races**
~~~~~~~~~

Stores race definitions:

* ``race_id`` (INTEGER PRIMARY KEY): Unique race identifier
* ``race_name`` (TEXT NOT NULL): Name of the race
* ``race_category`` (TEXT): Category (marathon, fell_race, etc.)
* ``created_at`` (TIMESTAMP): Creation timestamp

**race_editions**
~~~~~~~~~~~~~~~~~

Stores individual race instances:

* ``edition_id`` (INTEGER PRIMARY KEY): Unique edition identifier
* ``race_id`` (INTEGER): Foreign key to races table
* ``race_year`` (INTEGER): Year of the race
* ``race_date`` (TEXT): Date of the race (ISO format)
* ``source_url`` (TEXT): URL where results were obtained
* ``source_file`` (TEXT): File where results were obtained
* ``metadata`` (TEXT): JSON metadata
* ``created_at`` (TIMESTAMP): Creation timestamp

**results**
~~~~~~~~~~~

Stores race results:

* ``result_id`` (INTEGER PRIMARY KEY): Unique result identifier
* ``edition_id`` (INTEGER): Foreign key to race_editions
* ``position_overall`` (INTEGER): Overall position
* ``name`` (TEXT): Runner name (indexed)
* ``club`` (TEXT): Club name (indexed)
* ``gender`` (TEXT): Gender
* ``age_category`` (TEXT): Age category
* ``finish_time_seconds`` (REAL): Finish time in seconds
* ``finish_time_minutes`` (REAL): Finish time in minutes
* ``race_status`` (TEXT): FINISHED, DNF, DNS, DSQ
* Plus additional fields for bib numbers, positions, times, etc.

Indexes are created on frequently queried fields (name, club, race_year) for performance.

See Also
--------

* :doc:`models` - Data models
* :doc:`manager` - High-level manager interface
* :doc:`importers` - Data import utilities
