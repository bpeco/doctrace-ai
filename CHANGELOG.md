# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
## 2024-06-20
- `.DS_Store`: updated binary file  
- `app/main.py`: updated `generate_changelog_entry` docstring to include step for date heading  
- `app/main.py`: extended `extract_diff` to accept an optional `base_branch` and fetch/compare against it  
- `app/main.py`: enhanced `webhook_receiver` to process only push events, verify signatures, parse JSON payloads, restrict to heads, route feature/* and fix/* branches against `main`, and pass `base_branch` into `extract_diff`

2025-04-27
* `app/agents/docs_generator.py`: Updated function `generate_docstrings` to parse JSON response, validate its format, change the role and content of chat completion messages, and return a single JSON object with all patches.
* `main.py`: Updated function `verify_github_signature` to include a description in its docstring and added `GITHUB_REPO` variable to store the repository identifier.

2024-09-16
* `app/agents/changelog.py`: Added function `generate_changelog_entry` to generate changelog entries.
* `app/agents/docs_generator.py`: Added function `generate_docstrings` to generate docstrings for modified functions.
* `main.py`: Refactored code to improve readability and maintainability, added `verify_signature` function to verify GitHub HMAC signature, added `extract_diff` function to extract changed files and unified diff, added `update_changelog` function to generate changelog entry and append under ## [Unreleased], added `apply_doc_patches` function to generate docstring patches and apply them, and added `create_branch_and_pr` function to commit given files, push branch and open a PR.

## [Unreleased] - 2025-04-27
- Added `GITHUB_REPO` variable to store the repository identifier in the format "owner/repo" from environment variable.
- Updated `verify_github_signature` function to include a description in its docstring.
- Modified `webhook_receiver` to handle ping events and only handle push events.
- Added check to only process pushes to the main branch.
- Renamed some variables for clarity and renamed a function description to better match its functionality.

