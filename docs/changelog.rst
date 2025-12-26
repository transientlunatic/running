Changelog
=========

Version 0.1.0 (2025-12-26)
--------------------------

Initial release of running-results package.

**Features:**

* Data normalization with Pydantic validation
* Support for 23+ race result fields
* Automatic time parsing (HH:MM:SS, MM:SS, seconds)
* Club name standardization
* Age category parsing (V/SV/SSV/FV conventions)
* DNF/DNS/DSQ status handling
* SQLite database storage
* Web scraping from HTML tables
* File import (CSV, TSV, Excel, HTML)
* Auto-detection of file formats and columns
* Unified manager interface
* Runner history tracking
* Club and category analysis

**Documentation:**

* Comprehensive API reference
* Normalization guide
* Database guide
* Quick start guide
* Multiple examples

**Testing:**

* Validated with 2,553 Tinto Hill Race results (1985-2003)
* Tested with Edinburgh Marathon 2024 results
* Multiple data format compatibility verified
