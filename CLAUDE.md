# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses a DevContainer setup with Python 3.13 and modern Python tooling. The environment is pre-configured with all necessary dependencies.

## Common Commands

### Running Code
- `run` or `uv run python main.py` - Run the Strands Agents + Gradio chat application (port 7862)
- `gradio main.py` - Run with hot reload enabled (開発時推奨)

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

This is a Strands Agents + Gradio + MCP integration chat application. The project provides:
- **Single-file application**: `main.py` contains the complete chat interface
- **Strands Agents SDK**: Integration with AWS Bedrock Claude models
- **MCP Protocol**: Direct integration with AWS Documentation MCP Server
- **Real-time debugging**: Callback handlers display agent internal processing
- **Streaming interface**: Gradio ChatInterface with real-time status updates

### Architecture
- **Main Application**: `main.py` - Streamlined chat app with debug logging
- **Model Integration**: Direct AWS Bedrock Claude 3 Haiku usage
- **MCP Server**: External `awslabs.aws-documentation-mcp-server@latest` via uvx
- **UI Framework**: Gradio for web-based chat interface

### Environment Setup
Required environment variables in `.env`:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - AWS Bedrock credentials
- `AWS_DEFAULT_REGION` - AWS region (default: ap-northeast-1)

### Key Components
- **Callback Handlers**: Real-time debugging shows agent internal processing (🤔 thinking, 🔧 tool usage, ✍️ response generation)
- **Threading Model**: Agent processing runs in separate thread to enable streaming status updates
- **MCP Integration**: Direct connection to AWS Documentation server via MCPClient
- **Status Logging**: Both console logging and Gradio streaming display of agent activities

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

### Hot Reload (ホットリロード)
開発時は `gradio main.py` コマンドを使用することで、ファイル変更時の自動リロードが有効になります：
- ファイルを編集すると自動的にアプリが再読み込みされます
- モデルやMCPクライアントは `gr.NO_RELOAD` ブロック内にあるため、再読み込みされません
- UIの変更をすぐに確認できるため、開発効率が向上します
