# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Conversation Extractor is a Python CLI tool that extracts Claude Code conversations from the undocumented JSONL format stored in `~/.claude/projects/` and converts them to readable formats (Markdown, HTML, JSON). It has zero external dependencies and uses only Python's standard library.

## Commands

### Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint check
flake8 . --max-line-length=100

# Format check
black . --check
```

### Testing the Tool

```bash
# List all sessions
python src/extract_claude_logs.py --list

# Extract a specific session
python src/extract_claude_logs.py --extract 1

# Run the interactive UI
python src/extract_claude_logs.py
```

### Entry Points (after pip install)

- `claude-start` / `claude-extract` / `claude-logs` - Interactive UI with ASCII art and menus
- `claude-search` - Direct search command

## Architecture

### Source Files (`src/`)

| File | Purpose |
|------|---------|
| `extract_claude_logs.py` | Main entry point. Contains `ClaudeConversationExtractor` class that handles JSONL parsing, message extraction, plan/Q&A detection, and output formatting. Also contains CLI argument parsing and `launch_interactive()` entry point. |
| `interactive_ui.py` | ASCII art logo, menu-driven interactive interface |
| `search_conversations.py` | Search engine with fuzzy matching, regex, date filtering |
| `realtime_search.py` | Real-time search UI with instant results as you type |
| `search_cli.py` | Entry point for `claude-search` command |

### Key Classes

**`ClaudeConversationExtractor`** (in `extract_claude_logs.py`):
- `find_sessions()` - Locates JSONL files in `~/.claude/projects/`
- `find_projects()` - Lists project directories
- `extract_conversation()` - Parses JSONL and extracts messages, plans, Q&A pairs
- `extract_bash_commands()` - Extracts only successful bash commands
- `save_as_markdown/html/json()` - Output formatters

### Data Flow

1. Claude Code stores conversations as JSONL in `~/.claude/projects/{encoded-path}/*.jsonl`
2. Each JSONL line is a JSON object with `type` (user/assistant/tool_use/tool_result/system/summary)
3. Extractor reads each line, detects message types, extracts text content
4. Special content detection: plans (`📋`) via text pattern or `ExitPlanMode` tool, Q&A pairs via `AskUserQuestion` tool
5. Output formatted to Markdown/HTML/JSON with appropriate styling

### JSONL Entry Types

- `user` - User messages (content can be string or array with text/image)
- `assistant` - Claude responses (content array with text and tool_use items)
- `tool_use` - Tool invocations (Bash, Write, Read, etc.)
- `tool_result` - Output from tools
- `system` - System notifications
- `summary` - Session summaries

## Testing

Tests are in `tests/` directory. Key test files:
- `test_extractor.py` - Core extraction functionality
- `test_extract_comprehensive.py` - Comprehensive coverage tests
- `test_search*.py` - Search functionality tests
- `test_interactive_ui.py` - UI tests

Use `conftest.py` fixtures for sample conversation data.

## Code Style

- PEP 8 with 100-character line limit
- Use `black` for formatting
- Type hints where helpful
- Conventional commits: `feat:`, `fix:`, `docs:`, `perf:`
