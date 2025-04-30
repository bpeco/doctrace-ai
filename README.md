# Doctrace-AI 🧠

Doctrace-AI is an AI-powered documentation automation tool that generates changelog entries and Python docstrings directly from Git commit diffs. It is designed to run as a webhook listener that integrates seamlessly with GitHub workflows.

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
