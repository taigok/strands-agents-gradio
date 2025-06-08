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
- **Always use uv**: Never use pip directly
- **Frozen dependencies**: Use `uv run --frozen` for reproducible builds
- **Lock file**: Always commit `uv.lock` changes

#### Basic Commands
- `uv sync` - Install dependencies from pyproject.toml
- `uv add <package>` - Add a new dependency
- `uv add --dev <package>` - Add development dependencies
- `uv add "package>=1.0.0,<2.0.0"` - Add with version constraints
- `uv remove <package>` - Remove a dependency
- `uv sync --upgrade` - Update all dependencies

#### Dependency Files
- **pyproject.toml**: Defines project requirements with flexible version ranges
- **uv.lock**: Records exact versions and hashes for reproducible builds
- Both files should be committed to version control

## Project Structure

This is a Python project template configured for development with Strands Agent and Claude Code. The project uses:
- **uv** for Python package management
- **ruff** for linting and formatting (replaces black, isort, flake8)
- **pyright** for static type checking
- **pytest** for testing

## Development Standards

### Code Quality Requirements
- **Type hints**: All functions and methods must have complete type annotations
- **Docstrings**: All public functions, classes, and methods require docstrings
- **Line length**: Maximum 88 characters per line
- **Function size**: Keep functions focused and small (prefer < 20 lines)

### Testing Strategy
- **Test coverage**: All new features and bug fixes require tests
- **Edge cases**: Test error conditions and edge cases
- **Test command**: `uv run --frozen pytest`

### Code Quality Tools
- **Formatter**: Ruff (`uv run ruff format`)
- **Linter**: Ruff (`uv run ruff check`)
- **Type checker**: Pyright (`uv run pyright`)
- **Error resolution order**: Format → Type errors → Linting issues

### Development Workflow
1. Write code with type hints and docstrings
2. Format code: `uv run ruff format`
3. Fix type errors: `uv run pyright`
4. Fix linting issues: `uv run ruff check --fix`
5. Run tests: `uv run --frozen pytest`
6. Commit changes (ask permission first)

## Development Notes

- The DevContainer automatically runs `uv sync` on creation to install dependencies
- Git diffs are enhanced with delta for better readability
- Command history persists across container restarts in `.devcontainer/.persistent_history`
- **Always ask before committing**: When tasks are completed, Claude Code should ask for permission before creating git commits
