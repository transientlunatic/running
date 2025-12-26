models - Data Models and Normalization
========================================

.. automodule:: running_results.models
   :members:
   :undoc-members:
   :show-inheritance:

Core Classes
------------

NormalizedRaceResult
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: running_results.models.NormalizedRaceResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

ColumnMapping
~~~~~~~~~~~~~

.. autoclass:: running_results.models.ColumnMapping
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

RaceResultsNormalizer
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: running_results.models.RaceResultsNormalizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Enumerations
------------

RaceCategory
~~~~~~~~~~~~

.. autoclass:: running_results.models.RaceCategory
   :members:
   :undoc-members:
   :show-inheritance:

Gender
~~~~~~

.. autoclass:: running_results.models.Gender
   :members:
   :undoc-members:
   :show-inheritance:

RaceStatus
~~~~~~~~~~

.. autoclass:: running_results.models.RaceStatus
   :members:
   :undoc-members:
   :show-inheritance:

Helper Functions
----------------

Time Parsing
~~~~~~~~~~~~

.. autofunction:: running_results.models.fix_malformed_time

Club Normalization
~~~~~~~~~~~~~~~~~~

.. autofunction:: running_results.models.normalize_club_name

Age Category Parsing
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: running_results.models.parse_age_category

TimeParser
~~~~~~~~~~

.. autoclass:: running_results.models.TimeParser
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Basic Normalization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.models import (
       NormalizedRaceResult,
       ColumnMapping,
       RaceResultsNormalizer
   )
   import pandas as pd

   # Create a sample DataFrame
   data = {
       'Pos': [1, 2, 3],
       'Name': ['John Smith', 'Jane Doe', 'Bob Wilson'],
       'Club': ['Edinburgh AC', 'Carnethy HRC', 'Unattached'],
       'Time': ['31:45', '32:10', 'DNF'],
       'Cat': ['V', 'FV', 'SV']
   }
   df = pd.DataFrame(data)

   # Define column mapping
   mapping = ColumnMapping(
       position_overall='Pos',
       name='Name',
       club='Club',
       finish_time='Time',
       age_category='Cat'
   )

   # Normalize
   normalizer = RaceResultsNormalizer(mapping)
   result_df = normalizer.normalize(df)

   print(result_df[['name', 'club', 'finish_time_minutes', 'age_category', 'race_status']])

Creating Individual Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.models import NormalizedRaceResult, RaceStatus

   # Create a result object
   result = NormalizedRaceResult(
       position_overall=1,
       name='Alice Johnson',
       club='Highland Hill Runners',
       finish_time_seconds=1905,
       age_category='M40',
       gender='M',
       race_status=RaceStatus.FINISHED
   )

   # Access computed fields
   print(f"Finish time: {result.finish_time_minutes:.2f} minutes")

Handling Special Cases
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.models import fix_malformed_time, normalize_club_name

   # Fix time formats
   assert fix_malformed_time('42::51') == '42:51'
   assert fix_malformed_time(':40:56') == '40:56'

   # Normalize club names
   assert normalize_club_name('Carnethy HRC') == 'Carnethy'
   assert normalize_club_name('Edinburgh AC') == 'Edinburgh'
   assert normalize_club_name('U/A') == 'Unattached'

See Also
--------

* :doc:`database` - Database storage
* :doc:`importers` - Data import utilities
* :doc:`manager` - Unified manager interface
