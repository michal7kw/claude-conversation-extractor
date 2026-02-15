#!/usr/bin/env python3
"""
Sample conversations for testing search functionality
"""

import json
import tempfile
import uuid as _uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# New-format JSONL entry factories for testing.
# These produce entries matching Claude Code's new JSONL format with all
# required fields (uuid, sessionId, isSidechain, version, gitBranch, cwd,
# parentUuid, userType) plus the new message structures.
# ---------------------------------------------------------------------------

_COUNTER = {"ts": 0}


def _make_uuid():
    return str(_uuid.uuid4())


def _next_ts():
    _COUNTER["ts"] += 1
    return f"2026-01-15T10:{_COUNTER['ts']:02d}:00.000Z"


def _base_fields(entry_type, session_id="test-session-id", is_sidechain=False,
                 agent_id=None, timestamp=None, parent_uuid=None):
    fields = {
        "type": entry_type,
        "uuid": _make_uuid(),
        "parentUuid": parent_uuid,
        "sessionId": session_id,
        "timestamp": timestamp or _next_ts(),
        "isSidechain": is_sidechain,
        "userType": "external",
        "cwd": "/test/project",
        "version": "2.1.42",
        "gitBranch": "main",
    }
    if agent_id:
        fields["agentId"] = agent_id
    return fields


def make_user_entry(text, session_id="test-session-id", **kwargs):
    """Create a new-format user entry with string content."""
    entry = _base_fields("user", session_id=session_id, **kwargs)
    entry["message"] = {"role": "user", "content": text}
    return entry


def make_user_entry_with_tool_results(tool_results, session_id="test-session-id", **kwargs):
    """Create a new-format user entry with tool_result blocks in content array.
    tool_results: list of dicts with keys: tool_use_id, content
    """
    entry = _base_fields("user", session_id=session_id, **kwargs)
    content = []
    for tr in tool_results:
        content.append({
            "type": "tool_result",
            "tool_use_id": tr["tool_use_id"],
            "content": tr.get("content", ""),
        })
    entry["message"] = {"role": "user", "content": content}
    return entry


def make_assistant_entry(text, tool_uses=None, model="claude-opus-4-6",
                         thinking=None, session_id="test-session-id", **kwargs):
    """Create a new-format assistant entry.
    tool_uses: list of dicts with keys: id, name, input
    thinking: optional string for thinking block
    """
    entry = _base_fields("assistant", session_id=session_id, **kwargs)
    content = []
    if thinking:
        content.append({"type": "thinking", "thinking": thinking, "signature": "test-sig"})
    if text:
        content.append({"type": "text", "text": text})
    for tu in (tool_uses or []):
        content.append({
            "type": "tool_use",
            "id": tu.get("id", f"toolu_{_make_uuid().replace('-', '')[:24]}"),
            "name": tu["name"],
            "input": tu.get("input", {}),
        })
    entry["message"] = {
        "model": model,
        "id": f"msg_{_make_uuid().replace('-', '')[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_input_tokens": 5000,
            "cache_creation_input_tokens": 0,
        },
    }
    entry["requestId"] = f"req_{_make_uuid().replace('-', '')[:24]}"
    return entry


def make_progress_entry(hook_event="SessionStart", hook_name="SessionStart:startup",
                        session_id="test-session-id", **kwargs):
    """Create a new-format progress entry."""
    entry = _base_fields("progress", session_id=session_id, **kwargs)
    entry["data"] = {
        "type": "hook_progress",
        "hookEvent": hook_event,
        "hookName": hook_name,
        "command": "/bin/test-hook.sh",
    }
    tid = _make_uuid()
    entry["parentToolUseID"] = tid
    entry["toolUseID"] = tid
    return entry


def make_system_entry(subtype="turn_duration", content="", duration_ms=5000,
                      session_id="test-session-id", **kwargs):
    """Create a new-format system entry."""
    entry = _base_fields("system", session_id=session_id, **kwargs)
    entry["subtype"] = subtype
    entry["content"] = content
    entry["level"] = "info"
    entry["isMeta"] = False
    if subtype == "turn_duration":
        entry["durationMs"] = duration_ms
    return entry


def make_file_history_snapshot_entry():
    """Create a file-history-snapshot entry (should be skipped by extractor)."""
    return {
        "type": "file-history-snapshot",
        "messageId": _make_uuid(),
        "snapshot": {"messageId": _make_uuid(), "trackedFileBackups": {}, "timestamp": _next_ts()},
        "isSnapshotUpdate": False,
    }


def write_jsonl(path, entries):
    """Write entries to a JSONL file."""
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Original sample conversation data for search tests (DO NOT MODIFY below)
# ---------------------------------------------------------------------------

# Sample conversation data that covers various scenarios
SAMPLE_CONVERSATIONS = [
    {
        "id": "python_errors",
        "messages": [
            {
                "type": "user",
                "content": "How do I handle Python errors?",
                "timestamp": "2024-01-15T10:00:00Z",
            },
            {
                "type": "assistant",
                "content": (
                    "To handle errors in Python, use try-except blocks. "
                    "Here's an example:\n\n```python\ntry:\n    risky_operation()\n"
                    "except ValueError as e:\n    print(f'Error: {e}')\n```"
                ),
                "timestamp": "2024-01-15T10:01:00Z",
            },
            {
                "type": "user",
                "content": "What about handling multiple exception types?",
                "timestamp": "2024-01-15T10:02:00Z",
            },
            {
                "type": "assistant",
                "content": (
                    "You can handle multiple exceptions using multiple except blocks "
                    "or a tuple of exception types."
                ),
                "timestamp": "2024-01-15T10:03:00Z",
            },
        ],
    },
    {
        "id": "file_operations",
        "messages": [
            {
                "type": "user",
                "content": "Can you show me how to read and write files in Python?",
                "timestamp": "2024-01-16T14:30:00Z",
            },
            {
                "type": "assistant",
                "content": (
                    "Here's how to work with files:\n\n```python\n# Reading\n"
                    "with open('file.txt', 'r') as f:\n    content = f.read()\n\n"
                    "# Writing\nwith open('output.txt', 'w') as f:\n"
                    "    f.write('Hello, World!')\n```"
                ),
                "timestamp": "2024-01-16T14:31:00Z",
            },
        ],
    },
    {
        "id": "regex_patterns",
        "messages": [
            {
                "type": "user",
                "content": "I need help with regex patterns for email validation",
                "timestamp": "2024-01-17T09:15:00Z",
            },
            {
                "type": "assistant",
                "content": (
                    "Here's a regex pattern for email validation:\n\n```python\n"
                    "import re\n\npattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+"
                    "\\.[a-zA-Z]{2,}$'\nemail = 'user@example.com'\n\n"
                    "if re.match(pattern, email):\n    print('Valid email')\n```"
                ),
                "timestamp": "2024-01-17T09:16:00Z",
            },
        ],
    },
    {
        "id": "api_requests",
        "messages": [
            {
                "type": "user",
                "content": "How do I make API requests in Python?",
                "timestamp": "2024-01-18T16:45:00Z",
            },
            {
                "type": "assistant",
                "content": (
                    "You can use the requests library:\n\n```python\n"
                    "import requests\n\nresponse = requests.get("
                    "'https://api.example.com/data')\n"
                    "if response.status_code == 200:\n    data = response.json()\n```"
                ),
                "timestamp": "2024-01-18T16:46:00Z",
            },
        ],
    },
    {
        "id": "database_connection",
        "messages": [
            {
                "type": "user",
                "content": "What's the best way to connect to a PostgreSQL database?",
                "timestamp": "2024-01-19T11:20:00Z",
            },
            {
                "type": "assistant",
                "content": "I recommend using psycopg2 or SQLAlchemy for PostgreSQL connections.",
                "timestamp": "2024-01-19T11:21:00Z",
            },
        ],
    },
]


class ConversationFixtures:
    """Helper class to create test conversation files"""

    @staticmethod
    def create_test_environment():
        """Create a temporary directory with sample conversations"""
        temp_dir = tempfile.mkdtemp()
        claude_dir = Path(temp_dir) / ".claude" / "projects"

        # Create conversations in different project directories
        projects = ["python_help", "web_dev", "data_science"]

        all_files = []
        conversation_idx = 0

        for project in projects:
            project_dir = claude_dir / project
            project_dir.mkdir(parents=True)

            # Create 1-2 conversations per project
            for i in range(min(2, len(SAMPLE_CONVERSATIONS) - conversation_idx)):
                if conversation_idx >= len(SAMPLE_CONVERSATIONS):
                    break

                conv_data = SAMPLE_CONVERSATIONS[conversation_idx]
                chat_file = project_dir / f"chat_{conv_data['id']}.jsonl"

                # Write messages as JSONL
                with open(chat_file, "w") as f:
                    for msg in conv_data["messages"]:
                        f.write(json.dumps(msg) + "\n")

                all_files.append(chat_file)
                conversation_idx += 1

        return temp_dir, all_files

    @staticmethod
    def get_expected_search_results():
        """Get expected search results for various queries"""
        return {
            # Exact matches
            "Python errors": ["python_errors"],
            "PostgreSQL database": ["database_connection"],
            # Partial matches
            "python": ["python_errors", "file_operations", "api_requests"],
            "error": ["python_errors"],
            "file": ["file_operations"],
            "regex": ["regex_patterns"],
            "API": ["api_requests"],
            # Case insensitive
            "PYTHON": ["python_errors", "file_operations", "api_requests"],
            # Multi-word
            "handle errors": ["python_errors"],
            "read write files": ["file_operations"],
            # Code snippets
            "try except": ["python_errors"],
            "requests.get": ["api_requests"],
            "open file": ["file_operations"],
            # Regex patterns
            r"except \w+Error": ["python_errors"],
            r"@[a-zA-Z0-9.-]+": ["regex_patterns"],
            # No matches
            "javascript": [],
            "rust programming": [],
        }

    @staticmethod
    def get_date_filtered_results():
        """Get expected results for date-filtered searches"""
        # Assuming we set file modification times appropriately
        return {
            # Last 2 days (should get latest conversations)
            ("python", 2): ["api_requests", "database_connection"],
            # Last 5 days (should get all)
            ("python", 5): ["python_errors", "file_operations", "api_requests"],
            # Specific date range
            ("error", "2024-01-15", "2024-01-16"): ["python_errors"],
        }

    @staticmethod
    def get_speaker_filtered_results():
        """Get expected results for speaker-filtered searches"""
        return {
            # Human only
            ("Python", "human"): ["python_errors", "file_operations", "api_requests"],
            # Assistant only
            ("try-except", "assistant"): ["python_errors"],
            ("SQLAlchemy", "assistant"): ["database_connection"],
        }


def cleanup_test_environment(temp_dir):
    """Clean up the test environment"""
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
