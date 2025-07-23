# Changelog for TimeTrack

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Your new feature here.

### Fixed
- Your new fix here.


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

[Unreleased]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/PPeitsch/TimeTrack/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/PPeitsch/TimeTrack/releases/tag/v1.0.0
