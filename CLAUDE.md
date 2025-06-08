# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses a DevContainer setup with Python 3.13 and modern Python tooling. The environment is pre-configured with all necessary dependencies.

## Common Commands

### Running Code
- `run` or `uv run python main.py` - Run the main Python script

### Testing
- `test` or `uv run --frozen pytest` - Run all tests
- `uv run pytest tests/test_specific.py` - Run a specific test file
- `uv run pytest -k "test_name"` - Run tests matching a pattern

### Code Quality
- `lint` or `uv run ruff check` - Check code style and common errors
- `format` or `uv run ruff format` - Auto-format code
- `typecheck` or `uv run pyright` - Run type checking

### Package Management
- `uv sync` - Install dependencies from pyproject.toml
- `uv add <package>` - Add a new dependency
- `uv remove <package>` - Remove a dependency

## Project Structure

This is a Python project template configured for development with Strands Agent and Claude Code. The project uses:
- **uv** for Python package management
- **ruff** for linting and formatting (replaces black, isort, flake8)
- **pyright** for static type checking
- **pytest** for testing

## Development Notes

- The DevContainer automatically runs `uv sync` on creation to install dependencies
- Git diffs are enhanced with delta for better readability
- Command history persists across container restarts in `.devcontainer/.persistent_history`