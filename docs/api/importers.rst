importers - Data Import Utilities
==================================

.. automodule:: running_results.importers
   :members:
   :undoc-members:
   :show-inheritance:

Main Classes
------------

ResultsImporter
~~~~~~~~~~~~~~~

.. autoclass:: running_results.importers.ResultsImporter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

SmartImporter
~~~~~~~~~~~~~

.. autoclass:: running_results.importers.SmartImporter
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Examples
--------

Importing from URLs
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import ResultsImporter

   # Import from a webpage with HTML table
   importer = ResultsImporter()
   df = importer.from_url('https://example.com/results.html')

   # Specify CSS selector for the table
   df = importer.from_url(
       'https://example.com/results.html',
       table_selector='table.results'
   )

   # Import the second table on the page
   df = importer.from_url(
       'https://example.com/results.html',
       table_index=1
   )

Importing from Files
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import ResultsImporter

   importer = ResultsImporter()

   # Auto-detect file format
   df = importer.from_file('results.csv')
   df = importer.from_file('results.tsv')
   df = importer.from_file('results.xlsx')
   df = importer.from_file('results.html')

Importing from Text
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import ResultsImporter

   importer = ResultsImporter()

   # Auto-detect delimiter
   text_data = \"\"\"
   Pos,Name,Club,Time
   1,John Smith,Edinburgh AC,31:45
   2,Jane Doe,Carnethy HRC,32:10
   \"\"\"
   df = importer.from_text(text_data)

   # Specify delimiter
   tab_data = "Pos\\tName\\tClub\\tTime\\n1\\tJohn Smith\\tEdinburgh AC\\t31:45"
   df = importer.from_text(tab_data, delimiter='\\t')

Smart Import with Normalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import SmartImporter
   from running_results.models import ColumnMapping

   importer = SmartImporter()

   # Import and normalize in one step
   df = importer.import_and_normalize(
       source='results.csv',
       column_mapping=ColumnMapping(
           position_overall='Pos',
           name='Name',
           finish_time='Time'
       )
   )

   # Auto-detect columns
   df = importer.import_and_normalize(source='results.csv')

Advanced Usage
--------------

Custom Headers
~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import ResultsImporter

   # Use custom headers for HTTP requests
   importer = ResultsImporter()
   importer.session.headers.update({
       'User-Agent': 'MyBot/1.0'
   })
   df = importer.from_url('https://example.com/results.html')

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from running_results.importers import ResultsImporter

   importer = ResultsImporter()

   try:
       df = importer.from_url('https://example.com/results.html')
   except ValueError as e:
       print(f"Import failed: {e}")

Supported Formats
-----------------

**Web Sources:**

* HTML pages with ``<table>`` elements
* CSS selector support for targeting specific tables
* Automatic table detection

**File Formats:**

* CSV (Comma-separated values)
* TSV (Tab-separated values)
* Excel (.xlsx, .xls)
* HTML files with tables

**Text Data:**

* Delimited text with automatic delimiter detection
* Comma, tab, pipe, and semicolon delimiters supported
* Custom delimiter specification

See Also
--------

* :doc:`models` - Data normalization
* :doc:`manager` - High-level interface
* :doc:`database` - Database storage
