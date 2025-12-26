Installation
============

Requirements
------------

* Python 3.7 or higher
* pip package manager

From Source
-----------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/transientlunatic/running.git
   cd running
   pip install -e .

This will install the package along with all required dependencies.

Dependencies
------------

The package automatically installs the following dependencies:

**Core Dependencies:**

* ``pandas>=1.3.0`` - Data manipulation and analysis
* ``numpy>=1.21.0`` - Numerical computing
* ``pydantic>=2.0.0`` - Data validation
* ``typing-extensions>=4.6.0`` - Type hints support

**Import & Scraping:**

* ``beautifulsoup4>=4.9.0`` - HTML parsing
* ``lxml>=4.6.0`` - XML and HTML processing
* ``requests>=2.26.0`` - HTTP library

**Visualization:**

* ``matplotlib>=3.4.0`` - Plotting library

**Utilities:**

* ``nameparser>=1.1.0`` - Name parsing
* ``tqdm>=4.62.0`` - Progress bars

Development Dependencies
------------------------

For development work, install additional tools:

.. code-block:: bash

   pip install -e ".[dev]"

This includes:

* ``pytest>=6.0`` - Testing framework
* ``pytest-cov>=2.0`` - Code coverage
* ``black>=21.0`` - Code formatter
* ``flake8>=3.9`` - Linter

Documentation Dependencies
--------------------------

To build the documentation locally:

.. code-block:: bash

   pip install -e ".[docs]"

This includes:

* ``sphinx>=4.0`` - Documentation generator
* ``sphinx-kentigern>=0.1.0`` - Kentigern theme

Verifying Installation
-----------------------

After installation, verify that the package is correctly installed:

.. code-block:: python

   import running_results
   print(running_results.__version__)

You should see the version number printed without errors.

Next Steps
----------

* Continue to :doc:`quickstart` for a quick introduction
* See :doc:`normalization_guide` for data normalization details
* Check out :doc:`database_guide` for database usage
