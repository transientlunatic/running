Contributing
============

We welcome contributions to the running-results package!

How to Contribute
-----------------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a branch** for your changes
4. **Make your changes** and add tests
5. **Run tests** to ensure everything works
6. **Submit a pull request**

Development Setup
-----------------

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/transientlunatic/running.git
   cd running

   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

   # Install in development mode
   pip install -e ".[dev]"

Running Tests
-------------

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=running_results

   # Run specific test file
   pytest tests/test_models.py

Code Style
----------

We use:

* **Black** for code formatting
* **Flake8** for linting
* **Type hints** where appropriate

.. code-block:: bash

   # Format code
   black running_results/

   # Check linting
   flake8 running_results/

Documentation
-------------

Documentation is built with Sphinx. To build locally:

.. code-block:: bash

   cd docs
   make html

The documentation will be in ``docs/_build/html/``.

Reporting Bugs
--------------

Please report bugs via GitHub Issues. Include:

* Python version
* Package version
* Minimal code to reproduce
* Expected vs actual behavior
* Error messages/tracebacks

Feature Requests
----------------

Feature requests are welcome! Please describe:

* The problem you're trying to solve
* Your proposed solution
* Any alternative solutions considered

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.
