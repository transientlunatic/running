Quick Start
===========

This guide will get you started with the running-results package in just a few minutes.

Basic Normalization
-------------------

The simplest way to normalize race results:

.. code-block:: python

   from running_results import RaceResultsNormalizer, ColumnMapping
   import pandas as pd

   # Load your data
   df = pd.read_csv('my_race_results.csv')

   # Define how your columns map to standard fields
   mapping = ColumnMapping(
       position_overall='Position',
       name='Runner Name',
       club='Club',
       finish_time='Finish Time',
       gender='Gender',
       age_category='Category'
   )

   # Create normalizer and process
   normalizer = RaceResultsNormalizer(mapping)
   normalized_df = normalizer.normalize(df)

   # Save normalized results
   normalized_df.to_csv('normalized_results.csv', index=False)

The normalizer will:

* Parse times into seconds and minutes
* Extract gender from age categories
* Normalize club names
* Handle DNF/DNS/DSQ statuses
* Fix common data errors

Using the Database
------------------

For persistent storage and tracking across years:

.. code-block:: python

   from running_results import RaceResultsManager

   # Initialize with a database file
   manager = RaceResultsManager('my_races.db')

   # Import from a file
   manager.add_from_file(
       'tinto_2024.csv',
       race_name='Tinto Hill Race',
       race_year=2024,
       race_category='fell_race',
       column_mapping={'Position': 'position_overall', 'Time': 'finish_time'}
   )

   # Import from a URL
   manager.add_from_url(
       'https://example.com/results.html',
       race_name='Edinburgh Marathon',
       race_year=2024,
       race_category='marathon'
   )

Querying Results
----------------

Once data is in the database, you can query it easily:

.. code-block:: python

   # Get all results for a specific race and year
   results_2024 = manager.get_race('Tinto Hill Race', race_year=2024)

   # Get a runner's complete history
   runner_history = manager.get_runner_history('Jane Smith')

   # Search by club
   carnethy_runners = manager.search_results(club='Carnethy')

   # Search by age category
   veterans = manager.search_results(age_category='M40')

   # List all races in database
   all_races = manager.list_races()
   print(all_races)

Working with Normalized Data
-----------------------------

The normalized DataFrame has standardized columns:

.. code-block:: python

   # Access common fields
   print(normalized_df['name'])
   print(normalized_df['finish_time_minutes'])
   print(normalized_df['club'])
   print(normalized_df['age_category'])

   # Filter by finish status
   finishers = normalized_df[normalized_df['race_status'] == 'FINISHED']
   dnf = normalized_df[normalized_df['race_status'] == 'DNF']

   # Analyze by club
   club_counts = normalized_df['club'].value_counts()

   # Get fastest times
   fastest = normalized_df.nsmallest(10, 'finish_time_seconds')

Automatic Column Detection
---------------------------

If you don't provide a mapping, the importer will try to auto-detect:

.. code-block:: python

   # Let the system figure out the columns
   manager.add_from_file(
       'results.csv',
       race_name='Local 5K',
       race_year=2024,
       race_category='road_race'
   )

The system recognizes common column names like:

* Position: 'Pos', 'Position', 'Place', 'Rank'
* Name: 'Name', 'Runner', 'Athlete'
* Time: 'Time', 'Finish Time', 'Gun Time', 'Chip Time'
* Club: 'Club', 'Team', 'Affiliation'

Handling Special Cases
-----------------------

**DNF/DNS/DSQ Results:**

The system automatically detects non-finish statuses:

.. code-block:: python

   # These are recognized automatically
   # "DNF" in time field → race_status='DNF'
   # "DNS" in time field → race_status='DNS'
   # "DSQ" or "DQ" → race_status='DSQ'

**Malformed Times:**

Common time format errors are auto-corrected:

.. code-block:: python

   # "42::51" → "42:51"
   # ":40:56" → "40:56"
   # "1:23:45:67" → "1:23:45"

**Age Categories:**

Various age category formats are normalized:

.. code-block:: python

   # V → M40, FV → F40
   # SV → M50, FSV → F50
   # SSV → M60
   # J → U20

Next Steps
----------

* See :doc:`normalization_guide` for detailed normalization options
* Read :doc:`database_guide` for advanced database features
* Check out :doc:`examples` for more use cases
* Browse the :doc:`api/models` for complete API reference
