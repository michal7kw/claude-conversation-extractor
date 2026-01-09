# Claude Conversation Extractor - Export Claude Code Conversations to Markdown | Save Chat History

run
```
claude-extract --overwrite --from-date 2026-01-01 --by-project --by-day --all --output .
```


> **The ONLY tool to export Claude Code conversations**. Extract Claude chat history from ~/.claude/projects, search through logs, and backup your AI programming sessions.

## Two Ways to Use

- **`claude-start`** - Interactive UI with ASCII art logo, real-time search, and menu-driven interface (recommended)
- **`claude-extract`** - Plain CLI for command-line operations and scripting

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/claude-conversation-extractor.svg)](https://badge.fury.io/py/claude-conversation-extractor)
[![Downloads](https://pepy.tech/badge/claude-conversation-extractor)](https://pepy.tech/project/claude-conversation-extractor)
[![GitHub stars](https://img.shields.io/github/stars/ZeroSumQuant/claude-conversation-extractor?style=social)](https://github.com/ZeroSumQuant/claude-conversation-extractor)

**Export Claude Code conversations with the #1 extraction tool.** Claude Code stores chats in ~/.claude/projects as JSONL files with no export button - this tool solves that.

**What users search for:** [Export Claude conversations](#how-to-export-claude-code-conversations) | [Claude Code logs location](#where-are-claude-code-logs-stored) | [Backup Claude sessions](#backup-all-claude-conversations) | [Claude JSONL to Markdown](#convert-claude-jsonl-to-markdown)

## How to Export Claude Code Conversations - Demo

![Export Claude Code conversations demo - Claude Conversation Extractor in action](https://raw.githubusercontent.com/ZeroSumQuant/claude-conversation-extractor/main/assets/demo.gif)

## Can't Export Claude Code Conversations? We Solved It.

**Claude Code has no export button.** Your conversations are trapped in `~/.claude/projects/` as undocumented JSONL files. You need:
- **Export Claude Code conversations** before they're deleted
- **Search Claude Code chat history** to find that solution from last week
- **Backup Claude Code logs** for documentation or sharing
- **Convert Claude JSONL to Markdown** for readable archives

## Claude Conversation Extractor: The First Export Tool for Claude Code

This is the **ONLY tool that exports Claude Code conversations**:
- **Finds Claude Code logs** automatically in ~/.claude/projects
- **Extracts Claude conversations** to clean Markdown files
- **Searches Claude chat history** with real-time results
- **Backs up all Claude sessions** with one command
- **Works on Windows, macOS, Linux** - wherever Claude Code runs

## Features for Claude Code Users

- **Real-Time Search**: Search Claude conversations as you type - no flags needed
- **Claude JSONL to Markdown**: Clean export without terminal artifacts
- **Find Any Chat**: Search by content, date, or conversation name
- **Bulk Export**: Extract all Claude Code conversations at once
- **Extract Bash Commands**: Export only successful bash commands with context commentary
- **Extract Plans**: Automatically detect and format Claude's approved implementation plans
- **Extract Q&A**: Capture user questions (AskUserQuestion tool) and their answers
- **Organize by Date/Project**: Structure exports into date or project folders
- **Skip Existing**: Incremental exports that skip already-extracted conversations
- **Zero Config**: Just run `claude-extract` - we find everything automatically
- **No Dependencies**: Pure Python - no external packages required
- **Cross-Platform**: Export Claude Code logs on any OS
- **97% Test Coverage**: Reliable extraction you can trust

## Install Claude Conversation Extractor

### Quick Install (Recommended)

```bash
# Using pipx (solves Python environment issues)
pipx install claude-conversation-extractor

# OR using pip
pip install claude-conversation-extractor
```

### Install from GitHub (Latest Features)

```bash
# Install directly from GitHub for the latest features
pip install git+https://github.com/michal7kw/claude-conversation-extractor.git

# Reinstall to update (use --no-cache-dir to ensure fresh download)
pip uninstall claude-conversation-extractor -y
pip install --no-cache-dir git+https://github.com/michal7kw/claude-conversation-extractor.git
```

### Platform-Specific Setup

<details>
<summary>macOS</summary>

```bash
# Install pipx first
brew install pipx
pipx ensurepath

# Then install the extractor
pipx install claude-conversation-extractor
```
</details>

<details>
<summary>Windows</summary>

```bash
# Install pipx
py -m pip install --user pipx
py -m pipx ensurepath
# Restart terminal, then:

# Install the extractor
pipx install claude-conversation-extractor
```
</details>

<details>
<summary>Linux</summary>

```bash
# Ubuntu/Debian
sudo apt install pipx
pipx ensurepath

# Install the extractor
pipx install claude-conversation-extractor
```
</details>

<details>
<summary>HPC Cluster (with Conda)</summary>

```bash
# SSH into your cluster
ssh your_username@cluster_address

# Create/activate conda environment
conda create -n claude-extract python=3.10 -y
conda activate claude-extract

# Install from GitHub
pip install git+https://github.com/michal7kw/claude-conversation-extractor.git

# Verify installation
claude-extract --help
```
</details>

---

## Command Reference

### Basic Commands

| Command | Description |
|---------|-------------|
| `claude-start` | Launch interactive UI with ASCII art and menus |
| `claude-extract` | CLI interface (shows help by default) |
| `claude-search` | Direct search command |
| `claude-extract --list` | List all available sessions |
| `claude-extract --help` | Show all available options |

### Extraction Options

| Option | Description |
|--------|-------------|
| `--extract N` | Extract session number N |
| `--extract 1,3,5` | Extract multiple specific sessions |
| `--recent N` | Extract N most recent sessions |
| `--all` | Extract all sessions |
| `--output DIR` | Save to custom directory |
| `--bash-commands` | Extract only successful bash commands with context |
| `--list-projects` | List all available projects |
| `--project N` | Extract from specific project(s) by number |

### Export Format Options

| Option | Description |
|--------|-------------|
| `--format markdown` | Export as Markdown (default) |
| `--format json` | Export as JSON with metadata |
| `--format html` | Export as styled HTML |
| `--detailed` | Include tool use, MCP responses, system messages |

### Organization Options

| Option | Description |
|--------|-------------|
| `--by-day` | Organize into date folders (YYYY-MM-DD) |
| `--by-project` | Organize into project folders |
| `--by-project --by-day` | Hierarchy: project/date/ |
| `--overwrite` | Overwrite existing files (default is to skip) |
| `--from-date YYYY-MM-DD` | Only extract sessions from this date onwards |
| `--to-date YYYY-MM-DD` | Only extract sessions up to this date |

### Search Options

| Option | Description |
|--------|-------------|
| `--search "text"` | Smart text search |
| `--search-regex "pattern"` | Regex pattern search |
| `--search-date-from YYYY-MM-DD` | Filter from date |
| `--search-date-to YYYY-MM-DD` | Filter to date |
| `--search-speaker human/assistant/both` | Filter by speaker |
| `--case-sensitive` | Case-sensitive search |

---

## Usage Examples

### Basic Extraction

```bash
# List all available conversations
claude-extract --list

# Extract the most recent conversation
claude-extract --extract 1

# Extract multiple specific sessions
claude-extract --extract 1,3,5

# Extract 10 most recent sessions
claude-extract --recent 10

# Extract all conversations
claude-extract --all

# Save to a specific directory
claude-extract --all --output ~/my-claude-logs
```

### Export Formats

```bash
# Export as Markdown (default)
claude-extract --extract 1

# Export as JSON for programmatic processing
claude-extract --format json --extract 1

# Export as HTML with beautiful formatting
claude-extract --format html --all

# Include tool use, MCP responses, and system messages
claude-extract --detailed --extract 1

# Combine format and detailed mode
claude-extract --format html --detailed --recent 5
```

### Organize by Date

```bash
# Extract all conversations into date folders
claude-extract --by-day --all
# Output structure:
# Claude logs/
# ├── 2025-12-10/
# │   └── claude-conversation-2025-12-10-abc123.md
# ├── 2025-12-11/
# │   └── claude-conversation-2025-12-11-def456.md
# └── 2025-12-12/
#     └── claude-conversation-2025-12-12-ghi789.md

# Export recent sessions by date
claude-extract --by-day --recent 20

# Export to custom directory with date organization
claude-extract --by-day --all --output ~/claude-archive
```

### Organize by Project

```bash
# Extract all conversations into project folders
claude-extract --by-project --all
# Output structure:
# Claude logs/
# ├── my_webapp/
# │   └── claude-conversation-2025-12-12-abc123.md
# └── data_pipeline/
#     └── claude-conversation-2025-12-11-def456.md

# Export specific sessions by project
claude-extract --by-project --extract 1,2,3
```

### Organize by Project AND Date

```bash
# Full organization: project folders containing date folders
claude-extract --by-project --by-day --all
# Output structure:
# Claude logs/
# ├── my_webapp/
# │   ├── 2025-12-10/
# │   │   └── claude-conversation-2025-12-10-abc123.md
# │   └── 2025-12-12/
# │       └── claude-conversation-2025-12-12-def456.md
# └── data_pipeline/
#     └── 2025-12-11/
#         └── claude-conversation-2025-12-11-ghi789.md
```

### Incremental Exports and Overwrite

```bash
# First run: extracts everything
claude-extract --by-day --all --output ~/daily-backup

# Second run: automatically skips already extracted files (default behavior)
claude-extract --by-day --all --output ~/daily-backup
# Output: "Skipped: 2025-12-10/claude-conversation-2025-12-10-abc123.md (already exists)"

# Perfect for daily cron jobs - only exports new conversations
claude-extract --by-project --by-day --all

# Use --overwrite to replace existing files (e.g., re-export with different options)
claude-extract --by-day --overwrite --all --output ~/daily-backup
```

**Note**: By default, existing files are skipped. Use `--overwrite` to replace them.

### Filter by Project

```bash
# List all available projects
claude-extract --list-projects

# Extract all sessions from a specific project
claude-extract --project 1 --all

# Extract from multiple projects
claude-extract --project 1,3,5 --all

# Extract recent sessions from a specific project
claude-extract --project 2 --recent 10

# Combine project filter with date range
claude-extract --project 1 --from-date 2025-01-01 --all

# Extract bash commands from a specific project
claude-extract --bash-commands --project 2 --all
```

### Filter by Date Range

```bash
# Extract sessions from a specific date onwards
claude-extract --from-date 2025-01-01 --all

# Extract sessions up to a specific date
claude-extract --to-date 2025-01-31 --all

# Extract sessions within a date range
claude-extract --from-date 2025-01-01 --to-date 2025-01-31 --all

# Combine with other options
claude-extract --from-date 2025-01-01 --by-project --by-day --all

# Extract recent sessions within a date range
claude-extract --from-date 2025-01-01 --recent 10

# Extract bash commands from a specific month
claude-extract --bash-commands --from-date 2025-01-01 --to-date 2025-01-31 --all
```

### Search Conversations

```bash
# Interactive real-time search
claude-start
# Then select "Search conversations"

# Direct search command
claude-search "API integration"

# Search from CLI
claude-extract --search "error handling"

# Regex pattern search
claude-extract --search-regex "import.*pandas"

# Search within date range
claude-extract --search "bug fix" --search-date-from 2025-12-01 --search-date-to 2025-12-15

# Search only user messages
claude-extract --search "how do I" --search-speaker human

# Search only Claude's responses
claude-extract --search "here's how" --search-speaker assistant

# Case-sensitive search
claude-extract --search "API" --case-sensitive
```

### Extract Bash Commands

```bash
# Extract bash commands from a specific session
claude-extract --bash-commands --extract 1

# Extract bash commands from multiple sessions
claude-extract --bash-commands --extract 1,3,5

# Extract bash commands from recent sessions
claude-extract --bash-commands --recent 10

# Extract bash commands from all sessions
claude-extract --bash-commands --all

# Organize bash command exports by project and date
claude-extract --bash-commands --by-project --by-day --all

# Bash command exports also skip existing files by default
claude-extract --bash-commands --all
```

**Output format**: Creates markdown files like `bash-commands-2025-01-15-abc123.md`:
```markdown
# Bash Commands Log

Session ID: abc12345
Date: 2025-01-15 10:00:00

Total commands: 3

---

Let me check the git status:

```bash
git status
```

---

Now installing dependencies:

```bash
npm install
```
```

**Note**: Only successful commands are included - failed commands (errors, command not found, etc.) are filtered out automatically.

### Automatic Plan & Q&A Extraction

Plans and Q&A pairs are automatically extracted and formatted in all exports. Plans are detected using two methods:
1. **Text pattern**: "User approved Claude's plan" approval messages
2. **ExitPlanMode tool**: Claude's tool call when completing plan mode

```bash
# Plans are automatically detected when you export
claude-extract --extract 1
# Output includes:
# ## 📋 Approved Plan
# **Multi-User Support Implementation Plan**
# *Saved to: `~/.claude/plans/fuzzy-jumping-rabbit.md`*
# ---
# Executive Summary...

# Q&A pairs are also automatically captured
# ## ❓ User Questions & Answers
# ### Plan output
# **Q:** How should plans be included in the output?
# **A:** Embed inline
```

**Plan Format in Exports:**
```markdown
## 📋 Approved Plan

**My Implementation Plan**

*Saved to: `~/.claude/plans/cosmic-dancing-star.md`*

---

Executive Summary

This plan covers the implementation of...
```

**Q&A Format in Exports:**
```markdown
## ❓ User Questions & Answers

### Feature selection

**Q:** Which authentication method should we use?

**A:** OAuth 2.0 (Recommended)

### Database choice

**Q:** Which database should we use?

**A:** PostgreSQL
```

**Note**: Plans and Q&A pairs appear inline in the conversation flow - no special flags needed. They are automatically detected and formatted with distinctive styling in Markdown, HTML, and JSON outputs.

### Combined Examples

```bash
# Daily backup script: organized, incremental (default), detailed HTML exports
claude-extract --by-project --by-day --format html --detailed --all --output ~/claude-daily-backup

# Export recent work on specific project
claude-extract --by-day --recent 10 --output ~/current-project-logs

# Archive everything as JSON for analysis
claude-extract --format json --all --output ~/claude-json-archive

# Search and export matching conversations
claude-extract --search "machine learning" --format html

# Full detailed export with all organization
claude-extract --by-project --by-day --detailed --format html --all --output ~/complete-archive
```

### Automation Examples

```bash
# Cron job for daily backup (add to crontab) - skips existing files by default
0 2 * * * /path/to/claude-extract --by-project --by-day --all --output ~/claude-backups

# Backup script
#!/bin/bash
DATE=$(date +%Y-%m-%d)
claude-extract --by-project --by-day --all --output ~/backups/claude-$DATE

# Export and compress
claude-extract --all --output /tmp/claude-export && tar -czf ~/claude-backup.tar.gz /tmp/claude-export
```

---

## Where Are Claude Code Logs Stored?

### Claude Code Default Locations:
- **macOS/Linux**: `~/.claude/projects/*/chat_*.jsonl`
- **Windows**: `%USERPROFILE%\.claude\projects\*\chat_*.jsonl`
- **Format**: Undocumented JSONL with base64 encoded content

### Exported Claude Conversation Locations:

**Default (no organization flags):**
```text
~/Desktop/Claude logs/claude-conversation-2025-06-09-abc123.md
```

**With `--by-day`:**
```text
~/Desktop/Claude logs/
├── 2025-12-10/
│   └── claude-conversation-2025-12-10-abc123.md
├── 2025-12-11/
│   └── claude-conversation-2025-12-11-def456.md
└── 2025-12-12/
    └── claude-conversation-2025-12-12-ghi789.md
```

**With `--by-project`:**
```text
~/Desktop/Claude logs/
├── my_webapp/
│   └── claude-conversation-2025-12-12-abc123.md
└── data_pipeline/
    └── claude-conversation-2025-12-11-def456.md
```

**With `--by-project --by-day`:**
```text
~/Desktop/Claude logs/
├── my_webapp/
│   ├── 2025-12-10/
│   │   └── claude-conversation-2025-12-10-abc123.md
│   └── 2025-12-12/
│       └── claude-conversation-2025-12-12-def456.md
└── data_pipeline/
    └── 2025-12-11/
        └── claude-conversation-2025-12-11-ghi789.md
```

---

## Frequently Asked Questions

### How do I export Claude Code conversations?
Install with `pipx install claude-conversation-extractor` then run `claude-extract`. The tool automatically finds all conversations in ~/.claude/projects.

### How do I export the detailed transcript with tool use?
Use the `--detailed` flag to include tool invocations, MCP responses, terminal outputs, and system messages:
```bash
claude-extract --detailed --format html --extract 1
```
This gives you the complete conversation as seen in Claude's Ctrl+R view.

### How do I organize exports by date?
Use `--by-day` to create date-based folders:
```bash
claude-extract --by-day --all
```

### How do I organize exports by project?
Use `--by-project` to create project-based folders:
```bash
claude-extract --by-project --all
```

### How do I do incremental backups?
By default, the tool skips already-exported files, making incremental backups automatic:
```bash
claude-extract --by-day --all
```
This checks if each output file exists and skips it, allowing new conversations to be exported while preserving existing ones. Use `--overwrite` if you need to replace existing files.

### How do I extract only bash commands?
Use `--bash-commands` to export only successful terminal commands with their context:
```bash
claude-extract --bash-commands --all
```
This creates markdown files containing just the bash commands Claude ran, along with the assistant's explanatory text. Failed commands are automatically filtered out.

### How do I extract sessions from a specific date range?
Use `--from-date` and `--to-date` to filter sessions by date:
```bash
claude-extract --from-date 2025-01-01 --to-date 2025-01-31 --all
```
This extracts only sessions from January 2025. You can use just one of the options to set a start or end date.

### How do I extract sessions from a specific project?
First list all projects, then use `--project` to filter:
```bash
claude-extract --list-projects        # See all projects with numbers
claude-extract --project 1 --all      # Extract from project #1
claude-extract --project 1,3 --all    # Extract from multiple projects
```

### How are Claude's plans extracted?
Plans are automatically detected and formatted when you export any conversation. When Claude creates an implementation plan (using `/plan` mode), the approved plan appears in your export with:
- A distinctive `## 📋 Approved Plan` header
- The plan title in bold
- The path where the plan was saved
- The full plan content (Executive Summary, steps, etc.)

No special flags needed - plans are extracted automatically.

### How are user questions and answers extracted?
When Claude asks you questions using the AskUserQuestion tool (the interactive prompts you see during conversations), these Q&A pairs are automatically captured and formatted:
- `## ❓ User Questions & Answers` header
- Each question's category/header
- The question text
- Your selected answer

This preserves the decision points in your conversations.

### Where does Claude Code store conversations?
Claude Code saves all chats in `~/.claude/projects/` as JSONL files. There's no built-in export feature - that's why this tool exists.

### Can I search my Claude Code history?
Yes! Run `claude-search` or select "Search conversations" from the menu. Type anything and see results instantly.

### How to backup all Claude Code sessions?
Run `claude-extract --all` to export every conversation at once, or use the interactive menu option "Export all conversations".

### Does this work with Claude.ai (web version)?
No, this tool specifically exports Claude Code (desktop app) conversations. Claude.ai has its own export feature in settings.

### Can I convert Claude JSONL to other formats?
Yes! The tool supports multiple export formats:
- **Markdown** - Default clean text format
- **JSON** - Structured data with timestamps and metadata
- **HTML** - Beautiful web-viewable format with modern styling

Use `--format json` or `--format html` when extracting.

### Is this tool official?
No, this is an independent open-source tool. It reads the local Claude Code files on your computer - no API or internet required.

---

## Why This is the Best Claude Code Export Tool

| Feature | Claude Conversation Extractor | Manual Copy | Claude.ai Export |
|---------|------------------------------|-------------|------------------|
| Works with Claude Code | Full support | Tedious | Different product |
| Bulk export | All conversations | One at a time | N/A |
| Search capability | Real-time search | None | N/A |
| Clean formatting | Perfect Markdown | Terminal artifacts | N/A |
| Organize by date | `--by-day` flag | Manual | N/A |
| Organize by project | `--by-project` flag | Manual | N/A |
| Incremental export | Default (skips existing) | N/A | N/A |
| Extract bash commands | `--bash-commands` flag | N/A | N/A |
| Extract plans | Auto-detected | Manual | N/A |
| Extract Q&A pairs | Auto-detected | Manual | N/A |
| Multiple formats | MD, JSON, HTML | Text only | N/A |
| Zero configuration | Auto-detects | Manual process | N/A |
| Cross-platform | Win/Mac/Linux | Manual works | N/A |

---

## Technical Details

### How Claude Conversation Extractor Works

1. **Locates Claude Code logs**: Scans ~/.claude/projects for JSONL files
2. **Parses undocumented format**: Handles Claude's internal data structure
3. **Extracts conversations**: Preserves user inputs and Claude responses
4. **Detects special content**: Identifies plans (`📋`) and Q&A pairs (`❓`) automatically
5. **Converts to Markdown/JSON/HTML**: Clean format without terminal escape codes
6. **Organizes output**: Optional date and project folder structure
7. **Enables search**: Indexes content for instant searching

### Content Types Extracted

| Type | Description | Format |
|------|-------------|--------|
| **User Messages** | Your inputs to Claude | `## 👤 User` |
| **Assistant Messages** | Claude's responses | `## 🤖 Claude` |
| **Plans** | Approved implementation plans | `## 📋 Approved Plan` |
| **Q&A Pairs** | Interactive questions and answers | `## ❓ User Questions & Answers` |
| **Tool Use** | Tool invocations (detailed mode) | `### 🔧 Tool Use` |
| **Tool Results** | Tool outputs (detailed mode) | `### 📤 Tool Result` |
| **System** | System messages (detailed mode) | `### ℹ️ System` |

For detailed technical documentation, see [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

### Requirements
- Python 3.8+ (works with 3.9, 3.10, 3.11, 3.12)
- Claude Code installed with existing conversations
- No external dependencies for core features

### Optional: Advanced Search with spaCy
```bash
# For semantic search capabilities
pip install spacy
python -m spacy download en_core_web_sm
```

---

## Contributing

Help make the best Claude Code export tool even better! See [CONTRIBUTING.md](docs/development/CONTRIBUTING.md).

### Development Setup
```bash
# Clone the repo
git clone https://github.com/ZeroSumQuant/claude-conversation-extractor.git
cd claude-conversation-extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

---

## Troubleshooting Claude Export Issues

### Can't find Claude Code conversations?
- Ensure Claude Code has been used at least once
- Check `~/.claude/projects/` exists and has .jsonl files
- Verify read permissions on the directory
- Try `ls -la ~/.claude/projects/` to see if files exist

### "No Claude sessions found" error
- Claude Code must be installed and used before exporting
- Check the correct user directory is being scanned
- Ensure you're running the tool as the same user who uses Claude Code

### Installation issues?
See [INSTALL.md](docs/user/INSTALL.md) for:
- Fixing "externally managed environment" errors
- PATH configuration help
- Platform-specific troubleshooting

---

## Privacy & Security

- **100% Local**: Never sends your Claude conversations anywhere
- **No Internet**: Works completely offline
- **No Tracking**: Zero telemetry or analytics
- **Open Source**: Audit the code yourself
- **Read-Only**: Never modifies your Claude Code files

---

## Roadmap for Claude Code Export Tool

### Completed
- [x] Export Claude Code conversations to Markdown
- [x] Real-time search for Claude chat history
- [x] Bulk export all Claude sessions
- [x] Export to JSON format with metadata
- [x] Export to HTML with beautiful formatting
- [x] Detailed transcript mode with tool use/MCP responses
- [x] Direct search command (`claude-search`)
- [x] Organize by date (`--by-day`)
- [x] Organize by project (`--by-project`)
- [x] Incremental exports (skip existing by default, `--overwrite` to replace)
- [x] Extract bash commands only (`--bash-commands`)
- [x] Date range filtering (`--from-date`, `--to-date`)
- [x] Project selection (`--list-projects`, `--project`)
- [x] **Extract approved plans** - Auto-detect and format Claude's implementation plans
- [x] **Extract Q&A pairs** - Capture AskUserQuestion interactions and user answers

### Planned Features
- [ ] Export to PDF format
- [ ] Automated daily backups of Claude conversations
- [ ] Integration with Obsidian, Notion, Roam
- [ ] Watch mode for auto-export of new conversations
- [ ] Export statistics and analytics dashboard

---

## Legal Disclaimer

This tool accesses Claude Code conversation data stored locally in ~/.claude/projects on your computer. You are accessing your own data. This is an independent project not affiliated with Anthropic. Use responsibly and in accordance with Claude's terms of service.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support the Project

If this tool helps you export Claude Code conversations:
- Star this repo to help others find it
- Report issues if you find bugs
- Suggest features you'd like to see
- Share with other Claude Code users

---

**Keywords**: export claude code conversations, claude conversation extractor, claude code export tool, backup claude code logs, save claude chat history, claude jsonl to markdown, ~/.claude/projects, extract claude sessions, claude code no export button, where are claude code logs stored, claude terminal logs, anthropic claude code export, extract claude plans, extract claude qa, claude implementation plans

**Note**: This is an independent tool for exporting Claude Code conversations. Not affiliated with Anthropic.
