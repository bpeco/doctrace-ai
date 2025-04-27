# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
## 2025-04-27
* `changelog_entry_generator.py`: Changed generate_changelog_entry function to process unified diff and produce a Keep-a-Changelog formatted entry.

## [Unreleased] - 2025-04-27
- Added `GITHUB_REPO` variable to store the repository identifier in the format "owner/repo" from environment variable.
- Updated `verify_github_signature` function to include a description in its docstring.
- Modified `webhook_receiver` to handle ping events and only handle push events.
- Added check to only process pushes to the main branch.
- Renamed some variables for clarity and renamed a function description to better match its functionality.

