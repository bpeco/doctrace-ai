# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## 2023-10-05

- `webhook.py`: extended ignored prefixes to include “chore: update changelog and docs for” alongside the existing “chore: generate changelog entry for [Unreleased]”

## [Released]

## 2025-04-27
* `app/agents/changelog.py`: Added function `generate_changelog_entry` to generate changelog entries.
* `main.py`: Refactored code to improve readability and maintainability, added `verify_signature` function to verify GitHub HMAC signature, added `extract_diff` function to extract changed files and unified diff, added `update_changelog` function to generate changelog entry and append under ## [Unreleased], added `apply_doc_patches` function to generate docstring patches and apply them, and added `create_branch_and_pr` function to commit given files, push branch and open a PR.

## 2025-04-27
- Added `GITHUB_REPO` variable to store the repository identifier in the format "owner/repo" from environment variable.
- Updated `verify_github_signature` function to include a description in its docstring.
- Modified `webhook_receiver` to handle ping events and only handle push events.
- Added check to only process pushes to the main branch.
- Renamed some variables for clarity and renamed a function description to better match its functionality.