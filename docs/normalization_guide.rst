Normalization Guide
===================

This guide provides comprehensive information about normalizing race results data.

Overview
--------

The normalization system transforms race results from various formats into a standardized schema with:

* Consistent field names
* Validated data types
* Corrected time formats
* Standardized club names
* Parsed age categories
* Enumerated race statuses

The NormalizedRaceResult Model
-------------------------------

All normalized results conform to the ``NormalizedRaceResult`` Pydantic model with 23 optional fields:

**Position Fields:**

* ``position_overall``: Overall position in race
* ``position_gender``: Position within gender
* ``position_category``: Position within age category

**Runner Information:**

* ``name``: Runner's full name
* ``bib_number``: Race bib/number
* ``gender``: M (Male), F (Female), or other
* ``age_category``: Age category code (e.g., M40, F35-39, U20)
* ``club``: Club/team affiliation

**Time Fields:**

* ``finish_time_seconds``: Finish time in total seconds
* ``finish_time_minutes``: Finish time in decimal minutes
* ``chip_time_seconds``: Chip time in total seconds
* ``chip_time_minutes``: Chip time in decimal minutes
* ``gun_time_seconds``: Gun time in total seconds
* ``gun_time_minutes``: Gun time in decimal minutes

**Race Information:**

* ``race_status``: FINISHED, DNF, DNS, DSQ, or UNKNOWN

**Additional Fields:**

* Fields for split times, pace, distances, etc.

Column Mapping
--------------

Use ``ColumnMapping`` to map your data's columns to standard fields:

.. code-block:: python

   from running_results.models import ColumnMapping

   mapping = ColumnMapping(
       position_overall='Pos',
       name='Runner Name',
       club='Club/Team',
       finish_time='Finish Time',
       gender='Sex',
       age_category='Category'
   )

The ColumnMapping class accepts these parameters (all optional):

.. code-block:: python

   ColumnMapping(
       # Position fields
       position_overall='Pos',
       position_gender='Gender Pos',
       position_category='Cat Pos',
       
       # Runner info
       name='Name',
       bib_number='Bib',
       gender='Gender',
       age_category='Category',
       club='Club',
       
       # Time fields
       finish_time='Time',
       chip_time='Chip Time',
       gun_time='Gun Time',
       
       # Additional fields
       race_number='Race #',
       # ... and more
   )

Automatic Column Detection
---------------------------

If no mapping is provided, the system attempts to auto-detect columns using common names:

**Position:**
* 'pos', 'position', 'place', 'rank', 'overall', 'overall position'

**Name:**
* 'name', 'runner', 'athlete', 'runner name', 'athlete name'

**Club:**
* 'club', 'team', 'affiliation', 'club/team'

**Time:**
* 'time', 'finish time', 'gun time', 'chip time', 'finish'

**Gender:**
* 'gender', 'sex', 'g', 'm/f'

**Age Category:**
* 'category', 'cat', 'age cat', 'age category', 'age group'

Time Parsing
------------

The system handles multiple time formats:

**Standard Formats:**

.. code-block:: python

   '1:23:45'   # HH:MM:SS → 5025 seconds
   '23:45'     # MM:SS → 1425 seconds
   '1425'      # Total seconds → 1425 seconds

**Malformed Formats (Auto-corrected):**

.. code-block:: python

   '42::51'    # Double colon → '42:51'
   ':40:56'    # Leading colon → '40:56'
   '1:23:45:'  # Trailing colon → '1:23:45'

**Non-finish Indicators:**

.. code-block:: python

   'DNF'       # Did Not Finish
   'DNS'       # Did Not Start
   'DSQ'       # Disqualified
   'DQ'        # Disqualified

These are automatically detected and the ``race_status`` field is set accordingly.

Club Name Normalization
------------------------

Club names are automatically standardized:

.. code-block:: python

   from running_results.models import normalize_club_name

   normalize_club_name('Carnethy HRC')      # → 'Carnethy'
   normalize_club_name('Edinburgh AC')      # → 'Edinburgh'
   normalize_club_name('Highland Harriers') # → 'Highland'
   normalize_club_name('U/A')              # → 'Unattached'
   normalize_club_name('Unattached')       # → 'Unattached'
   normalize_club_name('None')             # → 'Unattached'

Removed suffixes:
* HRC (Hill Running Club)
* AC (Athletic Club)
* AAC (Amateur Athletic Club)
* RC (Running Club)
* Harriers
* Hill Runners
* And many more...

Age Category Parsing
--------------------

Various age category conventions are normalized:

.. code-block:: python

   from running_results.models import parse_age_category

   # Veteran codes (Scottish tradition)
   parse_age_category('V', 'M')    # → 'M40'
   parse_age_category('SV', 'M')   # → 'M50'
   parse_age_category('SSV', 'M')  # → 'M60'
   parse_age_category('FV', 'F')   # → 'F40'
   parse_age_category('FSV', 'F')  # → 'F50'

   # Junior codes
   parse_age_category('J', 'M')    # → 'U20'
   parse_age_category('J', 'F')    # → 'U20'

   # Standard codes (passed through)
   parse_age_category('M40', 'M')  # → 'M40'
   parse_age_category('F35-39', 'F') # → 'F35-39'

The system also extracts gender from age categories:

.. code-block:: python

   'M40'    # Gender: M
   'F35'    # Gender: F
   'FV'     # Gender: F (parsed to F40)

Complete Example
----------------

.. code-block:: python

   from running_results.models import (
       RaceResultsNormalizer,
       ColumnMapping
   )
   import pandas as pd

   # Raw data with various issues
   data = {
       'Pos': [1, 2, 3, 4],
       'Name': ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown'],
       'Club/Team': ['Edinburgh AC', 'Carnethy HRC', 'U/A', 'Highland Harriers'],
       'Time': ['31:45', '32::10', 'DNF', ':40:56'],
       'Cat': ['V', 'FV', 'SV', 'J']
   }
   df = pd.DataFrame(data)

   # Create mapping
   mapping = ColumnMapping(
       position_overall='Pos',
       name='Name',
       club='Club/Team',
       finish_time='Time',
       age_category='Cat'
   )

   # Normalize
   normalizer = RaceResultsNormalizer(mapping)
   result_df = normalizer.normalize(df)

   # Results:
   # - Times parsed: 31:45, 32:10 (corrected), DNF, 40:56 (corrected)
   # - Clubs: Edinburgh, Carnethy, Unattached, Highland
   # - Categories: M40, F40, M50, U20
   # - Genders extracted: M, F, M, (needs manual input for J)
   # - race_status: FINISHED, FINISHED, DNF, FINISHED

See Also
--------

* :doc:`api/models` - Full API reference
* :doc:`database_guide` - Storing normalized results
* :doc:`quickstart` - Quick start guide
