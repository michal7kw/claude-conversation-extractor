# Claude Conversation Extractor - Complete Usage Guide

A comprehensive guide to extracting, searching, and analyzing your Claude Code conversation history.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [Listing and Browsing Sessions](#listing-and-browsing-sessions)
4. [Extracting Conversations](#extracting-conversations)
5. [Output Formats](#output-formats)
6. [Detailed Mode, Thinking, and Metadata](#detailed-mode-thinking-and-metadata)
7. [Subagent Conversations](#subagent-conversations)
8. [Organization Options](#organization-options)
9. [Date Filtering](#date-filtering)
10. [Project Filtering](#project-filtering)
11. [Session ID Lookup](#session-id-lookup)
12. [Search Operations](#search-operations)
13. [Bash Commands Extraction](#bash-commands-extraction)
14. [Tool Operations Extraction](#tool-operations-extraction)
15. [Cross-Platform Usage (Windows, WSL, macOS, Linux)](#cross-platform-usage)
16. [Combined Examples and Recipes](#combined-examples-and-recipes)
17. [Automation and Scripting](#automation-and-scripting)
18. [Quick Reference](#quick-reference)

---

## Quick Start

```bash
# Install
pip install claude-conversation-extractor
# or: pipx install claude-conversation-extractor

# Interactive UI (recommended for first-time users)
claude-start

# List all available sessions
claude-extract --list

# Extract the most recent conversation
claude-extract --extract 1

# Extract all conversations
claude-extract --all
```

After extracting, files are saved to `~/Desktop/Claude logs/` (or `~/Documents/Claude logs/` if Desktop is unavailable). Use `--output` to change the destination.

---

## How It Works

Claude Code stores every conversation as a JSONL file in `~/.claude/projects/`. Each project directory corresponds to a working directory where you've used Claude Code.

```
~/.claude/projects/
  mnt-d-Github-myproject/
    abc12345-6789-...jsonl          <- main conversation
    abc12345-6789-.../
      subagents/
        agent-a1b2c3d4.jsonl        <- subagent conversation
        agent-e5f6g7h8.jsonl        <- another subagent
  home-user-another-project/
    def98765-4321-...jsonl
```

This tool reads those JSONL files and converts them into clean, readable Markdown, HTML, or JSON. It also handles:

- **Subagent conversations** (Task tool invocations that spawn separate agents)
- **Thinking blocks** (Claude's internal reasoning, when using extended thinking models)
- **Tool interactions** (Bash, Read, Write, Edit, Grep, Glob, WebFetch, etc.)
- **Plans and Q&A pairs** (detected automatically from conversation patterns)
- **Session statistics** (token usage, model info, tool counts, duration)

---

## Listing and Browsing Sessions

### List Recent Sessions

```bash
# List all sessions (sorted by most recent)
claude-extract --list

# Limit to 10 most recent
claude-extract --list --limit 10
```

Each listing shows:
- Project directory name
- Session ID (first 8 characters of UUID)
- Last modified date
- Message count and file size
- Preview of the first user message

### List Projects

```bash
# Show all projects where you've used Claude Code
claude-extract --list-projects
```

### Interactive Mode

```bash
# Launch interactive UI with menus
claude-start

# Alternative aliases (all identical)
claude-extract        # with no arguments
claude-logs
claude-extract -i
claude-extract --interactive
```

The interactive UI provides:
- ASCII art banner
- Menu-driven session selection
- Real-time search
- One-click extraction

---

## Extracting Conversations

### By Session Number

Session numbers correspond to the listing order (1 = most recent).

```bash
# Extract the most recent session
claude-extract --extract 1

# Extract session #5
claude-extract --extract 5

# Extract multiple specific sessions
claude-extract --extract 1,3,5

# Extract a range (sessions 1 through 5)
claude-extract --extract 1,2,3,4,5
```

### By Count (Most Recent)

```bash
# Extract 5 most recent sessions
claude-extract --recent 5

# Extract 20 most recent
claude-extract --recent 20
```

### All Sessions

```bash
# Extract every session
claude-extract --all
```

### Custom Output Directory

```bash
# Save to a specific directory
claude-extract --output ~/Documents/claude-logs --extract 1

# Save to current directory
claude-extract --output . --all

# Absolute path
claude-extract --output /home/user/backups/claude --all
```

### Overwrite vs Skip

By default, existing files are skipped. Use `--overwrite` to replace them:

```bash
# Skip existing files (default)
claude-extract --all

# Overwrite existing files
claude-extract --overwrite --all
```

---

## Output Formats

### Markdown (Default)

Clean, readable markdown with emoji headers, timestamps, and formatted code blocks.

```bash
claude-extract --extract 1
claude-extract --format markdown --extract 1   # explicit
```

Output example:
```markdown
# Claude Conversation Log
**Date:** 2026-02-15 | **Session:** abc12345

---

## User
Hello, can you help me refactor this function?

---

## Claude
Sure! Let me look at the code...
```

### HTML

Styled HTML with dark theme, syntax highlighting, and collapsible sections.

```bash
claude-extract --format html --extract 1
claude-extract --format html --all
```

### JSON

Machine-readable JSON with full metadata. Ideal for programmatic analysis.

```bash
claude-extract --format json --extract 1
claude-extract --format json --all --output ~/claude-json
```

---

## Detailed Mode, Thinking, and Metadata

### Detailed Mode (`--detailed`)

Includes tool invocations, system messages, MCP responses, per-message metadata, and session statistics.

```bash
# Detailed markdown
claude-extract --detailed --extract 1

# Detailed HTML (great for browsing)
claude-extract --detailed --format html --extract 1

# Detailed JSON (for analysis)
claude-extract --detailed --format json --all
```

In detailed mode, each assistant message includes metadata:

```markdown
## Claude
> *model: claude-opus-4-6 | tokens: 3500->120 | cache read: 40,000*

Here's how to refactor that function...
```

And a statistics block is appended at the end:

```markdown
## Session Statistics

| Metric | Value |
|--------|-------|
| Models | claude-opus-4-6 |
| User turns | 15 |
| Tool invocations | 47 |
| Subagents spawned | 3 |
| Total input tokens | 1,250 |
| Total output tokens | 15,890 |
| Cache read tokens | 850,000 |
| Total duration | 8m 32s |
| Git branch | feature/auth |

**Tools breakdown:**
- Bash: 12
- Read: 10
- Edit: 8
- Grep: 7
- Write: 5
- Glob: 3
- Task: 2
```

### Thinking Blocks (`--thinking`)

When Claude uses extended thinking (e.g., with Opus models), the internal reasoning is captured. By default, thinking blocks are hidden. Use `--thinking` to include them:

```bash
# Include thinking blocks
claude-extract --thinking --extract 1

# Thinking + detailed (full picture)
claude-extract --thinking --detailed --extract 1
```

In Markdown output, thinking blocks render as collapsible sections:

```markdown
<details>
<summary>Claude's Thinking</summary>

Let me analyze this step by step. The user wants to refactor
the authentication middleware, so I need to understand the
current flow before suggesting changes...

</details>
```

In HTML, thinking blocks have a distinct visual style and are collapsed by default.

### Combining Flags

```bash
# The full picture: detailed + thinking + HTML
claude-extract --detailed --thinking --format html --extract 1

# All sessions, fully detailed
claude-extract --detailed --thinking --all --output ~/full-archive
```

---

## Subagent Conversations

When Claude Code spawns subagents (via the Task tool), their conversations are stored in separate JSONL files under a `subagents/` directory. The extractor automatically:

1. **Discovers** subagent files for each session
2. **Inlines** them at the exact point where the Task tool was invoked
3. **Excludes** subagent files from the session listing (they're not standalone conversations)

In Markdown output, subagents appear as nested sections:

```markdown
### Subagent: general-purpose

> Model: claude-haiku-4-5

#### User (subagent)
Search for all files matching *.test.ts

#### Claude (subagent)
Found 12 test files...
```

In HTML, subagent conversations are visually indented with a distinct border.

No special flags are needed -- subagent handling is automatic.

---

## Organization Options

### Organize by Date

```bash
# Group into date folders (YYYY-MM-DD)
claude-extract --by-day --all
```

```
Claude logs/
  2026-02-14/
    2026-02-14-09_15-abc12345.md
    2026-02-14-14_30-def67890.md
  2026-02-15/
    2026-02-15-10_00-ghi11223.md
```

### Organize by Project

```bash
# Group into project folders
claude-extract --by-project --all
```

```
Claude logs/
  my-webapp/
    2026-02-15-10_00-abc12345.md
  data-pipeline/
    2026-02-14-09_15-def67890.md
```

### Combined (Project + Date)

```bash
# Full hierarchy
claude-extract --by-project --by-day --all
```

```
Claude logs/
  my-webapp/
    2026-02-14/
      2026-02-14-09_15-abc12345.md
    2026-02-15/
      2026-02-15-10_00-def67890.md
  data-pipeline/
    2026-02-14/
      2026-02-14-14_30-ghi11223.md
```

---

## Date Filtering

Filter sessions by when they were last modified:

```bash
# Sessions from a specific date onwards
claude-extract --from-date 2026-01-01 --all

# Sessions up to a specific date
claude-extract --to-date 2026-01-31 --all

# Date range
claude-extract --from-date 2026-01-01 --to-date 2026-01-31 --all

# Combine with other flags
claude-extract --from-date 2026-02-01 --by-day --detailed --all
```

Date format: `YYYY-MM-DD`

---

## Project Filtering

### List Available Projects

```bash
claude-extract --list-projects
```

### Extract from Specific Projects

```bash
# All sessions from project #1
claude-extract --project 1 --all

# From multiple projects
claude-extract --project 1,3 --all

# Recent sessions from a project
claude-extract --project 2 --recent 10

# Combine with date filter
claude-extract --project 1 --from-date 2026-01-01 --all
```

---

## Session ID Lookup

If you know part of a session UUID (visible in filenames or the `--list` output), you can extract it directly:

```bash
# Partial UUID (first 8 characters)
claude-extract --session-id abc12345

# Full UUID
claude-extract --session-id abc12345-6789-4def-abcd-123456789012

# Session ID with bash commands
claude-extract --bash-commands --session-id abc12345

# Session ID with tool ops
claude-extract --tool-ops --session-id abc12345

# Session ID with detailed + thinking
claude-extract --detailed --thinking --session-id abc12345
```

This is useful when you find a session ID in another context (e.g., a log file, a filename, or a git commit message) and want to quickly pull up that specific conversation.

---

## Search Operations

### Smart Search

Fuzzy text matching across all conversations:

```bash
# Search all conversations
claude-extract --search "authentication middleware"

# Case-sensitive search
claude-extract --search "APIError" --case-sensitive
```

### Regex Search

```bash
# Search with regex
claude-extract --search-regex "import.*pandas"

# Find function definitions
claude-extract --search-regex "def\s+\w+"

# Find error patterns
claude-extract --search-regex "Error:.*"
```

### Filter by Speaker

```bash
# Only user messages
claude-extract --search "how do I" --search-speaker human

# Only Claude's responses
claude-extract --search "here's how" --search-speaker assistant
```

### Filter by Date

```bash
# Search within date range
claude-extract --search "bug fix" --search-date-from 2026-01-01 --search-date-to 2026-01-31
```

### Real-Time Search

```bash
# Launch interactive real-time search
claude-search
```

This opens a terminal UI where results update as you type.

---

## Bash Commands Extraction

Extract only the bash commands Claude executed (successful ones), with the context of what was being done:

```bash
# From a specific session
claude-extract --bash-commands --extract 1

# From all sessions
claude-extract --bash-commands --all

# From recent sessions, organized by project
claude-extract --bash-commands --by-project --recent 20

# From a date range
claude-extract --bash-commands --from-date 2026-01-01 --all
```

Output includes each command, its output, and the context of what Claude was doing.

---

## Tool Operations Extraction

Extract all tool invocations (file reads, writes, searches, web fetches, etc.):

```bash
# All tool operations from a session
claude-extract --tool-ops --extract 1

# Filter by category
claude-extract --tool-ops --tool-filter file --all      # Read, Write, Edit
claude-extract --tool-ops --tool-filter search --all    # Grep, Glob
claude-extract --tool-ops --tool-filter web --all       # WebFetch, WebSearch
claude-extract --tool-ops --tool-filter git --all       # Git operations

# Filter by specific tool
claude-extract --tool-ops --tool-filter Grep,Glob --extract 1

# Mix categories and tools
claude-extract --tool-ops --tool-filter file,Grep --all

# Include full results (file contents, search output)
claude-extract --tool-ops --detailed --all

# Organized by project and date
claude-extract --tool-ops --by-project --by-day --all
```

---

## Cross-Platform Usage

The tool works on Windows, macOS, Linux, and WSL.

### Default Data Location

| Platform | Claude data directory |
|----------|---------------------|
| macOS/Linux | `~/.claude/projects/` |
| Windows | `%USERPROFILE%\.claude\projects\` |
| WSL | `/home/username/.claude/projects/` |

### WSL Accessing Windows Claude Data

If you installed Claude Code on Windows but want to run the extractor from WSL:

```bash
# Point to Windows Claude data from WSL
claude-extract --claude-dir /mnt/c/Users/YourUsername/.claude/projects --list

# Extract from Windows data
claude-extract --claude-dir /mnt/c/Users/YourUsername/.claude/projects --all

# Combine with any other flags
claude-extract --claude-dir /mnt/c/Users/YourUsername/.claude/projects \
  --detailed --thinking --by-project --all --output ~/claude-from-windows
```

### Windows Accessing WSL Claude Data

If you installed Claude Code in WSL but want to run from Windows:

```bash
claude-extract --claude-dir \\wsl$\Ubuntu\home\username\.claude\projects --list
```

### Custom Claude Directory

The `--claude-dir` flag works for any non-standard location:

```bash
# Custom path
claude-extract --claude-dir /path/to/custom/.claude/projects --list

# Network share
claude-extract --claude-dir /mnt/nas/backups/.claude/projects --list
```

---

## Combined Examples and Recipes

### Full Archive with Everything

```bash
# Complete detailed archive organized by project and date
claude-extract --detailed --thinking --by-project --by-day --all \
  --output ~/claude-archive
```

### Daily Backup

```bash
# Incremental backup (skips already-extracted sessions)
claude-extract --by-project --by-day --all --output ~/claude-backups

# Full detailed HTML backup
claude-extract --detailed --format html --by-project --by-day --all \
  --output ~/claude-backups-html
```

### Export for Analysis

```bash
# JSON export for programmatic analysis
claude-extract --format json --detailed --all --output ~/claude-json

# Bash command history for documentation
claude-extract --bash-commands --all --output ~/bash-history

# Tool usage analysis
claude-extract --tool-ops --detailed --all --output ~/tool-analysis
```

### Project-Specific Work

```bash
# Everything from project #1 this month
claude-extract --project 1 --from-date 2026-02-01 --detailed --by-day --all

# Recent work on a project as HTML
claude-extract --project 1 --recent 10 --format html --output ~/current-project

# Project's tool operations
claude-extract --tool-ops --project 1 --by-day --all
```

### Finding a Past Conversation

```bash
# Search for a topic
claude-extract --search "database migration"

# Search for a specific error
claude-extract --search-regex "ConnectionRefused.*5432"

# Search user messages only
claude-extract --search "how to deploy" --search-speaker human

# Then extract the session you found
claude-extract --session-id abc12345 --detailed --thinking
```

---

## Automation and Scripting

### Cron Job (Linux/macOS)

```bash
# Add to crontab: crontab -e
# Run daily at 2 AM
0 2 * * * /usr/local/bin/claude-extract --by-project --by-day --all --output ~/claude-backups 2>&1 >> ~/claude-backup.log
```

### Bash Script

```bash
#!/bin/bash
# backup-claude.sh - Daily Claude conversation backup

DATE=$(date +%Y-%m-%d)
BACKUP_DIR=~/backups/claude-$DATE

# Extract all conversations
claude-extract --by-project --by-day --detailed --all --output "$BACKUP_DIR"

# Compress
tar -czf ~/backups/claude-$DATE.tar.gz -C ~/backups "claude-$DATE"
rm -rf "$BACKUP_DIR"

echo "Backup: ~/backups/claude-$DATE.tar.gz"
```

### PowerShell Script (Windows)

```powershell
# backup-claude.ps1

$Date = Get-Date -Format "yyyy-MM-dd"
$BackupDir = "$env:USERPROFILE\backups\claude-$Date"

claude-extract --by-project --by-day --detailed --all --output $BackupDir

Compress-Archive -Path $BackupDir -DestinationPath "$env:USERPROFILE\backups\claude-$Date.zip"
Remove-Item -Recurse -Force $BackupDir

Write-Host "Backup: $env:USERPROFILE\backups\claude-$Date.zip"
```

### Python Integration

```python
from pathlib import Path
from extract_claude_logs import ClaudeConversationExtractor

# Initialize
extractor = ClaudeConversationExtractor(output_dir="./exports")

# List sessions
sessions = extractor.find_sessions()
print(f"Found {len(sessions)} sessions")

# Extract a conversation
conversation = extractor.extract_conversation(
    sessions[0],
    detailed=True,
    include_thinking=True
)

# Access messages
for msg in conversation:
    if msg["role"] == "user":
        print(f"User: {msg['content'][:80]}...")
    elif msg["role"] == "assistant":
        print(f"Claude: {msg['content'][:80]}...")
    elif msg["role"] == "stats":
        print(f"Stats: {msg['content']}")

# Save as markdown
output = extractor.save_as_markdown(conversation, sessions[0].stem)
print(f"Saved to: {output}")
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Interactive UI** | `claude-start` |
| **List sessions** | `claude-extract --list` |
| **List projects** | `claude-extract --list-projects` |
| **Extract latest** | `claude-extract --extract 1` |
| **Extract all** | `claude-extract --all` |
| **Extract recent N** | `claude-extract --recent N` |
| **Extract by session ID** | `claude-extract --session-id abc12345` |
| **Search** | `claude-search "query"` |
| **Regex search** | `claude-extract --search-regex "pattern"` |
| **Export as JSON** | `claude-extract --format json --all` |
| **Export as HTML** | `claude-extract --format html --all` |
| **Detailed mode** | `claude-extract --detailed --all` |
| **Include thinking** | `claude-extract --thinking --extract 1` |
| **Organize by date** | `claude-extract --by-day --all` |
| **Organize by project** | `claude-extract --by-project --all` |
| **Filter by project** | `claude-extract --project 1 --all` |
| **Filter by date** | `claude-extract --from-date 2026-01-01 --all` |
| **Bash commands only** | `claude-extract --bash-commands --all` |
| **Tool operations** | `claude-extract --tool-ops --all` |
| **File ops only** | `claude-extract --tool-ops --tool-filter file --all` |
| **Overwrite existing** | `claude-extract --overwrite --all` |
| **Custom output dir** | `claude-extract --output ~/my-logs --all` |
| **Custom Claude dir** | `claude-extract --claude-dir /path/to/projects --list` |
| **WSL -> Windows data** | `claude-extract --claude-dir /mnt/c/Users/me/.claude/projects --list` |
| **Full help** | `claude-extract --help` |

---

## All CLI Flags

| Flag | Description |
|------|-------------|
| `--list` | List recent sessions |
| `--list-projects` | List all projects |
| `--extract N` | Extract session(s) by number (comma-separated) |
| `--session-id ID` | Extract session by UUID (full or partial) |
| `--recent N` | Extract N most recent sessions |
| `--all` | Extract all sessions |
| `--output DIR` | Output directory |
| `--claude-dir DIR` | Override Claude projects directory |
| `--format {markdown,json,html}` | Output format (default: markdown) |
| `--detailed` | Include tool use, system messages, metadata, stats |
| `--thinking` | Include Claude's thinking/reasoning blocks |
| `--by-day` | Organize into date folders |
| `--by-project` | Organize into project folders |
| `--project N` | Filter by project number(s) |
| `--from-date YYYY-MM-DD` | Filter sessions from this date |
| `--to-date YYYY-MM-DD` | Filter sessions up to this date |
| `--bash-commands` | Extract bash commands instead of conversations |
| `--tool-ops` | Extract tool operations instead of conversations |
| `--tool-filter FILTER` | Filter tool ops by category or name |
| `--search QUERY` | Search conversations (smart matching) |
| `--search-regex PATTERN` | Search with regex |
| `--search-speaker {human,assistant,both}` | Filter search by speaker |
| `--search-date-from DATE` | Search from date |
| `--search-date-to DATE` | Search to date |
| `--case-sensitive` | Case-sensitive search |
| `--overwrite` | Overwrite existing output files |
| `--skip-existing` | Skip existing files (default) |
| `--limit N` | Limit for `--list` command |
| `--interactive`, `-i` | Launch interactive UI |
| `--help` | Show help |
