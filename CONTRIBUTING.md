# Contributing to GCP Agents - Summoner

Thanks for your interest in contributing! This document explains how to get
started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/TirtheshJani/GCP-Agents---Summoner.git
cd GCP-Agents---Summoner

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=agents --cov=tools --cov=config -v
```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting.

```bash
ruff check .          # lint
ruff format .         # format
```

## Adding a New Agent

1. Create a file under `agents/specialized_agents/`.
2. Subclass `BaseAgent` and implement `name`, `plan`, and `execute`.
3. Optionally override `reflect` for self-critique behaviour.
4. Export the class from `agents/specialized_agents/__init__.py`.
5. Add a CLI command in `main.py` if the agent should be user-facing.
6. Write tests under `tests/`.

## Pull Requests

- Keep PRs focused on a single change.
- Include tests for new functionality.
- Update documentation if the public API changes.
- Ensure `ruff check .` and `pytest` pass before submitting.
