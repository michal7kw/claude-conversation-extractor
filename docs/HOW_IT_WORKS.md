# How the Claude Conversation Extractor Works

A comprehensive guide to understanding the internals of the Claude conversation extraction system.

---

## Table of Contents

1. [Overview](#overview)
2. [Where Claude Stores Data](#where-claude-stores-data)
3. [JSONL File Structure](#jsonl-file-structure)
4. [The Extraction Process](#the-extraction-process)
5. [Content Type Detection](#content-type-detection)
6. [Plan Extraction Deep Dive](#plan-extraction-deep-dive)
7. [Output Formatting](#output-formatting)
8. [Code Architecture](#code-architecture)

---

## Overview

The Claude Conversation Extractor is a Python tool that reads Claude Code's internal conversation logs (stored as JSONL files) and converts them into human-readable formats (Markdown, HTML, JSON).

```
┌─────────────────────────────────────────┐
│  Claude Code Conversations              │
│  ~/.claude/projects/*/*.jsonl           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  ClaudeConversationExtractor            │
│  - Reads JSONL files                    │
│  - Parses message types                 │
│  - Extracts content                     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Output Formats                         │
│  - Markdown (.md)                       │
│  - HTML (.html)                         │
│  - JSON (.json)                         │
└─────────────────────────────────────────┘
```

---

## Where Claude Stores Data

Claude Code stores all conversation data locally on your machine:

### Directory Structure

```
~/.claude/
├── projects/                          # All conversation data
│   ├── D--Github-myproject/           # Project folder (path encoded)
│   │   ├── abc12345-def6-7890.jsonl   # Main conversation file
│   │   ├── agent-a1b2c3d4.jsonl       # Sub-agent conversation
│   │   └── agent-e5f6g7h8.jsonl       # Another sub-agent
│   └── C--Users-name-Documents/       # Another project
│       └── xyz98765-...jsonl
├── plans/                             # Saved plan files
│   ├── fuzzy-jumping-rabbit.md
│   └── cosmic-dancing-star.md
└── settings.json                      # User settings
```

### Path Encoding

Project folders use encoded paths where:
- `/` or `\` becomes `-`
- `:` is removed
- Example: `D:\Github\myproject` → `D--Github-myproject`

---

## JSONL File Structure

JSONL (JSON Lines) is a format where each line is a valid JSON object. Claude uses this to store conversation events.

### Basic Entry Structure

Every JSONL entry has these common fields:

```json
{
  "type": "user|assistant|tool_use|tool_result|system|summary",
  "uuid": "unique-identifier-for-this-entry",
  "parentUuid": "uuid-of-parent-entry",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "sessionId": "session-identifier",
  "message": { ... }
}
```

### Message Types Explained

#### 1. User Messages (`type: "user"`)

When you type something to Claude:

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "How do I create a React component?"
  },
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

Content can also be an array (for multi-part messages):

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {"type": "text", "text": "Look at this image:"},
      {"type": "image", "source": {...}}
    ]
  }
}
```

#### 2. Assistant Messages (`type: "assistant"`)

Claude's responses:

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "text", "text": "Here's how to create a React component..."},
      {
        "type": "tool_use",
        "id": "toolu_abc123",
        "name": "Write",
        "input": {"file_path": "/src/Component.tsx", "content": "..."}
      }
    ]
  }
}
```

#### 3. Tool Use (`type: "tool_use"`)

When Claude uses a tool:

```json
{
  "type": "tool_use",
  "tool": {
    "name": "Bash",
    "input": {"command": "npm install react"}
  },
  "tool_use_id": "toolu_abc123"
}
```

#### 4. Tool Result (`type: "tool_result"`)

Output from a tool:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_abc123",
  "result": {
    "output": "added 5 packages in 2s",
    "error": null
  }
}
```

#### 5. System Messages (`type: "system"`)

Internal system notifications:

```json
{
  "type": "system",
  "message": "Session started"
}
```

#### 6. Summary (`type: "summary"`)

Session summaries (appears at end of conversations):

```json
{
  "type": "summary",
  "summary": "Implemented React component with TypeScript",
  "leafUuid": "last-message-uuid"
}
```

---

## The Extraction Process

### Step 1: Find Sessions

The `find_sessions()` method locates all JSONL files:

```python
def find_sessions(self, limit: int = None) -> List[Path]:
    """Find all conversation JSONL files."""
    sessions = []

    # Walk through ~/.claude/projects/
    for project_dir in self.claude_dir.iterdir():
        if project_dir.is_dir():
            # Find all .jsonl files
            for jsonl_file in project_dir.glob("*.jsonl"):
                sessions.append(jsonl_file)

    # Sort by modification time (newest first)
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return sessions[:limit] if limit else sessions
```

### Step 2: Extract Conversation

The `extract_conversation()` method reads and parses a JSONL file:

```python
def extract_conversation(self, jsonl_path: Path, detailed: bool = False) -> List[Dict]:
    """Extract messages from a JSONL file."""
    conversation = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line.strip())

            # Process based on entry type
            if entry.get("type") == "user":
                # Extract user message
                ...
            elif entry.get("type") == "assistant":
                # Extract assistant message
                ...
            elif detailed and entry.get("type") == "tool_use":
                # Extract tool usage (only in detailed mode)
                ...

    return conversation
```

### Step 3: Extract Text Content

The `_extract_text_content()` helper handles various content formats:

```python
def _extract_text_content(self, content, detailed: bool = False) -> str:
    """Extract text from various content formats."""

    # Simple string content
    if isinstance(content, str):
        return content

    # Array of content items
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Text content
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

                # Tool use (in detailed mode)
                elif detailed and item.get("type") == "tool_use":
                    tool_name = item.get("name", "unknown")
                    text_parts.append(f"🔧 Using tool: {tool_name}")

        return "\n".join(text_parts)

    # Fallback
    else:
        return str(content)
```

---

## Content Type Detection

The extractor identifies special content types using pattern matching:

### Plan Detection

Plans are detected with regex patterns:

```python
def _contains_plan_approval(self, text: str) -> bool:
    """Check if text contains a plan approval section."""
    patterns = [
        r"⏺\s*User approved Claude's plan",
        r"Plan saved to:\s*~[/\\]\.claude[/\\]plans[/\\]",
    ]
    return any(re.search(pattern, text) for pattern in patterns)
```

### Bash Command Detection

Bash commands are identified by tool usage:

```python
# In extract_bash_commands()
if entry.get("type") == "assistant":
    content = entry["message"].get("content", [])
    for item in content:
        if item.get("type") == "tool_use" and item.get("name") == "Bash":
            command = item.get("input", {}).get("command", "")
            # Extract the command
```

---

## Plan Extraction Deep Dive

### How Plans Appear in Conversations

When you approve a plan in Claude Code, a message like this appears:

```
⏺ User approved Claude's plan
  ⎿  Plan saved to: ~/.claude/plans/fuzzy-rabbit.md · /plan to edit
     My Implementation Plan

     Executive Summary

     This plan covers...
```

### Parsing the Plan

The `_parse_plan_content()` method extracts:

```python
def _parse_plan_content(self, text: str) -> Optional[Dict]:
    """Parse plan title, path, and content from approval text."""

    # 1. Extract the path
    path_match = re.search(
        r"Plan saved to:\s*(~[/\\]\.claude[/\\]plans[/\\][^\s·]+\.md)",
        text
    )
    path = path_match.group(1)  # ~/.claude/plans/fuzzy-rabbit.md

    # 2. Find content after the path line
    remaining = text[text.find(path) + len(path):]

    # 3. Skip "· /plan to edit" suffix
    if remaining.startswith("·"):
        remaining = remaining.split("\n", 1)[-1]

    # 4. First non-empty line = title
    lines = remaining.split("\n")
    for i, line in enumerate(lines):
        if line.strip():
            title = line.strip()  # "My Implementation Plan"
            content_start = i + 1
            break

    # 5. Rest = content
    content = "\n".join(lines[content_start:])

    return {
        "title": title,
        "path": path,
        "content": content
    }
```

### Result Structure

Extracted plans are stored as:

```python
{
    "role": "plan",
    "content": "original full text",
    "plan_title": "My Implementation Plan",
    "plan_path": "~/.claude/plans/fuzzy-rabbit.md",
    "plan_content": "Executive Summary\n\nThis plan covers...",
    "timestamp": "2025-01-15T10:30:00.000Z"
}
```

### ExitPlanMode Tool Detection

Claude also uses the `ExitPlanMode` tool when completing a plan in plan mode. This is a separate detection method from the text-based approval pattern above.

**When It Appears:**

When Claude finishes creating a plan and exits plan mode, it calls the `ExitPlanMode` tool with the plan content. This appears in the JSONL as:

```json
{
  "type": "assistant",
  "slug": "toasty-greeting-donut",
  "message": {
    "content": [{
      "type": "tool_use",
      "id": "toolu_xyz789",
      "name": "ExitPlanMode",
      "input": {
        "plan": "# Implementation Plan

**Objective:** Fix breaking issues..."
      }
    }]
  }
}
```

**Key Fields:**
- `slug`: The plan filename (without `.md` extension)
- `input.plan`: The full plan content in markdown format

**Detection Method:**

The `_extract_plan_from_exit_tool()` method handles this:

```python
def _extract_plan_from_exit_tool(self, entry: dict) -> Optional[Dict]:
    content = entry.get("message", {}).get("content", [])

    for item in content:
        if item.get("type") == "tool_use" and item.get("name") == "ExitPlanMode":
            plan_content = item.get("input", {}).get("plan", "")
            if plan_content:
                slug = entry.get("slug", "")
                path = f"~/.claude/plans/{slug}.md"

                # Extract title from first markdown heading
                lines = plan_content.strip().split("
")
                title = "Untitled Plan"
                for line in lines:
                    if line.strip().startswith("# "):
                        title = line.strip()[2:]
                        break

                return {"title": title, "path": path, "content": plan_content}
    return None
```

### Two Detection Methods Compared

| Aspect | Text Pattern | ExitPlanMode Tool |
|--------|--------------|-------------------|
| **Trigger** | "User approved Claude's plan" text | `ExitPlanMode` tool call |
| **Plan Location** | Inline in message text | `input.plan` field |
| **Path Source** | Parsed from "Plan saved to:" text | Constructed from `slug` field |
| **Title Source** | First non-empty line after path | First `# ` heading in content |
| **When Used** | Plan approval confirmation | Plan mode completion |

Both methods produce the same output structure with `role: "plan"`.


---

## Q&A Extraction Deep Dive

### How Questions and Answers Appear

When Claude uses the `AskUserQuestion` tool, a question-answer pair is created:

**Question Entry (in assistant message):**
```json
{
  "type": "assistant",
  "message": {
    "content": [{
      "type": "tool_use",
      "id": "toolu_abc123",
      "name": "AskUserQuestion",
      "input": {
        "questions": [
          {
            "question": "How should plans be included?",
            "header": "Plan output",
            "options": [
              {"label": "Embed inline", "description": "Include directly"},
              {"label": "Separate files", "description": "Extract separately"}
            ],
            "multiSelect": false
          }
        ]
      }
    }]
  }
}
```

**Answer Entry (in user message):**
```json
{
  "type": "user",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_abc123",
      "content": "User has answered: \"How should...?\"=\"Embed inline\""
    }]
  },
  "toolUseResult": {
    "answers": {
      "How should plans be included?": "Embed inline"
    }
  }
}
```

### Linking Mechanism

Questions and answers are linked via `tool_use_id`:
- Question: `"id": "toolu_abc123"` in the tool_use object
- Answer: `"tool_use_id": "toolu_abc123"` in the tool_result

### Parsing Q&A

The `_extract_questions_from_content()` method finds questions:

```python
def _extract_questions_from_content(self, content: list) -> Optional[Dict]:
    """Extract AskUserQuestion data from message content."""
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "tool_use" and item.get("name") == "AskUserQuestion":
                return {
                    "tool_use_id": item.get("id"),
                    "questions": item.get("input", {}).get("questions", [])
                }
    return None
```

The `_extract_answers_from_entry()` method finds answers:

```python
def _extract_answers_from_entry(self, entry: dict) -> Optional[Dict]:
    """Extract answers from a user message entry."""
    content = entry.get("message", {}).get("content", [])
    for item in content:
        if isinstance(item, dict) and item.get("type") == "tool_result":
            tool_use_id = item.get("tool_use_id")
            answers = entry.get("toolUseResult", {}).get("answers", {})
            if answers and tool_use_id:
                return {"tool_use_id": tool_use_id, "answers": answers}
    return None
```

### Result Structure

Extracted Q&A pairs are stored as:

```python
{
    "role": "qa",
    "questions": [
        {
            "question": "How should plans be included?",
            "header": "Plan output",
            "options": [...],
            "multiSelect": false
        }
    ],
    "answers": {
        "How should plans be included?": "Embed inline"
    },
    "timestamp": "2025-01-15T10:30:00.000Z"
}
```

---

## Output Formatting

### Markdown Output

The `save_as_markdown()` method creates clean markdown:

```python
def save_as_markdown(self, conversation, session_id, ...):
    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write("# Claude Conversation Log\n\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Date: {date_str}\n\n---\n\n")

        # Messages
        for msg in conversation:
            role = msg["role"]

            if role == "user":
                f.write("## 👤 User\n\n")
                f.write(f"{msg['content']}\n\n")

            elif role == "assistant":
                f.write("## 🤖 Claude\n\n")
                f.write(f"{msg['content']}\n\n")

            elif role == "plan":
                f.write("## 📋 Approved Plan\n\n")
                f.write(f"**{msg['plan_title']}**\n\n")
                f.write(f"*Saved to: `{msg['plan_path']}`*\n\n")
                f.write("---\n\n")
                f.write(f"{msg['plan_content']}\n\n")

            f.write("---\n\n")
```

### HTML Output

The `save_as_html()` method creates styled HTML:

```python
def save_as_html(self, conversation, session_id, ...):
    # CSS for different message types
    css = """
        .user { border-left: 4px solid #3498db; }
        .assistant { border-left: 4px solid #2ecc71; }
        .plan { border-left: 4px solid #9b59b6; background: #f9f5ff; }
        .tool_use { border-left: 4px solid #f39c12; }
        .tool_result { border-left: 4px solid #e74c3c; }
    """

    # Generate HTML for each message
    for msg in conversation:
        role = msg["role"]
        html += f'<div class="message {role}">'

        if role == "plan":
            html += f'<div class="plan-title">{msg["plan_title"]}</div>'
            html += f'<div class="plan-path">Saved to: {msg["plan_path"]}</div>'
            html += f'<div class="plan-content">{msg["plan_content"]}</div>'
        else:
            html += f'<div class="content">{msg["content"]}</div>'

        html += '</div>'
```

### JSON Output

The `save_as_json()` method preserves all data:

```python
def save_as_json(self, conversation, session_id, ...):
    output = {
        "session_id": session_id,
        "date": date_str,
        "message_count": len(conversation),
        "messages": conversation  # All fields preserved
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
```

---

## Code Architecture

### Class Structure

```
ClaudeConversationExtractor
│
├── __init__(output_dir)
│   └── Sets up paths to ~/.claude and output directory
│
├── Session Discovery
│   ├── find_sessions(limit)      → List[Path]
│   ├── find_projects()           → Dict[str, List[Path]]
│   └── filter_sessions_by_date() → List[Path]
│
├── Extraction
│   ├── extract_conversation(path, detailed) → List[Dict]
│   ├── extract_bash_commands(path)          → List[Dict]
│   └── _extract_text_content(content)       → str
│
├── Plan Detection
│   ├── _contains_plan_approval(text)  → bool
│   └── _parse_plan_content(text)      → Dict
│
├── Output
│   ├── save_as_markdown(conversation, ...)  → Path
│   ├── save_as_html(conversation, ...)      → Path
│   ├── save_as_json(conversation, ...)      → Path
│   └── save_bash_commands_as_markdown(...)  → Path
│
└── Utilities
    ├── display_conversation(path)     → None (prints to terminal)
    ├── _get_output_dir(date, ...)     → Path
    └── _get_session_date(path)        → datetime
```

### Data Flow

```
1. User runs: claude-extract --session 0 --format markdown

2. find_sessions()
   └── Scans ~/.claude/projects/*/*.jsonl
   └── Returns sorted list of paths

3. extract_conversation(path)
   └── Opens JSONL file
   └── For each line:
       ├── Parse JSON
       ├── Check type (user/assistant/tool/system)
       ├── Extract text content
       ├── Check for plans → _contains_plan_approval()
       │   └── If plan → _parse_plan_content()
       └── Append to conversation list

4. save_as_markdown(conversation)
   └── Create output file
   └── Write header
   └── For each message:
       ├── Format based on role
       └── Write to file

5. Return output path to user
```

---

## Key Concepts Summary

| Concept | Description |
|---------|-------------|
| **JSONL** | JSON Lines format - each line is a separate JSON object |
| **Session** | One conversation, stored in one JSONL file |
| **Project** | Folder grouping sessions by working directory |
| **Entry Type** | Category of JSONL entry: user, assistant, tool_use, etc. |
| **Role** | Message role in output: user, assistant, plan, qa, tool_use, etc. |
| **Detailed Mode** | Includes tool usage and system messages |
| **Plan** | Special content type showing approved implementation plans |
| **Q&A** | Questions asked to user via AskUserQuestion tool and their answers |

---

## Example: Full Extraction Flow

```python
from src.extract_claude_logs import ClaudeConversationExtractor

# 1. Create extractor
extractor = ClaudeConversationExtractor(output_dir="./exports")

# 2. Find recent sessions
sessions = extractor.find_sessions(limit=10)
print(f"Found {len(sessions)} sessions")

# 3. Extract a conversation
conversation = extractor.extract_conversation(sessions[0], detailed=True)
print(f"Extracted {len(conversation)} messages")

# 4. Check for plans
plans = [m for m in conversation if m.get("role") == "plan"]
print(f"Found {len(plans)} plans")

# 5. Save as markdown
output = extractor.save_as_markdown(conversation, "my-session-id")
print(f"Saved to: {output}")
```

---

## Further Reading

- [README.md](../README.md) - Usage instructions
- [Source Code](../src/extract_claude_logs.py) - Full implementation
- [Claude Code Documentation](https://docs.anthropic.com/claude-code) - Official docs
