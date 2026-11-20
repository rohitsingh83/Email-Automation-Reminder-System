# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-20

### Added
- Standard `pyproject.toml` with PEP 621 packaging metadata and bounded dependencies.
- Centralized `Settings` configuration dataclass in `src/config.py`.
- Architecture Decisions Record (`DECISIONS.md`).
- GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- Flexible timestamp parsing supporting standard and ISO 8601 strings.
- Safety cap (`max_occurrences=100`) preventing infinite recurrence loops.
- Streamlit dry-run test dispatcher.

### Changed
- Replaced sequential database insert queries with batch `executemany` operations.
- Upgraded logging to structured logging.
