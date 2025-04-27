# doctrace-ai

Microservice powered by AI-Agent for automatic generation of Google-style docstrings and a Keep-a-Changelog-compliant CHANGELOG from GitHub push events.

## Features

- **Docstring Updater**: Detects modified Python functions and classes, regenerates their docstrings.
- **Changelog Generator**: Appends a human-readable changelog entry on every push.
- **Auto-PR**: Creates a branch `auto/docs-<hash>`, commits docs + changelog, and opens a pull request.

## Tech Stack

- **Web Framework**: FastAPI  
- **AI**: Llama AI via LangChain Agents  
- **Git Integration**: GitPython & PyGithub  
- **Containerization**: Docker
- 
## Getting Started

1. Clone the repo:  
   ```bash
   git clone https://github.com/<your-username>/doctrace-ai.git
   cd doctrace-ai

_Test commit for diff extraction_
_And here is Test Number 2_