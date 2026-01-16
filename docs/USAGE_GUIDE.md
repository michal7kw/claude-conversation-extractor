# Claude Conversation Extractor - Complete Usage Guide

A comprehensive guide to all CLI commands and options for extracting Claude Code conversations.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Commands](#basic-commands)
3. [Extraction Options](#extraction-options)
4. [Output Formats](#output-formats)
5. [Organization Options](#organization-options)
6. [Date Filtering](#date-filtering)
7. [Project Filtering](#project-filtering)
8. [Search Operations](#search-operations)
9. [Bash Commands Extraction](#bash-commands-extraction)
10. [Tool Operations Extraction](#tool-operations-extraction)
11. [Combined Examples](#combined-examples)
12. [Automation & Scripting](#automation--scripting)

---

## Quick Start

```bash
# Interactive UI (recommended for first-time users)
claude-start

# List all available sessions
claude-extract --list

# Extract the most recent conversation
claude-extract --extract 1

# Extract all conversations
claude-extract --all
```

---

## Basic Commands

### Interactive Mode

```bash
# Launch interactive UI with ASCII art and menus
claude-start

# Alternative commands (same as claude-start)
claude-extract
claude-logs
```

### Listing Sessions

```bash
# List all available sessions
claude-extract --list

# List all projects
claude-extract --list-projects
```

### Direct Search

```bash
# Launch search interface
claude-search

# Search with a query
claude-search "API integration"
```

---

## Extraction Options

### Extract Specific Sessions

```bash
# Extract session #1 (most recent)
claude-extract --extract 1

# Extract session #5
claude-extract --extract 5

# Extract multiple specific sessions
claude-extract --extract 1,3,5

# Extract sessions 1 through 5
claude-extract --extract 1,2,3,4,5
```

### Extract Recent Sessions

```bash
# Extract 5 most recent sessions
claude-extract --recent 5

# Extract 10 most recent sessions
claude-extract --recent 10

# Extract 20 most recent sessions
claude-extract --recent 20
```

### Extract All Sessions

```bash
# Extract all available sessions
claude-extract --all

# Extract all with custom output directory
claude-extract --all --output ~/my-claude-logs
```

### Custom Output Directory

```bash
# Specify output directory
claude-extract --output ~/Documents/claude-logs --extract 1

# Use current directory
claude-extract --output . --all

# Use absolute path
claude-extract --output /home/user/backups/claude --all
```

---

## Output Formats

### Markdown (Default)

```bash
# Export as Markdown (default)
claude-extract --extract 1

# Explicit Markdown format
claude-extract --format markdown --extract 1
```

### JSON

```bash
# Export as JSON
claude-extract --format json --extract 1

# Export all as JSON
claude-extract --format json --all

# JSON with custom output
claude-extract --format json --all --output ~/claude-json
```

### HTML

```bash
# Export as styled HTML
claude-extract --format html --extract 1

# Export all as HTML
claude-extract --format html --all

# HTML with detailed mode
claude-extract --format html --detailed --extract 1
```

### Detailed Mode

Include tool invocations, MCP responses, and system messages:

```bash
# Detailed Markdown
claude-extract --detailed --extract 1

# Detailed JSON
claude-extract --detailed --format json --extract 1

# Detailed HTML
claude-extract --detailed --format html --extract 1

# Detailed with all sessions
claude-extract --detailed --all
```

---

## Organization Options

### Organize by Date

```bash
# Organize into date folders (YYYY-MM-DD)
claude-extract --by-day --all

# Recent sessions by date
claude-extract --by-day --recent 20

# Specific sessions by date
claude-extract --by-day --extract 1,2,3
```

Output structure:
```
Claude logs/
├── 2025-01-10/
│   └── claude-conversation-2025-01-10-abc123.md
├── 2025-01-11/
│   └── claude-conversation-2025-01-11-def456.md
└── 2025-01-12/
    └── claude-conversation-2025-01-12-ghi789.md
```

### Organize by Project

```bash
# Organize into project folders
claude-extract --by-project --all

# Recent sessions by project
claude-extract --by-project --recent 10

# Specific sessions by project
claude-extract --by-project --extract 1,2,3
```

Output structure:
```
Claude logs/
├── my-webapp/
│   └── claude-conversation-2025-01-12-abc123.md
└── data-pipeline/
    └── claude-conversation-2025-01-11-def456.md
```

### Combined Organization (Project + Date)

```bash
# Full hierarchy: project/date/
claude-extract --by-project --by-day --all

# With custom output
claude-extract --by-project --by-day --all --output ~/claude-archive
```

Output structure:
```
Claude logs/
├── my-webapp/
│   ├── 2025-01-10/
│   │   └── claude-conversation-2025-01-10-abc123.md
│   └── 2025-01-12/
│       └── claude-conversation-2025-01-12-def456.md
└── data-pipeline/
    └── 2025-01-11/
        └── claude-conversation-2025-01-11-ghi789.md
```

### Overwrite vs Skip Existing

```bash
# Skip existing files (default behavior)
claude-extract --all

# Explicitly skip existing (same as default)
claude-extract --skip-existing --all

# Overwrite existing files
claude-extract --overwrite --all

# Overwrite with organization
claude-extract --overwrite --by-day --all
```

---

## Date Filtering

### Filter by Start Date

```bash
# Extract sessions from January 1, 2025 onwards
claude-extract --from-date 2025-01-01 --all

# Recent with start date
claude-extract --from-date 2025-01-01 --recent 10
```

### Filter by End Date

```bash
# Extract sessions up to January 31, 2025
claude-extract --to-date 2025-01-31 --all

# Recent with end date
claude-extract --to-date 2025-01-31 --recent 10
```

### Filter by Date Range

```bash
# Extract sessions within a specific month
claude-extract --from-date 2025-01-01 --to-date 2025-01-31 --all

# Extract last week
claude-extract --from-date 2025-01-08 --to-date 2025-01-15 --all

# Date range with organization
claude-extract --from-date 2025-01-01 --to-date 2025-01-31 --by-day --all

# Date range with project filter
claude-extract --from-date 2025-01-01 --project 1 --all
```

---

## Project Filtering

### List Projects

```bash
# List all available projects with details
claude-extract --list-projects
```

### Filter by Project

```bash
# Extract all sessions from project #1
claude-extract --project 1 --all

# Extract from multiple projects
claude-extract --project 1,3,5 --all

# Recent sessions from a project
claude-extract --project 2 --recent 10

# Specific sessions from a project
claude-extract --project 1 --extract 1,2,3
```

### Combine with Other Options

```bash
# Project filter with date range
claude-extract --project 1 --from-date 2025-01-01 --all

# Project filter with organization
claude-extract --project 1 --by-day --all

# Project filter with format
claude-extract --project 1 --format html --all
```

---

## Search Operations

### Basic Search

```bash
# Interactive search
claude-start
# Then select "Search conversations"

# Direct search command
claude-search "error handling"

# CLI search
claude-extract --search "API integration"
```

### Regex Search

```bash
# Search with regex pattern
claude-extract --search-regex "import.*pandas"

# Search for function definitions
claude-extract --search-regex "def\s+\w+"

# Search for class definitions
claude-extract --search-regex "class\s+\w+"
```

### Search with Date Filters

```bash
# Search within date range
claude-extract --search "bug fix" --search-date-from 2025-01-01

# Search with end date
claude-extract --search "feature" --search-date-to 2025-01-31

# Search in specific date range
claude-extract --search "refactor" --search-date-from 2025-01-01 --search-date-to 2025-01-15
```

### Search by Speaker

```bash
# Search only user messages
claude-extract --search "how do I" --search-speaker human

# Search only Claude's responses
claude-extract --search "here's how" --search-speaker assistant

# Search both (default)
claude-extract --search "python" --search-speaker both
```

### Case-Sensitive Search

```bash
# Case-sensitive search
claude-extract --search "API" --case-sensitive

# Case-insensitive (default)
claude-extract --search "api"
```

---

## Bash Commands Extraction

Extract only successful bash commands with context:

### Basic Bash Extraction

```bash
# Extract bash commands from session #1
claude-extract --bash-commands --extract 1

# Extract from multiple sessions
claude-extract --bash-commands --extract 1,3,5

# Extract from recent sessions
claude-extract --bash-commands --recent 10

# Extract from all sessions
claude-extract --bash-commands --all
```

### With Organization

```bash
# Bash commands organized by date
claude-extract --bash-commands --by-day --all

# Bash commands organized by project
claude-extract --bash-commands --by-project --all

# Full organization
claude-extract --bash-commands --by-project --by-day --all
```

### With Filters

```bash
# Bash commands from specific project
claude-extract --bash-commands --project 1 --all

# Bash commands from date range
claude-extract --bash-commands --from-date 2025-01-01 --all

# Combined filters
claude-extract --bash-commands --project 1 --from-date 2025-01-01 --by-day --all
```

---

## Tool Operations Extraction

Extract file operations, search patterns, web research, and git commands:

### Basic Tool Operations

```bash
# Extract all tool operations from session #1
claude-extract --tool-ops --extract 1

# Extract from multiple sessions
claude-extract --tool-ops --extract 1,3,5

# Extract from recent sessions
claude-extract --tool-ops --recent 10

# Extract from all sessions
claude-extract --tool-ops --all
```

### Filter by Category

Categories: `file`, `search`, `web`, `git`

```bash
# Extract only file operations (Read, Write, Edit)
claude-extract --tool-ops --tool-filter file --all

# Extract only search operations (Grep, Glob)
claude-extract --tool-ops --tool-filter search --all

# Extract only web operations (WebFetch, WebSearch)
claude-extract --tool-ops --tool-filter web --all

# Extract only git operations
claude-extract --tool-ops --tool-filter git --all

# Extract multiple categories
claude-extract --tool-ops --tool-filter file,search --all
```

### Filter by Specific Tools

Tools: `Read`, `Write`, `Edit`, `Grep`, `Glob`, `WebFetch`, `WebSearch`

```bash
# Extract only Read operations
claude-extract --tool-ops --tool-filter Read --all

# Extract only Grep and Glob operations
claude-extract --tool-ops --tool-filter Grep,Glob --all

# Extract Write and Edit operations
claude-extract --tool-ops --tool-filter Write,Edit --all

# Mix categories and tools
claude-extract --tool-ops --tool-filter file,Grep --all
```

### With Detailed Results

```bash
# Include full tool results (file contents, search output, etc.)
claude-extract --tool-ops --detailed --all

# Detailed with filter
claude-extract --tool-ops --detailed --tool-filter file --all
```

### With Organization

```bash
# Tool operations organized by date
claude-extract --tool-ops --by-day --all

# Tool operations organized by project
claude-extract --tool-ops --by-project --all

# Full organization
claude-extract --tool-ops --by-project --by-day --all
```

### With Other Filters

```bash
# Tool operations from specific project
claude-extract --tool-ops --project 1 --all

# Tool operations from date range
claude-extract --tool-ops --from-date 2025-01-01 --all

# Combined filters
claude-extract --tool-ops --tool-filter file --project 1 --from-date 2025-01-01 --by-day --all
```

---

## Combined Examples

### Daily Backup Script

```bash
# Full daily backup with organization
claude-extract --by-project --by-day --all --output ~/claude-daily-backup

# Detailed HTML backup
claude-extract --by-project --by-day --format html --detailed --all --output ~/claude-backup

# Incremental backup (skips existing)
claude-extract --by-project --by-day --all --output ~/claude-backup
```

### Export for Analysis

```bash
# Export all as JSON for programmatic analysis
claude-extract --format json --all --output ~/claude-json-archive

# Export tool operations for workflow analysis
claude-extract --tool-ops --format json --all --output ~/tool-analysis

# Export bash commands for script documentation
claude-extract --bash-commands --all --output ~/bash-history
```

### Project-Specific Export

```bash
# Export everything from a specific project
claude-extract --project 1 --by-day --detailed --format html --all

# Export recent work on project
claude-extract --project 1 --recent 10 --by-day --output ~/current-project

# Export project's tool operations
claude-extract --tool-ops --project 1 --by-day --all
```

### Time-Based Reports

```bash
# This month's conversations
claude-extract --from-date 2025-01-01 --to-date 2025-01-31 --by-day --all

# Last week's detailed export
claude-extract --from-date 2025-01-08 --detailed --format html --all

# Q1 2025 archive
claude-extract --from-date 2025-01-01 --to-date 2025-03-31 --by-project --by-day --all
```

### Search and Export

```bash
# Search and view results
claude-extract --search "machine learning"

# Export matching as HTML
claude-extract --search "API" --format html

# Regex search for patterns
claude-extract --search-regex "async.*await" --format json
```

---

## Automation & Scripting

### Cron Job for Daily Backup

```bash
# Add to crontab (crontab -e)
# Run at 2 AM daily
0 2 * * * /usr/local/bin/claude-extract --by-project --by-day --all --output ~/claude-backups
```

### Bash Backup Script

```bash
#!/bin/bash
# backup-claude.sh

DATE=$(date +%Y-%m-%d)
BACKUP_DIR=~/backups/claude-$DATE

# Create backup
claude-extract --by-project --by-day --all --output "$BACKUP_DIR"

# Compress
tar -czf ~/backups/claude-$DATE.tar.gz "$BACKUP_DIR"

# Clean up directory
rm -rf "$BACKUP_DIR"

echo "Backup completed: ~/backups/claude-$DATE.tar.gz"
```

### PowerShell Backup Script (Windows)

```powershell
# backup-claude.ps1

$Date = Get-Date -Format "yyyy-MM-dd"
$BackupDir = "$env:USERPROFILE\backups\claude-$Date"

# Create backup
claude-extract --by-project --by-day --all --output $BackupDir

# Compress
Compress-Archive -Path $BackupDir -DestinationPath "$env:USERPROFILE\backups\claude-$Date.zip"

# Clean up
Remove-Item -Recurse -Force $BackupDir

Write-Host "Backup completed: $env:USERPROFILE\backups\claude-$Date.zip"
```

### Python Integration

```python
import subprocess
import json
from pathlib import Path

# Export as JSON
result = subprocess.run(
    ["claude-extract", "--format", "json", "--all", "--output", "/tmp/claude-export"],
    capture_output=True,
    text=True
)

# Process exported files
export_dir = Path("/tmp/claude-export")
for json_file in export_dir.glob("*.json"):
    with open(json_file) as f:
        conversation = json.load(f)
        print(f"Session: {conversation['session_id']}")
        print(f"Messages: {conversation['message_count']}")
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Interactive UI | `claude-start` |
| List sessions | `claude-extract --list` |
| List projects | `claude-extract --list-projects` |
| Extract latest | `claude-extract --extract 1` |
| Extract all | `claude-extract --all` |
| Extract recent N | `claude-extract --recent N` |
| Search | `claude-search "query"` |
| Export as JSON | `claude-extract --format json --all` |
| Export as HTML | `claude-extract --format html --all` |
| Detailed mode | `claude-extract --detailed --all` |
| Organize by date | `claude-extract --by-day --all` |
| Organize by project | `claude-extract --by-project --all` |
| Filter by project | `claude-extract --project 1 --all` |
| Filter by date | `claude-extract --from-date YYYY-MM-DD --all` |
| Bash commands only | `claude-extract --bash-commands --all` |
| Tool operations | `claude-extract --tool-ops --all` |
| File ops only | `claude-extract --tool-ops --tool-filter file --all` |
| Overwrite existing | `claude-extract --overwrite --all` |

---

## Help

```bash
# Show all available options
claude-extract --help
```
