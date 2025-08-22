# Changelog for TimeTrack

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Your new feature here.

### Fixed
- Your new fix here.


## [1.2.2] - 2025-08-22

### Added
- Increased test coverage for the `manual_entry.py` module from 72% to 98%.


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


[Unreleased]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/PPeitsch/TimeTrack/compare/v1.2.0...v1.2.2
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
