# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
## [Unreleased] - 2025-04-27
- Added `generate_changelog_entry` function to create a changelog entry based on a unified diff.
- Modified the `webhook_receiver` function to generate a changelog entry, append it to `CHANGELOG.md`, commit and push the changes, and open a pull request.
- Added `groq` library and imported `load_dotenv` from `python-dotenv`.
- Updated `webhook_receiver` function to handle ping events and verify GitHub webhook signatures.
- Added `GH_CLIENT` and `GH_REPO` to interact with the GitHub API.
- Updated `get_repo_diff` function call to use `REPO_PATH` and `old_rev` and `new_rev` from the payload.
- Added error handling for missing revisions in the payload and for errors extracting the diff.
- Added `changelog_path` to specify the path to the `CHANGELOG.md` file.
- Updated the `generate_changelog_entry` function call to pass the `diff_text` as an argument.
- Added code to insert the generated changelog entry into the `CHANGELOG.md` file under the `[Unreleased]` section.
- Added code to commit and push the changes to a new branch and open a pull request.

