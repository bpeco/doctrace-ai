# Doctrace-AI 🧠

Doctrace-AI is an AI-powered tool that generates changelog entries and Python docstrings automatically based on Git commit diffs. It listens for GitHub webhooks and updates your repository with the generated documentation.

## 🚀 Features

- Listens to GitHub webhooks for specific branches (e.g. `auto/docs-*`)
- Parses commit diffs automatically
- Generates:
  - **Changelog entries** (Keep-a-Changelog format)
  - **Google-style Python docstrings**
- Applies diffs locally and commits the new documentation

## 🛠️ Tech Stack

- **Python 3.12**
- **FastAPI** – Webhook receiver & API layer
- **GitPython** – Git diff processing
- **OpenAI API** – Language model to generate changelogs and docstrings
- **Poetry** – Dependency management
- **Docker** (optional)
