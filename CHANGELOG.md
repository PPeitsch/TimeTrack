# Changelog for TimeTrack

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.5.0] - 2025-12-15

### Added
- **Comprehensive Test Coverage:** Increased test coverage from 75% to 98% (Issue #29).
  - Added `test_init_db.py`: 15 tests for environment parsing and database info extraction.
  - Added `test_init_data.py`: 8 tests for data seeding functions.
  - Added `test_import_log.py`: 18 tests for import routes.
  - Added `test_pdf_importer.py`: 19 tests for PDF parsing.
  - Expanded Excel importer tests with 15 edge cases.
  - Expanded route tests with 7 time summary edge cases.
- Added `.coveragerc` configuration to exclude interactive scripts from coverage.
- Integrated Codecov test results action for improved CI reporting.
- Dynamic Codecov coverage badge in README.

### Changed
- Improved CI workflow with `junitxml` output for better test reporting.


## [1.4.0] - 2025-12-14

### Added
- **File Import System**: Implemented automatic time data import from PDF and Excel files (Issue #78).
  - New `/import` route for uploading and parsing time reports.
  - Added `PDFImporter` using `pdfplumber` and `ExcelImporter` using `pandas`.
  - Factory pattern for selecting appropriate importer based on file type.
  - Preview page to validate parsed data before import.
- Added `observation` column to `ScheduleEntry` model.
- Added Flask-Migrate support for database migrations.


## [1.3.2] - 2025-12-12

### Added
- Added `AGENTS.md` and `WORKFLOW.md` to provide guidelines and workflows for AI agents.


## [1.3.1] - 2025-08-23

### Changed
- Updated the `README.md` file to accurately reflect the current state of the application. The update includes a revised feature list, a corrected project structure diagram, and improved quick start and usage instructions.


## [1.3.0] - 2025-08-23

### Changed
- **Standardized Default Absence Codes:** Replaced the initial Spanish absence codes (e.g., "LICENCIA MÉDICA") with a set of universal, English-language defaults (e.g., "Sick Leave", "Vacation"). This provides a more consistent out-of-the-box experience for new users.
- Refactored the data initialization script (`init_data.py`) by extracting the default codes into a constant, improving readability and maintainability.

### Removed
- Removed the unused `ABSENCE_CODES` list from the `config.py` file. This eliminates redundancy and establishes the database as the single source of truth for absence codes.


## [1.2.3] - 2025-08-22

### Added
- Increased test coverage for the `time_log.py` module from 88% to 100%.


## [1.2.2] - 2025-08-22

### Added
- Increased test coverage for the `manual_entry.py` module from 72% to 98%.


## [1.2.1] - 2025-08-22

### Fixed
- Corrected and updated the release comparison links in `CHANGELOG.md`.


## [1.2.0] - 2025-08-07

### Added
- **CRUD Management for Absence Codes:**
  - Implemented a new "Settings" page at `/settings/absences` for full CRUD (Create, Read, Update, Delete) management of absence codes.
  - Created a set of RESTful API endpoints under `/settings/api/absence-codes` to support the new management interface.
  - Added a comprehensive test suite (`tests/test_settings.py`) with 100% code coverage for the new backend routes and logic.

### Changed
- The "Manual Entry" dropdown is now dynamically populated with the user-managed absence codes from the database, replacing the previous hardcoded list.
- The "Calendar Log" view now fetches absence codes from the new centralized API endpoint, ensuring consistency across the application.

### Fixed
- Prevented the deletion of absence codes that are currently in use in any `ScheduleEntry`, ensuring data integrity.


## [1.1.1] - 2025-08-07

### Changed
- **Calendar Interaction Logic:**
  - Users can now select and modify weekends and holidays in the "Monthly Log" calendar to log work hours on non-standard workdays.
  - The day editing modal now includes a "(Revert to Default)" option, allowing users to remove an override and restore a day to its original state (e.g., Holiday or Weekend).
  - The backend API was updated to handle explicit "Work Day" overrides and the new "Revert to Default" action, ensuring predictable and intuitive behavior.


## [1.1.0] - 2025-08-07

### Fixed
- Resolved a CSS bug in the "Monthly Log" calendar where day types with multiple words (e.g., "LICENCIA MÉDICA") were unreadable due to poor color contrast.


## [1.0.9] - 2025-08-07

### Fixed
- Resolved a bug in the "Monthly Log" calendar where the "Edit Day Type" modal was not being populated with absence codes. This was caused by an error in the database initialization script that failed to seed the `absence_codes` table.
- Corrected an asynchronous flow issue in the frontend JavaScript to ensure the modal's dropdown is populated only after the absence codes have been successfully fetched from the API.


## [1.0.8] - 2025-08-07

### Fixed
- The automatic release workflow no longer adds a redundant "TimeTrack" prefix to the GitHub release title, which now consists only of the version tag.


## [1.0.7] - 2025-08-06

### Added
- **Monthly Calendar View:** Implemented a new primary interface at `/monthly-log` for managing daily log types. It displays a full month calendar with color-coded day types (Work Day, Weekend, Holiday, Absences).
- **Interactive Day Type Management:** Users can now click on a single day or click-and-drag to select multiple days to open an editing modal.
- **Bulk Updates:** The new modal allows changing the type for single or multiple days at once (e.g., assigning a week of vacation).
- New API endpoints (`/api/monthly-log/<year>/<month>` and `/api/update-days`) to support the new calendar view's data fetching and update operations.
- New API endpoint (`/api/absence-codes`) to dynamically populate the editing modal.

### Changed
- The primary navigation now includes a "Calendar Log" link to the new view, making it a central feature of the application.


## [1.0.6] - 2025-08-06

### Changed
- Refactored the holiday import system into a modular, provider-based architecture, decoupling the application from a single data source.
- The application now uses a `HOLIDAY_PROVIDER` setting in the configuration for future extensibility.
- Improved the database initialization script (`init_db.py`) with better user experience and more robust error handling.

### Added
- A `HolidayProvider` interface and a concrete `ArgentinaWebsiteProvider` implementation.
- A factory service (`get_holiday_provider`) to instantiate the correct provider based on configuration.
- A comprehensive suite of unit tests (`tests/test_services.py`) for the new holiday provider services, achieving 100% code coverage on the new modules.

### Fixed
- The holiday scraper, which was failing silently, is now fixed. It correctly parses data from an embedded JSON object on the source website, making it significantly more reliable.
- Corrected a recurring dependency check error for `beautifulsoup4` in the init script.
- Resolved multiple `mypy` type-checking errors that appeared in CI/CD environments.


## [1.0.5] - 2025-07-31

### Added
- Created a dedicated GitHub issue template (`docs.yaml`) for documentation-related reports to standardize submissions and improve clarity.


## [1.0.4] - 2025-07-31

### Fixed
- Corrected a UI bug in the "Manual Entry" form where time input fields remained visible for non-work day types (e.g., absences), causing user confusion. The fields are now dynamically shown or hidden based on the selected entry type.


## [1.0.3] - 2025-07-31

### Added
- Implemented a GitHub Actions workflow to automate the creation of releases.
- Added a Python script (`scripts/extract_release_notes.py`) to parse release notes for a specific version from `CHANGELOG.md`.

### Changed
- The new release workflow automatically populates the body of a GitHub Release using the content from the changelog when a new version tag (e.g., `v1.0.3`) is pushed.


## [1.0.2] - 2025-07-31

### Fixed
- Corrected off-by-one date display error in the daily summary view caused by timezone misinterpretation in the frontend.
- Fixed a bug where holidays were not being recognized or displayed in the time summary, leading to incorrect required hours calculations.
- Centralized day type logic (Work Day, Weekend, Holiday, Absence) in the backend to ensure data consistency.


## [1.0.1] - 2025-07-23

### Fixed
- Resolved WSGI server deployment issue caused by entry-point name conflict (`run.py`).
- Updated project documentation (`README.md`) to reflect the new entry-point file.
- Adjusted environment configuration (`.env.example`) to use the new `run.py` script.


## [1.0.0] - 2025-03-16

### Added
- Manual time entry with multiple entries per day.
- Time summary with monthly statistics.
- Absence management.
- Argentina holidays integration.
- Flexible database configuration (SQLite/PostgreSQL).



[1.5.0]: https://github.com/PPeitsch/TimeTrack/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/PPeitsch/TimeTrack/compare/v1.3.2...v1.4.0
[1.3.2]: https://github.com/PPeitsch/TimeTrack/compare/v1.3.1...v1.3.2

[1.3.1]: https://github.com/PPeitsch/TimeTrack/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.3...v1.3.0
[1.2.3]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/PPeitsch/TimeTrack/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/PPeitsch/TimeTrack/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.9...v1.1.0
[1.0.9]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/PPeitsch/TimeTrack/releases/tag/v1.0.0
