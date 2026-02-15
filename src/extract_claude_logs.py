#!/usr/bin/env python3
"""
Extract clean conversation logs from Claude Code's internal JSONL files

This tool parses the undocumented JSONL format used by Claude Code to store
conversations locally in ~/.claude/projects/ and exports them as clean,
readable markdown files.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Tool categories for extraction
TOOL_CATEGORIES = {
    "file": ["Read", "Write", "Edit"],
    "search": ["Grep", "Glob"],
    "web": ["WebFetch", "WebSearch"],
    "git": [],  # Git commands detected via Bash command content
}

ALL_EXTRACTABLE_TOOLS = ["Read", "Write", "Edit", "Grep", "Glob", "WebFetch", "WebSearch"]


class ClaudeConversationExtractor:
    """Extract and convert Claude Code conversations from JSONL to markdown."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the extractor with Claude's directory and output location."""
        self.claude_dir = Path.home() / ".claude" / "projects"

        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Try multiple possible output directories
            possible_dirs = [
                Path.home() / "Desktop" / "Claude logs",
                Path.home() / "Documents" / "Claude logs",
                Path.home() / "Claude logs",
                Path.cwd() / "claude-logs",
            ]

            # Use the first directory we can create
            for dir_path in possible_dirs:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Test if we can write to it
                    test_file = dir_path / ".test"
                    test_file.touch()
                    test_file.unlink()
                    self.output_dir = dir_path
                    break
                except Exception:
                    continue
            else:
                # Fallback to current directory
                self.output_dir = Path.cwd() / "claude-logs"
                self.output_dir.mkdir(exist_ok=True)

        print(f"📁 Saving logs to: {self.output_dir}")

    def find_sessions(self, project_path: Optional[str] = None) -> List[Path]:
        """Find all JSONL session files, sorted by most recent first."""
        if project_path:
            search_dir = self.claude_dir / project_path
        else:
            search_dir = self.claude_dir

        sessions = []
        if search_dir.exists():
            for jsonl_file in search_dir.rglob("*.jsonl"):
                # Skip subagent files — they belong to a parent session
                path_str = str(jsonl_file)
                if "/subagents/" in path_str or "\\subagents\\" in path_str:
                    continue
                sessions.append(jsonl_file)
        return sorted(sessions, key=lambda x: x.stat().st_mtime, reverse=True)

    def find_subagent_files(self, session_path: Path) -> Dict[str, Path]:
        """Find subagent JSONL files for a session.

        New-format sessions store subagent conversations at:
        {sessionId}/subagents/agent-{agentId}.jsonl

        Args:
            session_path: Path to the main session JSONL file

        Returns:
            Dict mapping agentId -> Path to subagent JSONL file
        """
        subagents_dir = session_path.parent / session_path.stem / "subagents"
        if not subagents_dir.exists():
            return {}

        result = {}
        for f in subagents_dir.glob("agent-*.jsonl"):
            agent_id = f.stem.replace("agent-", "", 1)
            result[agent_id] = f
        return result

    def extract_subagent_conversation(self, subagent_path: Path,
                                       detailed: bool = False,
                                       include_thinking: bool = False) -> Dict:
        """Extract a subagent's conversation from its JSONL file.

        Returns:
            Dict with keys: agent_id, model, messages (list of message dicts)
        """
        messages = []
        model = ""

        try:
            with open(subagent_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_type = entry.get("type", "")

                        if entry_type == "user" and "message" in entry:
                            msg = entry["message"]
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                content = msg.get("content", "")
                                text = self._extract_text_content(content)
                                if text and text.strip():
                                    messages.append({
                                        "role": "user",
                                        "content": text,
                                        "timestamp": entry.get("timestamp", ""),
                                    })

                        elif entry_type == "assistant" and "message" in entry:
                            msg = entry["message"]
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                if not model:
                                    model = msg.get("model", "")

                                content = msg.get("content", [])

                                if include_thinking and isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "thinking":
                                            thinking_text = item.get("thinking", "")
                                            if thinking_text:
                                                messages.append({
                                                    "role": "thinking",
                                                    "content": thinking_text,
                                                    "timestamp": entry.get("timestamp", ""),
                                                })

                                text = self._extract_text_content(content, detailed=detailed)
                                if text and text.strip():
                                    messages.append({
                                        "role": "assistant",
                                        "content": text,
                                        "timestamp": entry.get("timestamp", ""),
                                    })

                    except (json.JSONDecodeError, Exception):
                        continue

        except Exception:
            pass

        agent_id = subagent_path.stem.replace("agent-", "", 1)

        return {
            "agent_id": agent_id,
            "model": model,
            "messages": messages,
        }

    def find_session_by_id(self, session_id: str) -> Optional[Path]:
        """Find a session by its ID (full or partial UUID).

        Args:
            session_id: Full UUID or partial ID (prefix) of the session

        Returns:
            Path to the JSONL file if found, None otherwise
        """
        session_id = session_id.lower().strip()
        sessions = self.find_sessions()

        # First try exact match
        for session in sessions:
            if session.stem.lower() == session_id:
                return session

        # Then try prefix match
        matches = []
        for session in sessions:
            if session.stem.lower().startswith(session_id):
                matches.append(session)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"⚠️  Multiple sessions match '{session_id}':")
            for m in matches[:5]:  # Show first 5 matches
                print(f"   - {m.stem}")
            if len(matches) > 5:
                print(f"   ... and {len(matches) - 5} more")
            print("Please provide a more specific ID.")
            return None

        return None

    def find_projects(self) -> List[Path]:
        """Find all project directories containing JSONL files.

        Returns list of project directories sorted by most recent session.
        """
        projects = {}
        if self.claude_dir.exists():
            for jsonl_file in self.claude_dir.rglob("*.jsonl"):
                project_dir = jsonl_file.parent
                # Track the most recent modification time for each project
                mtime = jsonl_file.stat().st_mtime
                if project_dir not in projects or mtime > projects[project_dir]:
                    projects[project_dir] = mtime

        # Sort by most recent modification time
        return sorted(projects.keys(), key=lambda x: projects[x], reverse=True)

    def list_projects(self) -> List[Path]:
        """List all projects with details."""
        projects = self.find_projects()

        if not projects:
            print("❌ No Claude projects found in ~/.claude/projects/")
            print("💡 Make sure you've used Claude Code and have conversations saved.")
            return []

        print(f"\n📁 Found {len(projects)} Claude projects:\n")
        print("=" * 80)

        for i, project_dir in enumerate(projects, 1):
            # Get project name (clean it up for display)
            project_name = project_dir.name.replace('-', ' ').strip()
            if project_name.startswith("Users"):
                parts = project_name.split()
                project_name = "~/" + "/".join(parts[2:]) if len(parts) > 2 else "Home"

            # Count sessions in this project
            sessions = list(project_dir.glob("*.jsonl"))
            session_count = len(sessions)

            # Get most recent session date
            if sessions:
                most_recent = max(sessions, key=lambda x: x.stat().st_mtime)
                modified = datetime.fromtimestamp(most_recent.stat().st_mtime)
                date_str = modified.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = "Unknown"

            # Calculate total size
            total_size = sum(s.stat().st_size for s in sessions)
            size_kb = total_size / 1024

            print(f"\n{i}. 📁 {project_name}")
            print(f"   📄 Sessions: {session_count}")
            print(f"   📅 Last active: {date_str}")
            print(f"   💾 Total size: {size_kb:.1f} KB")
            print(f"   📂 Path: {project_dir.name}")

        print("\n" + "=" * 80)
        return projects

    def filter_sessions_by_projects(
        self, sessions: List[Path], project_indices: List[int], projects: List[Path]
    ) -> List[Path]:
        """Filter sessions to only include those from specified projects.

        Args:
            sessions: List of all session paths
            project_indices: List of project indices (0-based)
            projects: List of all project directories

        Returns:
            Filtered list of session paths
        """
        # Get the project directories for the specified indices
        selected_project_dirs = set()
        for idx in project_indices:
            if 0 <= idx < len(projects):
                selected_project_dirs.add(projects[idx])

        # Filter sessions to only include those from selected projects
        return [s for s in sessions if s.parent in selected_project_dirs]

    def extract_conversation(self, jsonl_path: Path, detailed: bool = False,
                             include_thinking: bool = False) -> List[Dict[str, str]]:
        """Extract conversation messages from a JSONL file.

        Args:
            jsonl_path: Path to the JSONL file
            detailed: If True, include tool use, system messages, and per-message metadata
            include_thinking: If True, include Claude's thinking/reasoning blocks
        """
        conversation = []
        pending_questions = {}

        from collections import Counter
        stats = {
            "models_used": set(),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cache_read_tokens": 0,
            "total_cache_creation_tokens": 0,
            "turn_count": 0,
            "tool_use_count": 0,
            "tools_used": Counter(),
            "subagent_count": 0,
            "total_duration_ms": 0,
            "session_version": "",
            "git_branch": "",
        }

        pending_task_tools = {}  # tool_use_id -> {"description": str, "subagent_type": str}
        subagent_files = self.find_subagent_files(jsonl_path)

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_type = entry.get("type", "")

                        # Capture version/branch from first entry
                        if not stats["session_version"]:
                            stats["session_version"] = entry.get("version", "")
                            stats["git_branch"] = entry.get("gitBranch", "")

                        # --- User messages ---
                        if entry_type == "user" and "message" in entry:
                            msg = entry["message"]
                            if isinstance(msg, dict) and msg.get("role") == "user":
                                # Check for subagent results in tool_result content blocks
                                content = msg.get("content", "")
                                if isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "tool_result":
                                            tool_use_id = item.get("tool_use_id", "")
                                            if tool_use_id in pending_task_tools:
                                                result_text = item.get("content", "")
                                                if isinstance(result_text, list):
                                                    result_text = "\n".join(
                                                        b.get("text", "") for b in result_text if isinstance(b, dict)
                                                    )
                                                result_text = str(result_text)

                                                agent_id_match = re.search(r'agentId:\s*(\w+)', result_text)
                                                if agent_id_match:
                                                    agent_id = agent_id_match.group(1)
                                                    if agent_id in subagent_files:
                                                        sub_conv = self.extract_subagent_conversation(
                                                            subagent_files[agent_id],
                                                            detailed=detailed,
                                                            include_thinking=include_thinking,
                                                        )
                                                        task_info = pending_task_tools[tool_use_id]
                                                        conversation.append({
                                                            "role": "subagent",
                                                            "description": task_info["description"],
                                                            "subagent_type": task_info["subagent_type"],
                                                            "agent_id": sub_conv["agent_id"],
                                                            "model": sub_conv["model"],
                                                            "messages": sub_conv["messages"],
                                                            "timestamp": entry.get("timestamp", ""),
                                                        })
                                                        if detailed:
                                                            stats["subagent_count"] += 1
                                                del pending_task_tools[tool_use_id]

                                # Check for Q&A answers
                                answer_data = self._extract_answers_from_entry(entry)
                                if answer_data:
                                    tool_id = answer_data["tool_use_id"]
                                    if tool_id in pending_questions:
                                        conversation.append({
                                            "role": "qa",
                                            "questions": pending_questions[tool_id],
                                            "answers": answer_data["answers"],
                                            "timestamp": entry.get("timestamp", ""),
                                        })
                                        del pending_questions[tool_id]
                                        continue

                                text = self._extract_text_content(content)

                                if text and text.strip():
                                    if self._contains_plan_approval(text):
                                        plan = self._parse_plan_content(text)
                                        if plan:
                                            conversation.append({
                                                "role": "plan",
                                                "content": text,
                                                "plan_title": plan["title"],
                                                "plan_path": plan["path"],
                                                "plan_content": plan["content"],
                                                "timestamp": entry.get("timestamp", ""),
                                            })
                                        else:
                                            conversation.append({
                                                "role": "user",
                                                "content": text,
                                                "timestamp": entry.get("timestamp", ""),
                                            })
                                    else:
                                        conversation.append({
                                            "role": "user",
                                            "content": text,
                                            "timestamp": entry.get("timestamp", ""),
                                        })
                                    stats["turn_count"] += 1

                        # --- Assistant messages ---
                        elif entry_type == "assistant" and "message" in entry:
                            msg = entry["message"]
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                content = msg.get("content", [])

                                # Accumulate stats for assistant messages
                                if detailed:
                                    model = msg.get("model", "")
                                    if model:
                                        stats["models_used"].add(model)
                                    usage = msg.get("usage", {})
                                    stats["total_input_tokens"] += usage.get("input_tokens", 0)
                                    stats["total_output_tokens"] += usage.get("output_tokens", 0)
                                    stats["total_cache_read_tokens"] += usage.get("cache_read_input_tokens", 0)
                                    stats["total_cache_creation_tokens"] += usage.get("cache_creation_input_tokens", 0)
                                    if isinstance(content, list):
                                        for item in content:
                                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                                stats["tool_use_count"] += 1
                                                stats["tools_used"][item.get("name", "unknown")] += 1

                                # Detect Task tool uses for subagent merging
                                if isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "tool_use":
                                            if item.get("name") == "Task":
                                                tool_input = item.get("input", {})
                                                pending_task_tools[item.get("id", "")] = {
                                                    "description": tool_input.get("description", ""),
                                                    "subagent_type": tool_input.get("subagent_type", ""),
                                                }

                                # Check for AskUserQuestion
                                qa_data = self._extract_questions_from_content(content)
                                if qa_data:
                                    pending_questions[qa_data["tool_use_id"]] = qa_data["questions"]

                                # Check for ExitPlanMode
                                exit_plan = self._extract_plan_from_exit_tool(entry)
                                if exit_plan:
                                    conversation.append({
                                        "role": "plan",
                                        "content": exit_plan["content"],
                                        "plan_title": exit_plan["title"],
                                        "plan_path": exit_plan["path"],
                                        "plan_content": exit_plan["content"],
                                        "timestamp": entry.get("timestamp", ""),
                                    })
                                    continue

                                # Extract thinking blocks if requested
                                if include_thinking and isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get("type") == "thinking":
                                            thinking_text = item.get("thinking", "")
                                            if thinking_text:
                                                conversation.append({
                                                    "role": "thinking",
                                                    "content": thinking_text,
                                                    "timestamp": entry.get("timestamp", ""),
                                                })

                                text = self._extract_text_content(content, detailed=detailed)

                                if text and text.strip():
                                    if self._contains_plan_approval(text):
                                        plan = self._parse_plan_content(text)
                                        if plan:
                                            conversation.append({
                                                "role": "plan",
                                                "content": text,
                                                "plan_title": plan["title"],
                                                "plan_path": plan["path"],
                                                "plan_content": plan["content"],
                                                "timestamp": entry.get("timestamp", ""),
                                            })
                                        else:
                                            msg_dict = {
                                                "role": "assistant",
                                                "content": text,
                                                "timestamp": entry.get("timestamp", ""),
                                            }
                                            if detailed:
                                                msg_dict["metadata"] = self._extract_message_metadata(entry)
                                            conversation.append(msg_dict)
                                    else:
                                        msg_dict = {
                                            "role": "assistant",
                                            "content": text,
                                            "timestamp": entry.get("timestamp", ""),
                                        }
                                        if detailed:
                                            msg_dict["metadata"] = self._extract_message_metadata(entry)
                                        conversation.append(msg_dict)

                        # --- System messages (new format) ---
                        elif entry_type == "system":
                            subtype = entry.get("subtype", "")

                            # Always accumulate duration stats
                            if subtype == "turn_duration":
                                stats["total_duration_ms"] += entry.get("durationMs", 0)

                            if not detailed:
                                continue

                            content = entry.get("content", "")

                            if subtype == "turn_duration":
                                duration_ms = entry.get("durationMs", 0)
                                text = f"Turn completed in {duration_ms / 1000:.1f}s"
                            elif subtype == "local_command":
                                text = f"Command: {content}"
                            else:
                                text = content or str(entry.get("subtype", "system"))

                            if text:
                                conversation.append({
                                    "role": "system",
                                    "content": f"ℹ️ System: {text}",
                                    "timestamp": entry.get("timestamp", ""),
                                })

                        # --- Progress entries (hook events) ---
                        elif entry_type == "progress" and detailed:
                            data = entry.get("data", {})
                            hook_event = data.get("hookEvent", "")
                            hook_name = data.get("hookName", "")
                            if hook_event:
                                conversation.append({
                                    "role": "system",
                                    "content": f"⚙️ Hook: {hook_event} ({hook_name})",
                                    "timestamp": entry.get("timestamp", ""),
                                })

                        # file-history-snapshot entries are skipped entirely

                    except json.JSONDecodeError:
                        continue
                    except Exception:
                        continue

        except Exception as e:
            print(f"❌ Error reading file {jsonl_path}: {e}")

        if detailed and conversation:
            stats["models_used"] = sorted(stats["models_used"])
            stats["tools_used"] = dict(stats["tools_used"])
            conversation.append({
                "role": "stats",
                "content": stats,
                "timestamp": "",
            })

        return conversation

    def extract_bash_commands(self, jsonl_path: Path) -> List[Dict]:
        """Extract successful bash commands with their surrounding context.

        Returns a list of dicts with:
        - command: The bash command that was run
        - context: The assistant's text commentary before/around the command
        - timestamp: When the command was run
        """
        bash_commands = []

        # We need to parse the file and track:
        # 1. Assistant text (context)
        # 2. Bash tool_use entries
        # 3. Corresponding tool_result entries

        try:
            entries = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Track context from assistant messages
            current_context = []
            pending_bash_commands = []  # Commands waiting for their results

            for i, entry in enumerate(entries):
                entry_type = entry.get("type", "")

                # Collect assistant text as context
                if entry_type == "assistant" and "message" in entry:
                    msg = entry["message"]
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        content = msg.get("content", [])

                        # Extract text and tool_use from assistant content
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get("type") == "text":
                                        text = item.get("text", "").strip()
                                        if text:
                                            current_context.append(text)
                                    elif item.get("type") == "tool_use":
                                        tool_name = item.get("name", "").lower()
                                        if tool_name == "bash":
                                            tool_input = item.get("input", {})
                                            command = tool_input.get("command", "")
                                            tool_use_id = item.get("id", "")
                                            if command:
                                                pending_bash_commands.append({
                                                    "command": command,
                                                    "context": "\n\n".join(current_context),
                                                    "timestamp": entry.get("timestamp", ""),
                                                    "tool_use_id": tool_use_id,
                                                })
                                                # Reset context after capturing for a command
                                                current_context = []
                        elif isinstance(content, str) and content.strip():
                            current_context.append(content.strip())

                # Extract tool_results from user message content arrays
                elif entry_type == "user":
                    msg = entry.get("message", {})
                    if isinstance(msg, dict):
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "tool_result":
                                    tool_use_id = item.get("tool_use_id", "")
                                    result_content = item.get("content", "")

                                    # Normalize result content (can be string or list of text blocks)
                                    if isinstance(result_content, list):
                                        result_content = "\n".join(
                                            b.get("text", "") for b in result_content
                                            if isinstance(b, dict)
                                        )
                                    result_content = str(result_content)

                                    # Check for errors
                                    has_error = False
                                    error_patterns = [
                                        "command not found",
                                        "No such file or directory",
                                        "Permission denied",
                                        "fatal:",
                                    ]
                                    first_line = (
                                        result_content.split('\n')[0].lower()
                                        if result_content else ""
                                    )
                                    has_error = any(
                                        pattern.lower() in first_line
                                        for pattern in error_patterns
                                    )

                                    # Match with pending commands
                                    matched_cmd = None
                                    if tool_use_id:
                                        for cmd in pending_bash_commands:
                                            if cmd.get("tool_use_id") == tool_use_id:
                                                matched_cmd = cmd
                                                pending_bash_commands.remove(cmd)
                                                break

                                    if not matched_cmd and pending_bash_commands:
                                        matched_cmd = pending_bash_commands.pop(0)

                                    if matched_cmd and not has_error:
                                        bash_commands.append({
                                            "command": matched_cmd["command"],
                                            "context": matched_cmd["context"],
                                            "timestamp": matched_cmd["timestamp"],
                                        })

                    current_context = []

        except Exception as e:
            print(f"❌ Error extracting bash commands from {jsonl_path}: {e}")

        return bash_commands

    def _is_git_command(self, command: str) -> bool:
        """Check if a bash command is a git operation."""
        if not command:
            return False
        cmd = command.strip()
        return cmd.startswith("git ") or cmd.startswith("git\t")

    def extract_tool_operations(
        self, jsonl_path: Path,
        tool_filter: Optional[List[str]] = None,
        detailed: bool = False
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """Extract tool operations from a JSONL session file.

        Args:
            jsonl_path: Path to the JSONL file
            tool_filter: Optional list of tool categories or tool names to include
                        Categories: 'file', 'search', 'web', 'git'
                        Tools: 'Read', 'Write', 'Edit', 'Grep', 'Glob', 'WebFetch', 'WebSearch'
            detailed: If True, include full tool results instead of summaries

        Returns:
            Dictionary with structure:
            {
                "file": {"Read": [...], "Write": [...], "Edit": [...]},
                "search": {"Grep": [...], "Glob": [...]},
                "web": {"WebFetch": [...], "WebSearch": [...]},
                "git": [...]  # Git commands from Bash
            }
        """
        tool_ops: Dict[str, Dict[str, List[Dict]]] = {
            "file": {"Read": [], "Write": [], "Edit": []},
            "search": {"Grep": [], "Glob": []},
            "web": {"WebFetch": [], "WebSearch": []},
            "git": [],
        }

        # Determine which tools to extract based on filter
        extract_categories = set()
        extract_tools = set()

        if tool_filter:
            for item in tool_filter:
                item_lower = item.lower()
                if item_lower in TOOL_CATEGORIES:
                    extract_categories.add(item_lower)
                    extract_tools.update(TOOL_CATEGORIES[item_lower])
                elif item in ALL_EXTRACTABLE_TOOLS:
                    extract_tools.add(item)
                elif item.lower() == "git":
                    extract_categories.add("git")
        else:
            # Extract all tools if no filter
            extract_categories = {"file", "search", "web", "git"}
            extract_tools = set(ALL_EXTRACTABLE_TOOLS)

        try:
            entries = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            current_context = []
            pending_tool_ops = {}  # tool_use_id -> tool_op_data

            for entry in entries:
                entry_type = entry.get("type", "")

                # Collect assistant text as context
                if entry_type == "assistant" and "message" in entry:
                    msg = entry["message"]
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        content = msg.get("content", [])

                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get("type") == "text":
                                        text = item.get("text", "").strip()
                                        if text:
                                            current_context.append(text)
                                    elif item.get("type") == "tool_use":
                                        tool_name = item.get("name", "")
                                        tool_input = item.get("input", {})
                                        tool_use_id = item.get("id", "")

                                        # Check if this is a tool we want to extract
                                        if tool_name in extract_tools:
                                            pending_tool_ops[tool_use_id] = {
                                                "tool_name": tool_name,
                                                "context": "\n\n".join(current_context),
                                                "timestamp": entry.get("timestamp", ""),
                                                "tool_use_id": tool_use_id,
                                                "input": tool_input,
                                            }
                                            current_context = []

                                        # Check for git commands via Bash
                                        elif tool_name == "Bash" and "git" in extract_categories:
                                            command = tool_input.get("command", "")
                                            if self._is_git_command(command):
                                                pending_tool_ops[tool_use_id] = {
                                                    "tool_name": "Bash",
                                                    "is_git": True,
                                                    "context": "\n\n".join(current_context),
                                                    "timestamp": entry.get("timestamp", ""),
                                                    "tool_use_id": tool_use_id,
                                                    "input": tool_input,
                                                }
                                                current_context = []

                        elif isinstance(content, str) and content.strip():
                            current_context.append(content.strip())

                # Extract tool_results from user message content arrays
                elif entry_type == "user":
                    msg = entry.get("message", {})
                    if isinstance(msg, dict):
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "tool_result":
                                    tool_use_id = item.get("tool_use_id", "")
                                    result_content = item.get("content", "")

                                    if tool_use_id in pending_tool_ops:
                                        tool_op = pending_tool_ops.pop(tool_use_id)
                                        tool_name = tool_op["tool_name"]

                                        result = self._normalize_tool_result(result_content)
                                        tool_op["result"] = self._summarize_tool_result(
                                            tool_name, result, tool_op.get("input", {}), detailed
                                        )

                                        # Categorize the tool operation
                                        if tool_op.get("is_git"):
                                            tool_ops["git"].append(tool_op)
                                        elif tool_name in TOOL_CATEGORIES["file"]:
                                            tool_ops["file"][tool_name].append(tool_op)
                                        elif tool_name in TOOL_CATEGORIES["search"]:
                                            tool_ops["search"][tool_name].append(tool_op)
                                        elif tool_name in TOOL_CATEGORIES["web"]:
                                            tool_ops["web"][tool_name].append(tool_op)

                    current_context = []

            # Handle any pending tool operations without results
            for tool_use_id, tool_op in pending_tool_ops.items():
                tool_name = tool_op["tool_name"]
                tool_op["result"] = {"status": "no_result"}

                if tool_op.get("is_git"):
                    tool_ops["git"].append(tool_op)
                elif tool_name in TOOL_CATEGORIES["file"]:
                    tool_ops["file"][tool_name].append(tool_op)
                elif tool_name in TOOL_CATEGORIES["search"]:
                    tool_ops["search"][tool_name].append(tool_op)
                elif tool_name in TOOL_CATEGORIES["web"]:
                    tool_ops["web"][tool_name].append(tool_op)

        except Exception as e:
            print(f"❌ Error extracting tool operations from {jsonl_path}: {e}")

        return tool_ops

    def _normalize_tool_result(self, result_content) -> Dict:
        """Normalize new-format tool result content to old result dict format."""
        if isinstance(result_content, list):
            text = "\n".join(
                b.get("text", "") for b in result_content if isinstance(b, dict)
            )
        else:
            text = str(result_content)
        return {"output": text}

    def _summarize_tool_result(
        self, tool_name: str, result: dict, tool_input: dict, detailed: bool = False
    ) -> Dict:
        """Create a summary of tool result based on tool type.

        Args:
            tool_name: Name of the tool
            result: Raw result from tool_result entry
            tool_input: Tool input parameters
            detailed: If True, include full content
        """
        output = result.get("output", "")
        error = result.get("error")

        summary = {
            "success": not bool(error),
            "error": error,
        }

        if tool_name == "Read":
            if detailed:
                summary["content"] = output
            else:
                # Count lines and estimate size
                lines = output.count("\n") + 1 if output else 0
                size = len(output.encode("utf-8")) if output else 0
                summary["lines"] = lines
                summary["size_bytes"] = size

        elif tool_name in ["Write", "Edit"]:
            if detailed:
                summary["content"] = output
            else:
                summary["status"] = "Success" if not error else "Failed"

        elif tool_name in ["Grep", "Glob"]:
            if detailed:
                summary["output"] = output
            else:
                # Try to count matched files
                if output:
                    lines = [l for l in output.split("\n") if l.strip()]
                    summary["matched_count"] = len(lines)
                    summary["matches_preview"] = lines[:5] if lines else []
                else:
                    summary["matched_count"] = 0
                    summary["matches_preview"] = []

        elif tool_name in ["WebFetch", "WebSearch"]:
            if detailed:
                summary["output"] = output
            else:
                # Truncate for preview
                summary["preview"] = output[:500] + "..." if len(output) > 500 else output

        elif tool_name == "Bash":
            # Git command
            if detailed:
                summary["output"] = output
            else:
                # Truncate output for preview
                summary["output_preview"] = output[:300] + "..." if len(output) > 300 else output

        return summary

    def _extract_text_content(self, content, detailed: bool = False) -> str:
        """Extract text from various content formats Claude uses."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_result":
                        continue  # Handled separately
                    elif detailed and item.get("type") == "tool_use":
                        tool_name = item.get("name", "unknown")
                        tool_input = item.get("input", {})
                        text_parts.append(f"\n🔧 Using tool: {tool_name}")
                        text_parts.append(f"Input: {json.dumps(tool_input, indent=2)}\n")
            return "\n".join(text_parts)
        else:
            return str(content)

    def _extract_message_metadata(self, entry: Dict) -> Dict:
        """Extract per-message metadata from an assistant entry."""
        msg = entry.get("message", {})
        usage = msg.get("usage", {})
        return {
            "model": msg.get("model", ""),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
            "cwd": entry.get("cwd", ""),
            "git_branch": entry.get("gitBranch", ""),
        }

    def _contains_plan_approval(self, text: str) -> bool:
        """Check if text contains a plan approval section.

        Detects Claude's plan approval format with patterns like:
        - "⏺ User approved Claude's plan"
        - "Plan saved to: ~/.claude/plans/"
        """
        import re
        patterns = [
            r"⏺\s*User approved Claude's plan",
            r"Plan saved to:\s*~[/\\]\.claude[/\\]plans[/\\]",
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _parse_plan_content(self, text: str) -> Optional[Dict]:
        """Parse plan title, path, and content from approval text.

        Expected format:
        ⏺ User approved Claude's plan
          ⎿  Plan saved to: ~/.claude/plans/xxx.md · /plan to edit
             Plan Title Here

             Executive Summary
             ...content...

        Returns dict with title, path, content or None if parsing fails.
        """
        import re

        # Extract path: ~/.claude/plans/xxx.md
        path_match = re.search(
            r"Plan saved to:\s*(~[/\\]\.claude[/\\]plans[/\\][^\s·]+\.md)",
            text
        )
        if not path_match:
            return None

        path = path_match.group(1)

        # Find the plan content after the path line
        path_line_end = text.find(path) + len(path)
        remaining = text[path_line_end:].strip()

        # Skip any "· /plan to edit" suffix and get to the content
        if remaining.startswith("·"):
            # Find the next newline
            newline_pos = remaining.find("\n")
            if newline_pos != -1:
                remaining = remaining[newline_pos + 1:]
            else:
                remaining = ""

        remaining = remaining.strip()

        if not remaining:
            return None

        # First non-empty line is typically the title
        lines = remaining.split("\n")
        title = ""
        content_start = 0

        for i, line in enumerate(lines):
            # Strip leading whitespace but preserve it for content
            stripped = line.strip()
            if stripped:
                title = stripped
                content_start = i + 1
                break

        # Rest is the content - preserve structure but normalize indentation
        content_lines = lines[content_start:]
        # Find minimum indentation to normalize
        non_empty_lines = [l for l in content_lines if l.strip()]
        if non_empty_lines:
            min_indent = min(len(l) - len(l.lstrip()) for l in non_empty_lines)
            content_lines = [
                l[min_indent:] if len(l) >= min_indent else l
                for l in content_lines
            ]
        content = "\n".join(content_lines).strip()

        return {
            "title": title,
            "path": path,
            "content": content,
        }

    def _extract_questions_from_content(self, content: list) -> Optional[Dict]:
        """Extract AskUserQuestion data from message content.

        Looks for tool_use entries with name "AskUserQuestion" and extracts
        the questions array along with the tool_use_id for later matching.

        Returns dict with tool_use_id and questions list, or None if not found.
        """
        if not isinstance(content, list):
            return None

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "tool_use" and item.get("name") == "AskUserQuestion":
                    return {
                        "tool_use_id": item.get("id"),
                        "questions": item.get("input", {}).get("questions", [])
                    }
        return None

    def _extract_answers_from_entry(self, entry: dict) -> Optional[Dict]:
        """Extract answers from a user message entry with tool_result.

        Looks for tool_result entries and extracts answers from the
        toolUseResult field which contains structured answer data.

        Returns dict with tool_use_id and answers dict, or None if not found.
        """
        content = entry.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return None

        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_use_id = item.get("tool_use_id")
                # Get structured answers from toolUseResult field
                answers = entry.get("toolUseResult", {}).get("answers", {})
                if answers and tool_use_id:
                    return {
                        "tool_use_id": tool_use_id,
                        "answers": answers
                    }
        return None

    def _extract_plan_from_exit_tool(self, entry: dict) -> Optional[Dict]:
        """Extract plan data from ExitPlanMode tool usage.

        Claude uses ExitPlanMode tool when completing a plan, with the plan
        content in input.plan and the plan filename in entry's slug field.

        Returns dict with title, path, and content, or None if not found.
        """
        content = entry.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return None

        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "tool_use" and item.get("name") == "ExitPlanMode":
                    plan_content = item.get("input", {}).get("plan", "")
                    if plan_content:
                        # Get slug from entry (plan filename)
                        slug = entry.get("slug", "")
                        path = f"~/.claude/plans/{slug}.md" if slug else "~/.claude/plans/unknown.md"

                        # Extract title from first markdown heading or first line
                        lines = plan_content.strip().split("\n")
                        title = "Untitled Plan"
                        for line in lines:
                            line = line.strip()
                            if line.startswith("# "):
                                title = line[2:].strip()
                                break
                            elif line and not line.startswith("#"):
                                title = line[:100]
                                break

                        return {
                            "title": title,
                            "path": path,
                            "content": plan_content,
                        }
        return None

    def display_conversation(self, jsonl_path: Path, detailed: bool = False) -> None:
        """Display a conversation in the terminal with pagination.
        
        Args:
            jsonl_path: Path to the JSONL file
            detailed: If True, include tool use and system messages
        """
        try:
            # Extract conversation
            messages = self.extract_conversation(jsonl_path, detailed=detailed)
            
            if not messages:
                print("❌ No messages found in conversation")
                return
            
            # Get session info
            session_id = jsonl_path.stem
            
            # Clear screen and show header
            print("\033[2J\033[H", end="")  # Clear screen
            print("=" * 60)
            print(f"📄 Viewing: {jsonl_path.parent.name}")
            print(f"Session: {session_id[:8]}...")
            
            # Get timestamp from first message
            first_timestamp = messages[0].get("timestamp", "")
            if first_timestamp:
                try:
                    dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                    print(f"Date: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception:
                    pass
            
            print("=" * 60)
            print("↑↓ to scroll • Q to quit • Enter to continue\n")
            
            # Display messages with pagination
            lines_shown = 8  # Header lines
            lines_per_page = 30
            
            for i, msg in enumerate(messages):
                role = msg["role"]
                content = msg["content"]
                
                # Format role display
                if role == "user" or role == "human":
                    print(f"\n{'─' * 40}")
                    print(f"👤 HUMAN:")
                    print(f"{'─' * 40}")
                elif role == "assistant":
                    print(f"\n{'─' * 40}")
                    print(f"🤖 CLAUDE:")
                    print(f"{'─' * 40}")
                elif role == "tool_use":
                    print(f"\n🔧 TOOL USE:")
                elif role == "tool_result":
                    print(f"\n📤 TOOL RESULT:")
                elif role == "system":
                    print(f"\nℹ️ SYSTEM:")
                else:
                    print(f"\n{role.upper()}:")
                
                # Display content (limit very long messages)
                lines = content.split('\n')
                max_lines_per_msg = 50
                
                for line_idx, line in enumerate(lines[:max_lines_per_msg]):
                    # Wrap very long lines
                    if len(line) > 100:
                        line = line[:97] + "..."
                    print(line)
                    lines_shown += 1
                    
                    # Check if we need to paginate
                    if lines_shown >= lines_per_page:
                        response = input("\n[Enter] Continue • [Q] Quit: ").strip().upper()
                        if response == "Q":
                            print("\n👋 Stopped viewing")
                            return
                        # Clear screen for next page
                        print("\033[2J\033[H", end="")
                        lines_shown = 0
                
                if len(lines) > max_lines_per_msg:
                    print(f"... [{len(lines) - max_lines_per_msg} more lines truncated]")
                    lines_shown += 1
            
            print("\n" + "=" * 60)
            print("📄 End of conversation")
            print("=" * 60)
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error displaying conversation: {e}")
            input("\nPress Enter to continue...")

    def _get_output_dir(
        self, date_str: str, by_day: bool = False,
        by_project: bool = False, project_name: Optional[str] = None,
        create: bool = True
    ) -> Path:
        """Determine output directory based on organization options.

        Hierarchy when both are used: project/date/

        Args:
            date_str: Date string in YYYY-MM-DD format
            by_day: If True, include date in path
            by_project: If True, include project name in path
            project_name: Name of the project
            create: If True, create the directory if it doesn't exist
        """
        output_dir = self.output_dir

        if by_project and project_name:
            output_dir = output_dir / project_name

        if by_day:
            output_dir = output_dir / date_str

        if create:
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _get_date_from_session(self, session_path: Path) -> str:
        """Extract date string from a session file's first message timestamp.

        Returns date in YYYY-MM-DD format, or current date if extraction fails.
        """
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        timestamp = entry.get("timestamp", "")
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            return dt.strftime("%Y-%m-%d")
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception:
            pass
        return datetime.now().strftime("%Y-%m-%d")

    def filter_sessions_by_date(
        self, sessions: List[Path],
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Path]:
        """Filter sessions by date range.

        Args:
            sessions: List of session paths
            from_date: Only include sessions from this date onwards
            to_date: Only include sessions up to this date

        Returns:
            Filtered list of session paths
        """
        if not from_date and not to_date:
            return sessions

        filtered = []
        for session_path in sessions:
            date_str = self._get_date_from_session(session_path)
            try:
                session_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Check from_date
                if from_date and session_date < from_date:
                    continue

                # Check to_date (include the entire day)
                if to_date and session_date > to_date:
                    continue

                filtered.append(session_path)
            except ValueError:
                # If we can't parse the date, include the session
                filtered.append(session_path)

        return filtered

    def save_as_markdown(
        self, conversation: List[Dict[str, str]], session_id: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save conversation as clean markdown file.

        Args:
            conversation: The conversation data
            session_id: Session identifier
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        if not conversation:
            return None

        # Get timestamp from first message
        first_timestamp = conversation[0].get("timestamp", "")
        if first_timestamp:
            try:
                # Parse ISO timestamp
                dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H_%M")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H_%M")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H_%M")

        filename = f"{date_str}-{time_str}-{session_id[:8]}.md"

        # Determine output directory
        output_dir = self._get_output_dir(date_str, by_day, by_project, project_name)
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Claude Conversation Log\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Date: {date_str}")
            if time_str:
                f.write(f" {time_str}")
            f.write("\n\n---\n\n")

            for msg in conversation:
                role = msg["role"]
                content = msg.get("content", "")  # Q&A entries may not have content

                if role == "user":
                    f.write("## 👤 User\n\n")
                    f.write(f"{content}\n\n")
                elif role == "assistant":
                    f.write("## 🤖 Claude\n\n")
                    metadata = msg.get("metadata")
                    if metadata:
                        model = metadata.get("model", "")
                        inp = metadata.get("input_tokens", 0)
                        out = metadata.get("output_tokens", 0)
                        cache = metadata.get("cache_read_tokens", 0)
                        parts = []
                        if model:
                            parts.append(f"model: {model}")
                        parts.append(f"tokens: {inp:,}→{out:,}")
                        if cache:
                            parts.append(f"cache read: {cache:,}")
                        f.write(f"> *{' | '.join(parts)}*\n\n")
                    f.write(f"{content}\n\n")
                elif role == "tool_use":
                    f.write("### 🔧 Tool Use\n\n")
                    f.write(f"{content}\n\n")
                elif role == "tool_result":
                    f.write("### 📤 Tool Result\n\n")
                    f.write(f"{content}\n\n")
                elif role == "system":
                    f.write("### ℹ️ System\n\n")
                    f.write(f"{content}\n\n")
                elif role == "plan":
                    f.write("## 📋 Approved Plan\n\n")
                    plan_title = msg.get("plan_title", "Untitled Plan")
                    plan_path = msg.get("plan_path", "")
                    plan_content = msg.get("plan_content", "")
                    f.write(f"**{plan_title}**\n\n")
                    if plan_path:
                        f.write(f"*Saved to: `{plan_path}`*\n\n")
                    if plan_content:
                        f.write("---\n\n")
                        f.write(f"{plan_content}\n\n")
                elif role == "qa":
                    f.write("## ❓ User Questions & Answers\n\n")
                    questions = msg.get("questions", [])
                    answers = msg.get("answers", {})
                    for q in questions:
                        question_text = q.get("question", "")
                        header = q.get("header", "")
                        options = q.get("options", [])
                        multi_select = q.get("multiSelect", False)
                        answer = answers.get(question_text, "No answer")
                        if header:
                            f.write(f"### {header}\n\n")
                        f.write(f"**Q:** {question_text}\n\n")
                        # Show all available choices
                        if options:
                            f.write("**Choices:**\n")
                            for opt in options:
                                label = opt.get("label", "")
                                description = opt.get("description", "")
                                # Mark selected answer(s)
                                if label == answer or (isinstance(answer, list) and label in answer):
                                    f.write(f"- **✓ {label}**")
                                else:
                                    f.write(f"- {label}")
                                if description:
                                    f.write(f" - {description}")
                                f.write("\n")
                            f.write("\n")
                        f.write(f"**Selected:** {answer}\n\n")
                elif role == "thinking":
                    f.write("### 💭 Thinking\n\n")
                    f.write("<details>\n<summary>Claude's reasoning</summary>\n\n")
                    f.write(f"{content}\n\n")
                    f.write("</details>\n\n")

                elif role == "subagent":
                    desc = msg.get("description", "Subagent task")
                    agent_id = msg.get("agent_id", "unknown")
                    model = msg.get("model", "unknown")
                    agent_type = msg.get("subagent_type", "")
                    f.write(f"### 🔄 Subagent: {desc}\n\n")
                    f.write(f"> *Agent: {agent_id} | Model: {model}")
                    if agent_type:
                        f.write(f" | Type: {agent_type}")
                    f.write("*\n\n")
                    for sub_msg in msg.get("messages", []):
                        sub_role = sub_msg.get("role", "")
                        sub_content = sub_msg.get("content", "")
                        if sub_role == "user":
                            f.write(f"#### 👤 User (Subagent)\n\n{sub_content}\n\n")
                        elif sub_role == "assistant":
                            f.write(f"#### 🤖 Claude (Subagent)\n\n{sub_content}\n\n")
                        elif sub_role == "thinking":
                            f.write("#### 💭 Thinking (Subagent)\n\n")
                            f.write(f"<details>\n<summary>Reasoning</summary>\n\n{sub_content}\n\n</details>\n\n")

                elif role == "stats":
                    stats = msg.get("content", {})
                    if isinstance(stats, dict):
                        f.write("## 📊 Session Statistics\n\n")
                        f.write("| Metric | Value |\n")
                        f.write("|--------|-------|\n")
                        models = ", ".join(stats.get("models_used", []))
                        f.write(f"| Models | {models} |\n")
                        f.write(f"| User turns | {stats.get('turn_count', 0)} |\n")
                        f.write(f"| Tool invocations | {stats.get('tool_use_count', 0)} |\n")
                        f.write(f"| Subagents spawned | {stats.get('subagent_count', 0)} |\n")
                        f.write(f"| Total input tokens | {stats.get('total_input_tokens', 0):,} |\n")
                        f.write(f"| Total output tokens | {stats.get('total_output_tokens', 0):,} |\n")
                        cache = stats.get("total_cache_read_tokens", 0)
                        if cache:
                            f.write(f"| Cache read tokens | {cache:,} |\n")
                        duration_ms = stats.get("total_duration_ms", 0)
                        if duration_ms:
                            mins = duration_ms // 60000
                            secs = (duration_ms % 60000) / 1000
                            f.write(f"| Total duration | {mins}m {secs:.0f}s |\n")
                        ver = stats.get("session_version", "")
                        if ver:
                            f.write(f"| Claude Code version | {ver} |\n")
                        branch = stats.get("git_branch", "")
                        if branch:
                            f.write(f"| Git branch | {branch} |\n")
                        f.write("\n")
                        tools = stats.get("tools_used", {})
                        if tools:
                            f.write("**Tools breakdown:**\n")
                            for tool_name, count in sorted(tools.items(), key=lambda x: -x[1]):
                                f.write(f"- {tool_name}: {count}\n")
                            f.write("\n")

                else:
                    f.write(f"## {role}\n\n")
                    f.write(f"{content}\n\n")
                f.write("---\n\n")

        return output_path

    def save_as_json(
        self, conversation: List[Dict[str, str]], session_id: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save conversation as JSON file.

        Args:
            conversation: The conversation data
            session_id: Session identifier
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        if not conversation:
            return None

        # Get timestamp from first message
        first_timestamp = conversation[0].get("timestamp", "")
        if first_timestamp:
            try:
                dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H_%M")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H_%M")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H_%M")

        filename = f"{date_str}-{time_str}-{session_id[:8]}.json"

        # Determine output directory
        output_dir = self._get_output_dir(date_str, by_day, by_project, project_name)
        output_path = output_dir / filename

        # Create JSON structure
        output = {
            "session_id": session_id,
            "date": date_str,
            "message_count": len(conversation),
            "messages": conversation
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output_path
    
    def save_as_html(
        self, conversation: List[Dict[str, str]], session_id: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save conversation as HTML file with syntax highlighting.

        Args:
            conversation: The conversation data
            session_id: Session identifier
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        if not conversation:
            return None

        # Get timestamp from first message
        first_timestamp = conversation[0].get("timestamp", "")
        if first_timestamp:
            try:
                dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H_%M")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H_%M")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H_%M")

        filename = f"{date_str}-{time_str}-{session_id[:8]}.html"

        # Determine output directory
        output_dir = self._get_output_dir(date_str, by_day, by_project, project_name)
        output_path = output_dir / filename

        # HTML template with modern styling
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Conversation - {session_id[:8]}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin: 0 0 10px 0;
        }}
        .metadata {{
            color: #666;
            font-size: 0.9em;
        }}
        .message {{
            background: white;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .user {{
            border-left: 4px solid #3498db;
        }}
        .assistant {{
            border-left: 4px solid #2ecc71;
        }}
        .tool_use {{
            border-left: 4px solid #f39c12;
            background: #fffbf0;
        }}
        .tool_result {{
            border-left: 4px solid #e74c3c;
            background: #fff5f5;
        }}
        .system {{
            border-left: 4px solid #95a5a6;
            background: #f8f9fa;
        }}
        .plan {{
            border-left: 4px solid #9b59b6;
            background: #f9f5ff;
        }}
        .plan-title {{
            font-size: 1.1em;
            font-weight: bold;
            color: #9b59b6;
            margin-bottom: 5px;
        }}
        .plan-path {{
            font-size: 0.85em;
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }}
        .plan-content {{
            border-top: 1px solid #e0d4f0;
            padding-top: 10px;
            margin-top: 10px;
        }}
        .qa {{
            border-left: 4px solid #e67e22;
            background: #fef9f3;
        }}
        .qa-header {{
            font-size: 1em;
            font-weight: bold;
            color: #d35400;
            margin-top: 10px;
            margin-bottom: 5px;
        }}
        .qa-question {{
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        .qa-answer {{
            color: #27ae60;
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        .qa-choices {{
            margin: 10px 0 10px 20px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .qa-choices ul {{
            margin: 5px 0 0 20px;
            padding: 0;
        }}
        .qa-choices li {{
            margin: 5px 0;
            color: #555;
        }}
        .qa-choices li strong {{
            color: #27ae60;
        }}
        .thinking {{
            border-left: 4px solid #8e44ad;
            background: #faf5ff;
        }}
        .thinking details {{
            margin: 5px 0;
        }}
        .thinking summary {{
            cursor: pointer;
            color: #8e44ad;
            font-weight: bold;
        }}
        .subagent {{
            border-left: 4px solid #16a085;
            background: #f0faf8;
        }}
        .subagent-info {{
            font-size: 0.85em;
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }}
        .subagent-message {{
            margin-left: 20px;
            padding: 8px 12px;
            border-left: 2px solid #ccc;
            margin-bottom: 8px;
        }}
        .stats {{
            border-left: 4px solid #2980b9;
            background: #f5f9ff;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .stats-table th, .stats-table td {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        .stats-table th {{
            background: #eef3f9;
        }}
        .msg-metadata {{
            font-size: 0.8em;
            color: #888;
            font-style: italic;
            margin-bottom: 8px;
        }}
        .role {{
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        pre {{
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Claude Conversation Log</h1>
        <div class="metadata">
            <p>Session ID: {session_id}</p>
            <p>Date: {date_str} {time_str}</p>
            <p>Messages: {len(conversation)}</p>
        </div>
    </div>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
            for msg in conversation:
                role = msg["role"]
                raw_content = msg.get("content", "")  # Q&A entries may not have content

                # Escape HTML only for string content
                if isinstance(raw_content, str):
                    content = raw_content.replace("&", "&amp;")
                    content = content.replace("<", "&lt;")
                    content = content.replace(">", "&gt;")
                else:
                    content = raw_content  # dicts (stats) handled separately

                role_display = {
                    "user": "👤 User",
                    "assistant": "🤖 Claude",
                    "tool_use": "🔧 Tool Use",
                    "tool_result": "📤 Tool Result",
                    "system": "ℹ️ System",
                    "plan": "📋 Approved Plan",
                    "qa": "❓ Questions & Answers",
                    "thinking": "💭 Thinking",
                    "subagent": "🔄 Subagent",
                    "stats": "📊 Session Statistics",
                }.get(role, role)

                f.write(f'    <div class="message {role}">\n')
                f.write(f'        <div class="role">{role_display}</div>\n')

                # Special handling for plan messages
                if role == "plan":
                    plan_title = msg.get("plan_title", "Untitled Plan")
                    plan_path = msg.get("plan_path", "")
                    plan_content = msg.get("plan_content", "")
                    # Escape HTML in plan content
                    plan_title = plan_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    plan_content = plan_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    f.write(f'        <div class="plan-title">{plan_title}</div>\n')
                    if plan_path:
                        f.write(f'        <div class="plan-path">Saved to: {plan_path}</div>\n')
                    if plan_content:
                        f.write(f'        <div class="plan-content">{plan_content}</div>\n')
                elif role == "qa":
                    # Special handling for Q&A messages
                    questions = msg.get("questions", [])
                    answers = msg.get("answers", {})
                    for q in questions:
                        question_text = q.get("question", "")
                        header = q.get("header", "")
                        options = q.get("options", [])
                        answer = answers.get(question_text, "No answer")
                        # Escape HTML
                        question_text = question_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        answer_str = str(answer).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        header = header.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        if header:
                            f.write(f'        <div class="qa-header">{header}</div>\n')
                        f.write(f'        <div class="qa-question">Q: {question_text}</div>\n')
                        # Show all available choices
                        if options:
                            f.write('        <div class="qa-choices"><strong>Choices:</strong><ul>\n')
                            for opt in options:
                                label = opt.get("label", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                description = opt.get("description", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                # Mark selected answer(s)
                                is_selected = label == answer or (isinstance(answer, list) and label in answer)
                                if is_selected:
                                    f.write(f'            <li><strong>✓ {label}</strong>')
                                else:
                                    f.write(f'            <li>{label}')
                                if description:
                                    f.write(f' - <em>{description}</em>')
                                f.write('</li>\n')
                            f.write('        </ul></div>\n')
                        f.write(f'        <div class="qa-answer">Selected: {answer_str}</div>\n')
                elif role == "assistant":
                    # Show metadata if present
                    metadata = msg.get("metadata")
                    if metadata:
                        model = metadata.get("model", "")
                        inp = metadata.get("input_tokens", 0)
                        out = metadata.get("output_tokens", 0)
                        cache_r = metadata.get("cache_read_tokens", 0)
                        parts = []
                        if model:
                            parts.append(f"model: {model}")
                        parts.append(f"tokens: {inp:,}&rarr;{out:,}")
                        if cache_r:
                            parts.append(f"cache read: {cache_r:,}")
                        f.write(f'        <div class="msg-metadata">{" | ".join(parts)}</div>\n')
                    f.write(f'        <div class="content">{content}</div>\n')
                elif role == "thinking":
                    f.write('        <details>\n')
                    f.write("            <summary>Claude's reasoning</summary>\n")
                    f.write(f'            <div class="content">{content}</div>\n')
                    f.write('        </details>\n')
                elif role == "subagent":
                    desc = msg.get("description", "Subagent task")
                    agent_id = msg.get("agent_id", "unknown")
                    model_name = msg.get("model", "unknown")
                    agent_type = msg.get("subagent_type", "")
                    info_parts = [f"Agent: {agent_id}", f"Model: {model_name}"]
                    if agent_type:
                        info_parts.append(f"Type: {agent_type}")
                    f.write(f'        <div class="subagent-info">{desc} &mdash; {" | ".join(info_parts)}</div>\n')
                    for sub_msg in msg.get("messages", []):
                        sub_role = sub_msg.get("role", "")
                        sub_content = sub_msg.get("content", "")
                        if isinstance(sub_content, str):
                            sub_content = sub_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        if sub_role == "user":
                            f.write(f'        <div class="subagent-message"><strong>User:</strong> {sub_content}</div>\n')
                        elif sub_role == "assistant":
                            f.write(f'        <div class="subagent-message"><strong>Claude:</strong> {sub_content}</div>\n')
                        elif sub_role == "thinking":
                            f.write(f'        <div class="subagent-message"><details><summary>Reasoning</summary>{sub_content}</details></div>\n')
                elif role == "stats":
                    stats = msg.get("content", {})
                    if isinstance(stats, dict):
                        f.write('        <table class="stats-table">\n')
                        f.write('            <tr><th>Metric</th><th>Value</th></tr>\n')
                        models = ", ".join(stats.get("models_used", []))
                        f.write(f'            <tr><td>Models</td><td>{models}</td></tr>\n')
                        f.write(f'            <tr><td>User turns</td><td>{stats.get("turn_count", 0)}</td></tr>\n')
                        f.write(f'            <tr><td>Tool invocations</td><td>{stats.get("tool_use_count", 0)}</td></tr>\n')
                        f.write(f'            <tr><td>Subagents spawned</td><td>{stats.get("subagent_count", 0)}</td></tr>\n')
                        f.write(f'            <tr><td>Total input tokens</td><td>{stats.get("total_input_tokens", 0):,}</td></tr>\n')
                        f.write(f'            <tr><td>Total output tokens</td><td>{stats.get("total_output_tokens", 0):,}</td></tr>\n')
                        cache_t = stats.get("total_cache_read_tokens", 0)
                        if cache_t:
                            f.write(f'            <tr><td>Cache read tokens</td><td>{cache_t:,}</td></tr>\n')
                        duration_ms = stats.get("total_duration_ms", 0)
                        if duration_ms:
                            mins = duration_ms // 60000
                            secs = (duration_ms % 60000) / 1000
                            f.write(f'            <tr><td>Total duration</td><td>{mins}m {secs:.0f}s</td></tr>\n')
                        ver = stats.get("session_version", "")
                        if ver:
                            f.write(f'            <tr><td>Claude Code version</td><td>{ver}</td></tr>\n')
                        branch = stats.get("git_branch", "")
                        if branch:
                            f.write(f'            <tr><td>Git branch</td><td>{branch}</td></tr>\n')
                        f.write('        </table>\n')
                        tools = stats.get("tools_used", {})
                        if tools:
                            f.write('        <div><strong>Tools breakdown:</strong><ul>\n')
                            for tool_name, count in sorted(tools.items(), key=lambda x: -x[1]):
                                f.write(f'            <li>{tool_name}: {count}</li>\n')
                            f.write('        </ul></div>\n')
                else:
                    f.write(f'        <div class="content">{content}</div>\n')

                f.write(f'    </div>\n')
            
            f.write("\n</body>\n</html>")

        return output_path

    def save_bash_commands_as_markdown(
        self, bash_commands: List[Dict], session_id: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save extracted bash commands as a markdown file.

        Args:
            bash_commands: List of bash command dicts with command, context, timestamp
            session_id: Session identifier
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        if not bash_commands:
            return None

        # Get timestamp from first command
        first_timestamp = bash_commands[0].get("timestamp", "")
        if first_timestamp:
            try:
                dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H_%M")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H_%M")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H_%M")

        filename = f"{date_str}-{time_str}-{session_id[:8]}-bash.md"

        # Determine output directory
        output_dir = self._get_output_dir(date_str, by_day, by_project, project_name)
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Bash Commands Log\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Date: {date_str}")
            if time_str:
                f.write(f" {time_str}")
            f.write(f"\n\nTotal commands: {len(bash_commands)}\n\n")
            f.write("---\n\n")

            for i, cmd in enumerate(bash_commands, 1):
                command = cmd.get("command", "")
                context = cmd.get("context", "")

                # Write context (assistant's commentary) if available
                if context:
                    f.write(f"{context}\n\n")

                # Write the command in a bash code block
                f.write("```bash\n")
                f.write(f"{command}\n")
                f.write("```\n\n")

                # Add separator between commands (except for the last one)
                if i < len(bash_commands):
                    f.write("---\n\n")

        return output_path

    def save_tool_operations_as_markdown(
        self, tool_ops: Dict, session_id: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save extracted tool operations as a markdown file.

        Args:
            tool_ops: Dictionary of tool operations by category
            session_id: Session identifier
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        # Count total operations
        total_ops = 0
        category_counts = {}

        for category, data in tool_ops.items():
            if category == "git":
                count = len(data) if isinstance(data, list) else 0
                category_counts["git"] = count
                total_ops += count
            else:
                cat_count = 0
                tool_counts = {}
                for tool_name, ops_list in data.items():
                    tool_counts[tool_name] = len(ops_list)
                    cat_count += len(ops_list)
                category_counts[category] = {"total": cat_count, "tools": tool_counts}
                total_ops += cat_count

        if total_ops == 0:
            return None

        # Get timestamp from first operation
        first_timestamp = None
        for category, data in tool_ops.items():
            if category == "git" and data:
                first_timestamp = data[0].get("timestamp", "")
                break
            elif isinstance(data, dict):
                for tool_name, ops_list in data.items():
                    if ops_list:
                        first_timestamp = ops_list[0].get("timestamp", "")
                        break
                if first_timestamp:
                    break

        if first_timestamp:
            try:
                dt = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H_%M")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H_%M")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H_%M")

        filename = f"{date_str}-{time_str}-{session_id[:8]}-tools.md"

        # Determine output directory
        output_dir = self._get_output_dir(date_str, by_day, by_project, project_name)
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Tool Operations Log\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Date: {date_str}")
            if time_str:
                f.write(f" {time_str}")
            f.write("\n")
            if project_name:
                f.write(f"Project: {project_name}\n")
            f.write("\n")

            # Write summary
            f.write("## Summary\n\n")
            f.write(f"Total operations: {total_ops}\n\n")

            # File operations
            if "file" in category_counts and category_counts["file"]["total"] > 0:
                tools_str = ", ".join(
                    f"{t}: {c}" for t, c in category_counts["file"]["tools"].items() if c > 0
                )
                f.write(f"- File Operations: {category_counts['file']['total']} ({tools_str})\n")

            # Search operations
            if "search" in category_counts and category_counts["search"]["total"] > 0:
                tools_str = ", ".join(
                    f"{t}: {c}" for t, c in category_counts["search"]["tools"].items() if c > 0
                )
                f.write(f"- Search Operations: {category_counts['search']['total']} ({tools_str})\n")

            # Web operations
            if "web" in category_counts and category_counts["web"]["total"] > 0:
                tools_str = ", ".join(
                    f"{t}: {c}" for t, c in category_counts["web"]["tools"].items() if c > 0
                )
                f.write(f"- Web Operations: {category_counts['web']['total']} ({tools_str})\n")

            # Git operations
            if "git" in category_counts and category_counts["git"] > 0:
                f.write(f"- Git Operations: {category_counts['git']}\n")

            f.write("\n---\n\n")

            # Write File Operations section
            file_ops = tool_ops.get("file", {})
            has_file_ops = any(ops for ops in file_ops.values())
            if has_file_ops:
                f.write("## File Operations\n\n")

                for tool_name in ["Read", "Write", "Edit"]:
                    ops_list = file_ops.get(tool_name, [])
                    if ops_list:
                        f.write(f"### {tool_name}\n\n")
                        for i, op in enumerate(ops_list, 1):
                            file_path = op.get("input", {}).get("file_path", "Unknown")
                            f.write(f"#### {i}. `{file_path}`\n\n")

                            context = op.get("context", "")
                            if context:
                                f.write(f"{context}\n\n")

                            result = op.get("result", {})
                            if tool_name == "Read":
                                if "lines" in result:
                                    f.write(f"- **Lines:** {result.get('lines', 0)}\n")
                                size_kb = result.get("size_bytes", 0) / 1024
                                f.write(f"- **Status:** {'Success' if result.get('success') else 'Failed'} ({size_kb:.1f} KB)\n")
                            else:
                                f.write(f"- **Status:** {result.get('status', 'Unknown')}\n")

                            if result.get("error"):
                                f.write(f"- **Error:** {result['error']}\n")

                            f.write("\n---\n\n")

            # Write Search Operations section
            search_ops = tool_ops.get("search", {})
            has_search_ops = any(ops for ops in search_ops.values())
            if has_search_ops:
                f.write("## Search Operations\n\n")

                for tool_name in ["Grep", "Glob"]:
                    ops_list = search_ops.get(tool_name, [])
                    if ops_list:
                        f.write(f"### {tool_name}\n\n")
                        for i, op in enumerate(ops_list, 1):
                            inp = op.get("input", {})
                            pattern = inp.get("pattern", "")
                            path = inp.get("path", ".")

                            f.write(f"#### {i}. Pattern: `{pattern}`\n\n")

                            context = op.get("context", "")
                            if context:
                                f.write(f"{context}\n\n")

                            f.write(f"- **Path:** `{path}`\n")

                            result = op.get("result", {})
                            if "matched_count" in result:
                                f.write(f"- **Matched:** {result['matched_count']} files\n")
                                preview = result.get("matches_preview", [])
                                if preview:
                                    f.write("- **Preview:**\n")
                                    for match in preview[:5]:
                                        f.write(f"  - `{match}`\n")

                            if result.get("error"):
                                f.write(f"- **Error:** {result['error']}\n")

                            f.write("\n---\n\n")

            # Write Web Operations section
            web_ops = tool_ops.get("web", {})
            has_web_ops = any(ops for ops in web_ops.values())
            if has_web_ops:
                f.write("## Web Operations\n\n")

                for tool_name in ["WebFetch", "WebSearch"]:
                    ops_list = web_ops.get(tool_name, [])
                    if ops_list:
                        f.write(f"### {tool_name}\n\n")
                        for i, op in enumerate(ops_list, 1):
                            inp = op.get("input", {})

                            if tool_name == "WebFetch":
                                url = inp.get("url", "Unknown URL")
                                f.write(f"#### {i}. URL: `{url}`\n\n")
                            else:
                                query = inp.get("query", "Unknown query")
                                f.write(f'#### {i}. Query: "{query}"\n\n')

                            context = op.get("context", "")
                            if context:
                                f.write(f"{context}\n\n")

                            result = op.get("result", {})
                            f.write(f"- **Status:** {'Success' if result.get('success') else 'Failed'}\n")

                            preview = result.get("preview", "")
                            if preview:
                                f.write(f"- **Preview:** {preview[:200]}...\n")

                            if result.get("error"):
                                f.write(f"- **Error:** {result['error']}\n")

                            f.write("\n---\n\n")

            # Write Git Operations section
            git_ops = tool_ops.get("git", [])
            if git_ops:
                f.write("## Git Operations\n\n")

                for i, op in enumerate(git_ops, 1):
                    command = op.get("input", {}).get("command", "")
                    f.write(f"#### {i}. `{command}`\n\n")

                    context = op.get("context", "")
                    if context:
                        f.write(f"{context}\n\n")

                    result = op.get("result", {})
                    output_preview = result.get("output_preview", "")
                    if output_preview:
                        f.write("```\n")
                        f.write(f"{output_preview}\n")
                        f.write("```\n\n")

                    if result.get("error"):
                        f.write(f"**Error:** {result['error']}\n\n")

                    f.write("---\n\n")

        return output_path

    def save_conversation(
        self, conversation: List[Dict[str, str]], session_id: str,
        format: str = "markdown", by_day: bool = False,
        by_project: bool = False, project_name: Optional[str] = None
    ) -> Optional[Path]:
        """Save conversation in the specified format.

        Args:
            conversation: The conversation data
            session_id: Session identifier
            format: Output format ('markdown', 'json', 'html')
            by_day: If True, save to a date-based subdirectory (YYYY-MM-DD)
            by_project: If True, save to a project-based subdirectory
            project_name: Name of the project (extracted from session path)
        """
        if format == "markdown":
            return self.save_as_markdown(
                conversation, session_id, by_day=by_day,
                by_project=by_project, project_name=project_name
            )
        elif format == "json":
            return self.save_as_json(
                conversation, session_id, by_day=by_day,
                by_project=by_project, project_name=project_name
            )
        elif format == "html":
            return self.save_as_html(
                conversation, session_id, by_day=by_day,
                by_project=by_project, project_name=project_name
            )
        else:
            print(f"❌ Unsupported format: {format}")
            return None

    def get_conversation_preview(self, session_path: Path) -> Tuple[str, int]:
        """Get a preview of the conversation's first real user message and message count."""
        try:
            first_user_msg = ""
            msg_count = 0
            
            with open(session_path, 'r', encoding='utf-8') as f:
                for line in f:
                    msg_count += 1
                    if not first_user_msg:
                        try:
                            data = json.loads(line)
                            # Check for user message
                            if data.get("type") == "user" and "message" in data:
                                msg = data["message"]
                                if msg.get("role") == "user":
                                    content = msg.get("content", "")
                                    
                                    # Handle list content (common format in Claude JSONL)
                                    if isinstance(content, list):
                                        for item in content:
                                            if isinstance(item, dict) and item.get("type") == "text":
                                                text = item.get("text", "").strip()
                                                
                                                # Skip tool results
                                                if text.startswith("tool_use_id"):
                                                    continue
                                                
                                                # Skip interruption messages
                                                if "[Request interrupted" in text:
                                                    continue
                                                
                                                # Skip Claude's session continuation messages
                                                if "session is being continued" in text.lower():
                                                    continue
                                                
                                                # Remove XML-like tags (command messages, etc)
                                                import re
                                                text = re.sub(r'<[^>]+>', '', text).strip()
                                                
                                                # Skip command outputs  
                                                if "is running" in text and "…" in text:
                                                    continue
                                                
                                                # Handle image references - extract text after them
                                                if text.startswith("[Image #"):
                                                    parts = text.split("]", 1)
                                                    if len(parts) > 1:
                                                        text = parts[1].strip()
                                                
                                                # If we have real user text, use it
                                                if text and len(text) > 3:  # Lower threshold to catch "hello"
                                                    first_user_msg = text[:100].replace('\n', ' ')
                                                    break
                                    
                                    # Handle string content (less common but possible)
                                    elif isinstance(content, str):
                                        import re
                                        content = content.strip()
                                        
                                        # Remove XML-like tags
                                        content = re.sub(r'<[^>]+>', '', content).strip()
                                        
                                        # Skip command outputs
                                        if "is running" in content and "…" in content:
                                            continue
                                        
                                        # Skip Claude's session continuation messages
                                        if "session is being continued" in content.lower():
                                            continue
                                        
                                        # Skip tool results and interruptions
                                        if not content.startswith("tool_use_id") and "[Request interrupted" not in content:
                                            if content and len(content) > 3:  # Lower threshold to catch short messages
                                                first_user_msg = content[:100].replace('\n', ' ')
                        except json.JSONDecodeError:
                            continue
                            
            return first_user_msg or "No preview available", msg_count
        except Exception as e:
            return f"Error: {str(e)[:30]}", 0

    def list_recent_sessions(self, limit: int = None) -> List[Path]:
        """List recent sessions with details."""
        sessions = self.find_sessions()

        if not sessions:
            print("❌ No Claude sessions found in ~/.claude/projects/")
            print("💡 Make sure you've used Claude Code and have conversations saved.")
            return []

        print(f"\n📚 Found {len(sessions)} Claude sessions:\n")
        print("=" * 80)

        # Show all sessions if no limit specified
        sessions_to_show = sessions[:limit] if limit else sessions
        for i, session in enumerate(sessions_to_show, 1):
            # Clean up project name (remove hyphens, make readable)
            project = session.parent.name.replace('-', ' ').strip()
            if project.startswith("Users"):
                project = "~/" + "/".join(project.split()[2:]) if len(project.split()) > 2 else "Home"
            
            session_id = session.stem
            modified = datetime.fromtimestamp(session.stat().st_mtime)

            # Get file size
            size = session.stat().st_size
            size_kb = size / 1024
            
            # Get preview and message count
            preview, msg_count = self.get_conversation_preview(session)

            # Print formatted info
            print(f"\n{i}. 📁 {project}")
            print(f"   📄 Session: {session_id[:8]}...")
            print(f"   📅 Modified: {modified.strftime('%Y-%m-%d %H:%M')}")
            print(f"   💬 Messages: {msg_count}")
            print(f"   💾 Size: {size_kb:.1f} KB")
            print(f"   📝 Preview: \"{preview}...\"")

        print("\n" + "=" * 80)
        return sessions[:limit]

    def _get_project_name(self, session_path: Path) -> str:
        """Extract a clean project name from the session path.

        The session files are in ~/.claude/projects/<project-path-encoded>/
        This extracts and cleans the project folder name.
        """
        project_folder = session_path.parent.name
        # Clean up the folder name (it may be URL-encoded or have special chars)
        # Replace common path separators with underscores
        project_name = project_folder.replace('-', '_').replace('%', '_')
        # Limit length and clean up
        if len(project_name) > 50:
            project_name = project_name[:50]
        return project_name or "unknown_project"

    def _get_output_file_path(
        self, session_id: str, date_str: str, format: str,
        by_day: bool = False, by_project: bool = False, project_name: Optional[str] = None
    ) -> Path:
        """Get the full output file path without creating directories.

        Since filenames include time (which we don't know without reading the file),
        this method checks for any matching file using a glob pattern.

        Args:
            session_id: Session identifier
            date_str: Date string in YYYY-MM-DD format
            format: Output format ('markdown', 'json', 'html')
            by_day: If True, include date in path
            by_project: If True, include project name in path
            project_name: Name of the project

        Returns:
            Path to existing file if found, otherwise a placeholder path that won't exist
        """
        # Determine file extension
        ext_map = {"markdown": "md", "json": "json", "html": "html"}
        ext = ext_map.get(format, "md")

        # Get output directory (without creating it)
        output_dir = self._get_output_dir(
            date_str, by_day=by_day, by_project=by_project,
            project_name=project_name, create=False
        )

        # Check for existing files matching the pattern (date-time-sessionid.ext)
        # Pattern: YYYY-MM-DD-HH_MM-{session_id[:8]}.{ext}
        pattern = f"{date_str}-*-{session_id[:8]}.{ext}"
        if output_dir.exists():
            matches = list(output_dir.glob(pattern))
            if matches:
                return matches[0]  # Return first match

        # Return a placeholder path that won't exist
        return output_dir / f"{date_str}-00_00-{session_id[:8]}.{ext}"

    def extract_multiple(
        self, sessions: List[Path], indices: List[int],
        format: str = "markdown", detailed: bool = False,
        by_day: bool = False, by_project: bool = False,
        overwrite: bool = False, include_thinking: bool = False
    ) -> Tuple[int, int]:
        """Extract multiple sessions by index.

        Args:
            sessions: List of session paths
            indices: Indices to extract
            format: Output format ('markdown', 'json', 'html')
            detailed: If True, include tool use and system messages
            by_day: If True, save to date-based subdirectories (YYYY-MM-DD)
            by_project: If True, save to project-based subdirectories
            overwrite: If True, overwrite existing files; if False (default), skip them
            include_thinking: If True, include Claude's thinking/reasoning blocks
        """
        success = 0
        skipped = 0
        total = len(indices)

        for idx in indices:
            if 0 <= idx < len(sessions):
                session_path = sessions[idx]

                # Check if file exists and skip unless overwrite is set
                if not overwrite:
                    project_name = self._get_project_name(session_path) if by_project else None
                    date_str = self._get_date_from_session(session_path)

                    # Get the full output file path
                    output_file = self._get_output_file_path(
                        session_path.stem, date_str, format,
                        by_day=by_day, by_project=by_project, project_name=project_name
                    )

                    if output_file.exists():
                        skipped += 1
                        try:
                            rel_path = output_file.relative_to(self.output_dir)
                        except ValueError:
                            rel_path = output_file.name
                        print(f"⏭️  Skipped: {rel_path} (already exists)")
                        continue

                conversation = self.extract_conversation(
                    session_path, detailed=detailed,
                    include_thinking=include_thinking
                )
                if conversation:
                    # Extract project name from path if needed
                    project_name = self._get_project_name(session_path) if by_project else None

                    output_path = self.save_conversation(
                        conversation, session_path.stem, format=format,
                        by_day=by_day, by_project=by_project, project_name=project_name
                    )
                    success += 1
                    msg_count = len(conversation)
                    print(
                        f"✅ {success}/{total - skipped}: {output_path.name} "
                        f"({msg_count} messages)"
                    )
                else:
                    print(f"⏭️  Skipped session {idx + 1} (no conversation)")
            else:
                print(f"❌ Invalid session number: {idx + 1}")

        return success, total

    def extract_bash_commands_multiple(
        self, sessions: List[Path], indices: List[int],
        by_day: bool = False, by_project: bool = False,
        overwrite: bool = False
    ) -> Tuple[int, int]:
        """Extract bash commands from multiple sessions by index.

        Args:
            sessions: List of session paths
            indices: Indices to extract
            by_day: If True, save to date-based subdirectories (YYYY-MM-DD)
            by_project: If True, save to project-based subdirectories
            overwrite: If True, overwrite existing files; if False (default), skip them
        """
        success = 0
        skipped = 0
        total = len(indices)
        total_commands = 0

        for idx in indices:
            if 0 <= idx < len(sessions):
                session_path = sessions[idx]

                # Check if file exists and skip unless overwrite is set
                if not overwrite:
                    project_name = self._get_project_name(session_path) if by_project else None
                    date_str = self._get_date_from_session(session_path)

                    # Get the expected output file path
                    output_dir = self._get_output_dir(
                        date_str, by_day=by_day, by_project=by_project,
                        project_name=project_name, create=False
                    )
                    output_file = output_dir / f"bash-commands-{date_str}-{session_path.stem[:8]}.md"

                    if output_file.exists():
                        skipped += 1
                        try:
                            rel_path = output_file.relative_to(self.output_dir)
                        except ValueError:
                            rel_path = output_file.name
                        print(f"⏭️  Skipped: {rel_path} (already exists)")
                        continue

                bash_commands = self.extract_bash_commands(session_path)
                if bash_commands:
                    # Extract project name from path if needed
                    project_name = self._get_project_name(session_path) if by_project else None

                    output_path = self.save_bash_commands_as_markdown(
                        bash_commands, session_path.stem,
                        by_day=by_day, by_project=by_project, project_name=project_name
                    )
                    success += 1
                    cmd_count = len(bash_commands)
                    total_commands += cmd_count
                    print(
                        f"✅ {success}/{total - skipped}: {output_path.name} "
                        f"({cmd_count} commands)"
                    )
                else:
                    print(f"⏭️  Skipped session {idx + 1} (no bash commands)")
            else:
                print(f"❌ Invalid session number: {idx + 1}")

        return success, total_commands

    def extract_tool_operations_multiple(
        self, sessions: List[Path], indices: List[int],
        tool_filter: Optional[List[str]] = None,
        detailed: bool = False,
        by_day: bool = False, by_project: bool = False,
        overwrite: bool = False
    ) -> Tuple[int, int]:
        """Extract tool operations from multiple sessions by index.

        Args:
            sessions: List of session paths
            indices: Indices to extract
            tool_filter: Optional list of tool categories or tool names to include
            detailed: If True, include full tool results
            by_day: If True, save to date-based subdirectories
            by_project: If True, save to project-based subdirectories
            overwrite: If True, overwrite existing files; if False (default), skip them

        Returns:
            Tuple of (successful_sessions, total_operations)
        """
        success = 0
        skipped = 0
        total = len(indices)
        total_operations = 0

        for idx in indices:
            if 0 <= idx < len(sessions):
                session_path = sessions[idx]

                # Check if file exists and skip unless overwrite is set
                if not overwrite:
                    project_name = self._get_project_name(session_path) if by_project else None
                    date_str = self._get_date_from_session(session_path)

                    # Get the expected output file path
                    output_dir = self._get_output_dir(
                        date_str, by_day=by_day, by_project=by_project,
                        project_name=project_name, create=False
                    )
                    output_file = output_dir / f"tool-operations-{date_str}-{session_path.stem[:8]}.md"

                    if output_file.exists():
                        skipped += 1
                        try:
                            rel_path = output_file.relative_to(self.output_dir)
                        except ValueError:
                            rel_path = output_file.name
                        print(f"⏭️  Skipped: {rel_path} (already exists)")
                        continue

                tool_ops = self.extract_tool_operations(
                    session_path, tool_filter=tool_filter, detailed=detailed
                )

                # Count operations
                op_count = 0
                for category, data in tool_ops.items():
                    if category == "git":
                        op_count += len(data) if isinstance(data, list) else 0
                    else:
                        for tool_name, ops_list in data.items():
                            op_count += len(ops_list)

                if op_count > 0:
                    # Extract project name from path if needed
                    project_name = self._get_project_name(session_path) if by_project else None

                    output_path = self.save_tool_operations_as_markdown(
                        tool_ops, session_path.stem,
                        by_day=by_day, by_project=by_project, project_name=project_name
                    )
                    if output_path:
                        success += 1
                        total_operations += op_count
                        print(
                            f"✅ {success}/{total - skipped}: {output_path.name} "
                            f"({op_count} operations)"
                        )
                else:
                    print(f"⏭️  Skipped session {idx + 1} (no tool operations)")
            else:
                print(f"❌ Invalid session number: {idx + 1}")

        return success, total_operations


def main():
    parser = argparse.ArgumentParser(
        description="Extract Claude Code conversations to clean markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                    # List all available sessions
  %(prog)s --extract 1               # Extract the most recent session
  %(prog)s --extract 1,3,5           # Extract specific sessions
  %(prog)s --recent 5                # Extract 5 most recent sessions
  %(prog)s --all                     # Extract all sessions
  %(prog)s --output ~/my-logs        # Specify output directory
  %(prog)s --search "python error"   # Search conversations
  %(prog)s --search-regex "import.*" # Search with regex
  %(prog)s --format json --all       # Export all as JSON
  %(prog)s --format html --extract 1 # Export session 1 as HTML
  %(prog)s --detailed --extract 1    # Include tool use & system messages
  %(prog)s --by-day --all            # Organize exports into date folders
  %(prog)s --by-project --all        # Organize exports into project folders
  %(prog)s --by-project --by-day --all  # project/date hierarchy
  %(prog)s --by-day --skip-existing --all  # skip already extracted dates
  %(prog)s --bash-commands --extract 1    # Extract bash commands from session 1
  %(prog)s --bash-commands --all          # Extract bash commands from all sessions
  %(prog)s --tool-ops --all               # Extract all tool operations
  %(prog)s --tool-ops --tool-filter file --all  # Extract only file operations
  %(prog)s --tool-ops --tool-filter Grep,Glob --extract 1  # Extract search ops
  %(prog)s --overwrite --all              # Overwrite existing files
  %(prog)s --from-date 2025-01-01 --all   # Extract sessions from Jan 1, 2025
  %(prog)s --to-date 2025-01-31 --all     # Extract sessions up to Jan 31, 2025
  %(prog)s --from-date 2025-01-01 --to-date 2025-01-31 --all  # Date range
  %(prog)s --list-projects             # List all projects
  %(prog)s --project 1 --all           # Extract all sessions from project 1
  %(prog)s --project 1,3 --recent 5    # Extract recent from multiple projects
  %(prog)s --session-id 8fd830ec       # Extract session by ID (partial or full)
  %(prog)s --session-id 8fd830ec-ec03-4c6c-8d63-a23976a2ce97  # Full UUID
  %(prog)s --bash-commands --session-id 8fd830ec  # Extract bash commands by session ID
        """,
    )
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    parser.add_argument("--list-projects", action="store_true", help="List all projects")
    parser.add_argument(
        "--project",
        type=str,
        help="Extract from specific project(s) by number (comma-separated)"
    )
    parser.add_argument(
        "--extract",
        type=str,
        help="Extract specific session(s) by number (comma-separated)",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Extract session by ID (full UUID or partial prefix)",
    )
    parser.add_argument(
        "--all", "--logs", action="store_true", help="Extract all sessions"
    )
    parser.add_argument(
        "--recent", type=int, help="Extract N most recent sessions", default=0
    )
    parser.add_argument(
        "--output", type=str, help="Output directory for markdown files"
    )
    parser.add_argument(
        "--limit", type=int, help="Limit for --list command (default: show all)", default=None
    )
    parser.add_argument(
        "--interactive",
        "-i",
        "--start",
        "-s",
        action="store_true",
        help="Launch interactive UI for easy extraction",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export mode: 'logs' for interactive UI",
    )

    # Search arguments
    parser.add_argument(
        "--search", type=str, help="Search conversations for text (smart search)"
    )
    parser.add_argument(
        "--search-regex", type=str, help="Search conversations using regex pattern"
    )
    parser.add_argument(
        "--search-date-from", type=str, help="Filter search from date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--search-date-to", type=str, help="Filter search to date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--search-speaker",
        choices=["human", "assistant", "both"],
        default="both",
        help="Filter search by speaker",
    )
    parser.add_argument(
        "--case-sensitive", action="store_true", help="Make search case-sensitive"
    )
    
    # Export format arguments
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format for exported conversations (default: markdown)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include tool use, MCP responses, and system messages in export"
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Include Claude's thinking/reasoning blocks in output"
    )
    parser.add_argument(
        "--by-day",
        action="store_true",
        help="Organize extracted conversations into date folders (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--by-project",
        action="store_true",
        help="Organize extracted conversations into project folders"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip existing files (default behavior, kept for backwards compatibility)"
    )
    parser.add_argument(
        "--bash-commands",
        action="store_true",
        help="Extract only successful bash commands with context (instead of full conversation)"
    )
    parser.add_argument(
        "--tool-ops",
        action="store_true",
        help="Extract tool operations (Read, Write, Edit, Grep, Glob, WebFetch, WebSearch, Git)"
    )
    parser.add_argument(
        "--tool-filter",
        type=str,
        help="Filter tool operations by category or name (comma-separated). "
             "Categories: file, search, web, git. "
             "Tools: Read, Write, Edit, Grep, Glob, WebFetch, WebSearch. "
             "Example: --tool-filter file,Grep"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files instead of skipping them"
    )
    parser.add_argument(
        "--from-date",
        type=str,
        help="Only extract sessions from this date onwards (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to-date",
        type=str,
        help="Only extract sessions up to this date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Check for mutually exclusive options
    if args.skip_existing and args.overwrite:
        print("❌ Error: --skip-existing and --overwrite are mutually exclusive")
        return

    # Parse date filters
    from_date = None
    to_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format for --from-date: {args.from_date} (use YYYY-MM-DD)")
            return

    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format for --to-date: {args.to_date} (use YYYY-MM-DD)")
            return

    # Validate date range
    if from_date and to_date and from_date > to_date:
        print("❌ Error: --from-date cannot be after --to-date")
        return

    # Handle interactive mode
    if args.interactive or (args.export and args.export.lower() == "logs"):
        from interactive_ui import main as interactive_main

        interactive_main()
        return

    # Initialize extractor with optional output directory
    extractor = ClaudeConversationExtractor(args.output)

    # Handle --list-projects
    if args.list_projects:
        extractor.list_projects()
        return

    # Parse project filter
    project_indices = []
    projects = None
    if args.project:
        projects = extractor.find_projects()
        if not projects:
            print("❌ No projects found")
            return

        for num in args.project.split(","):
            try:
                idx = int(num.strip()) - 1  # Convert to 0-based index
                if 0 <= idx < len(projects):
                    project_indices.append(idx)
                else:
                    print(f"❌ Invalid project number: {num} (valid: 1-{len(projects)})")
                    return
            except ValueError:
                print(f"❌ Invalid project number: {num}")
                return

        # Show which projects are selected
        print(f"📁 Extracting from {len(project_indices)} project(s):")
        for idx in project_indices:
            project_name = projects[idx].name.replace('-', ' ').strip()
            print(f"   - {project_name}")

    # Handle search mode
    if args.search or args.search_regex:
        from search_conversations import ConversationSearcher

        searcher = ConversationSearcher()

        # Determine search mode and query
        if args.search_regex:
            query = args.search_regex
            mode = "regex"
        else:
            query = args.search
            mode = "smart"

        # Parse date filters
        date_from = None
        date_to = None
        if args.search_date_from:
            try:
                date_from = datetime.strptime(args.search_date_from, "%Y-%m-%d")
            except ValueError:
                print(f"❌ Invalid date format: {args.search_date_from}")
                return

        if args.search_date_to:
            try:
                date_to = datetime.strptime(args.search_date_to, "%Y-%m-%d")
            except ValueError:
                print(f"❌ Invalid date format: {args.search_date_to}")
                return

        # Speaker filter
        speaker_filter = None if args.search_speaker == "both" else args.search_speaker

        # Perform search
        print(f"🔍 Searching for: {query}")
        results = searcher.search(
            query=query,
            mode=mode,
            date_from=date_from,
            date_to=date_to,
            speaker_filter=speaker_filter,
            case_sensitive=args.case_sensitive,
            max_results=30,
        )

        if not results:
            print("❌ No matches found.")
            return

        print(f"\n✅ Found {len(results)} matches across conversations:")

        # Group and display results
        results_by_file = {}
        for result in results:
            if result.file_path not in results_by_file:
                results_by_file[result.file_path] = []
            results_by_file[result.file_path].append(result)

        # Store file paths for potential viewing
        file_paths_list = []
        for file_path, file_results in results_by_file.items():
            file_paths_list.append(file_path)
            print(f"\n{len(file_paths_list)}. 📄 {file_path.parent.name} ({len(file_results)} matches)")
            # Show first match preview
            first = file_results[0]
            print(f"   {first.speaker}: {first.matched_content[:100]}...")

        # Offer to view conversations
        if file_paths_list:
            print("\n" + "=" * 60)
            try:
                view_choice = input("\nView a conversation? Enter number (1-{}) or press Enter to skip: ".format(
                    len(file_paths_list))).strip()
                
                if view_choice.isdigit():
                    view_num = int(view_choice)
                    if 1 <= view_num <= len(file_paths_list):
                        selected_path = file_paths_list[view_num - 1]
                        extractor.display_conversation(selected_path, detailed=args.detailed)
                        
                        # Offer to extract after viewing
                        extract_choice = input("\n📤 Extract this conversation? (y/N): ").strip().lower()
                        if extract_choice == 'y':
                            conversation = extractor.extract_conversation(
                                selected_path, detailed=args.detailed,
                                include_thinking=args.thinking
                            )
                            if conversation:
                                session_id = selected_path.stem
                                if args.format == "json":
                                    output = extractor.save_as_json(conversation, session_id)
                                elif args.format == "html":
                                    output = extractor.save_as_html(conversation, session_id)
                                else:
                                    output = extractor.save_as_markdown(conversation, session_id)
                                print(f"✅ Saved: {output.name}")
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Cancelled")
        
        return

    # Default action is to list sessions
    if args.list or (
        not args.extract
        and not args.session_id
        and not args.all
        and not args.recent
        and not args.search
        and not args.search_regex
    ):
        sessions = extractor.list_recent_sessions(args.limit)

        if sessions and not args.list:
            print("\nTo extract conversations:")
            print("  claude-extract --extract <number>      # Extract specific session")
            print("  claude-extract --session-id <id>       # Extract session by ID")
            print("  claude-extract --recent 5              # Extract 5 most recent")
            print("  claude-extract --all                   # Extract all sessions")

    elif args.session_id:
        # Find session by ID
        session_path = extractor.find_session_by_id(args.session_id)
        if not session_path:
            print(f"❌ No session found matching ID: {args.session_id}")
            return

        session_id = session_path.stem
        project_name = session_path.parent.name if args.by_project else None
        print(f"📄 Found session: {session_id}")

        if args.bash_commands:
            print(f"\n📤 Extracting bash commands...")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")

            bash_commands = extractor.extract_bash_commands(session_path)
            if bash_commands:
                output = extractor.save_bash_commands_as_markdown(
                    bash_commands, session_id,
                    by_day=args.by_day, by_project=args.by_project,
                    project_name=project_name
                )
                if output:
                    print(f"✅ Saved {len(bash_commands)} commands to: {output.name}")
            else:
                print("⚠️  No bash commands found in this session")

        elif args.tool_ops:
            # Parse tool filter
            tool_filter = None
            if args.tool_filter:
                tool_filter = [t.strip() for t in args.tool_filter.split(",")]

            print(f"\n📤 Extracting tool operations...")
            if tool_filter:
                print(f"🔧 Filter: {', '.join(tool_filter)}")
            if args.detailed:
                print("📋 Including detailed results")

            tool_ops = extractor.extract_tool_operations(
                session_path, tool_filter=tool_filter, detailed=args.detailed
            )
            if tool_ops and any(tool_ops.values()):
                output = extractor.save_tool_operations_as_markdown(
                    tool_ops, session_id,
                    by_day=args.by_day, by_project=args.by_project,
                    project_name=project_name
                )
                if output:
                    total = sum(len(ops) for ops in tool_ops.values())
                    print(f"✅ Saved {total} operations to: {output.name}")
            else:
                print("⚠️  No tool operations found in this session")

        else:
            print(f"\n📤 Extracting conversation as {args.format.upper()}...")
            if args.detailed:
                print("📋 Including detailed tool use and system messages")

            conversation = extractor.extract_conversation(
                session_path, detailed=args.detailed,
                include_thinking=args.thinking
            )
            if conversation:
                output = extractor.save_conversation(
                    conversation, session_id,
                    format=args.format,
                    by_day=args.by_day, by_project=args.by_project,
                    project_name=project_name
                )
                if output:
                    print(f"✅ Saved to: {output.name}")
            else:
                print("⚠️  No conversation found in this session")

    elif args.extract:
        sessions = extractor.find_sessions()

        # Parse comma-separated indices
        indices = []
        for num in args.extract.split(","):
            try:
                idx = int(num.strip()) - 1  # Convert to 0-based index
                indices.append(idx)
            except ValueError:
                print(f"❌ Invalid session number: {num}")
                continue

        if indices:
            if args.bash_commands:
                print(f"\n📤 Extracting bash commands from {len(indices)} session(s)...")
                if args.by_project:
                    print("📂 Organizing by project folders")
                if args.by_day:
                    print("📅 Organizing by date folders")
                if args.overwrite:
                    print("🔄 Overwriting existing files")
                success, total_cmds = extractor.extract_bash_commands_multiple(
                    sessions, indices,
                    by_day=args.by_day, by_project=args.by_project,
                    overwrite=args.overwrite
                )
                print(f"\n✅ Successfully extracted {total_cmds} commands from {success} sessions")
            elif args.tool_ops:
                # Parse tool filter
                tool_filter = None
                if args.tool_filter:
                    tool_filter = [t.strip() for t in args.tool_filter.split(",")]

                print(f"\n📤 Extracting tool operations from {len(indices)} session(s)...")
                if tool_filter:
                    print(f"🔧 Filter: {', '.join(tool_filter)}")
                if args.detailed:
                    print("📋 Including detailed results")
                if args.by_project:
                    print("📂 Organizing by project folders")
                if args.by_day:
                    print("📅 Organizing by date folders")
                if args.overwrite:
                    print("🔄 Overwriting existing files")

                success, total_ops = extractor.extract_tool_operations_multiple(
                    sessions, indices,
                    tool_filter=tool_filter,
                    detailed=args.detailed,
                    by_day=args.by_day, by_project=args.by_project,
                    overwrite=args.overwrite
                )
                print(f"\n✅ Successfully extracted {total_ops} operations from {success} sessions")
            else:
                print(f"\n📤 Extracting {len(indices)} session(s) as {args.format.upper()}...")
                if args.detailed:
                    print("📋 Including detailed tool use and system messages")
                if args.by_project:
                    print("📂 Organizing by project folders")
                if args.by_day:
                    print("📅 Organizing by date folders")
                if args.overwrite:
                    print("🔄 Overwriting existing files")
                success, total = extractor.extract_multiple(
                    sessions, indices, format=args.format, detailed=args.detailed,
                    by_day=args.by_day, by_project=args.by_project,
                    overwrite=args.overwrite, include_thinking=args.thinking
                )
                print(f"\n✅ Successfully extracted {success}/{total} sessions")

    elif args.recent:
        sessions = extractor.find_sessions()

        # Apply project filter
        if project_indices and projects:
            sessions = extractor.filter_sessions_by_projects(sessions, project_indices, projects)

        # Apply date filter
        if from_date or to_date:
            sessions = extractor.filter_sessions_by_date(sessions, from_date, to_date)
            if from_date:
                print(f"📅 Filtering from: {from_date.strftime('%Y-%m-%d')}")
            if to_date:
                print(f"📅 Filtering to: {to_date.strftime('%Y-%m-%d')}")

        limit = min(args.recent, len(sessions))
        indices = list(range(limit))

        if args.bash_commands:
            print(f"\n📤 Extracting bash commands from {limit} most recent sessions...")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")
            success, total_cmds = extractor.extract_bash_commands_multiple(
                sessions, indices,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite
            )
            print(f"\n✅ Successfully extracted {total_cmds} commands from {success} sessions")
        elif args.tool_ops:
            # Parse tool filter
            tool_filter = None
            if args.tool_filter:
                tool_filter = [t.strip() for t in args.tool_filter.split(",")]

            print(f"\n📤 Extracting tool operations from {limit} most recent sessions...")
            if tool_filter:
                print(f"🔧 Filter: {', '.join(tool_filter)}")
            if args.detailed:
                print("📋 Including detailed results")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")

            success, total_ops = extractor.extract_tool_operations_multiple(
                sessions, indices,
                tool_filter=tool_filter,
                detailed=args.detailed,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite
            )
            print(f"\n✅ Successfully extracted {total_ops} operations from {success} sessions")
        else:
            print(f"\n📤 Extracting {limit} most recent sessions as {args.format.upper()}...")
            if args.detailed:
                print("📋 Including detailed tool use and system messages")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")
            success, total = extractor.extract_multiple(
                sessions, indices, format=args.format, detailed=args.detailed,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite, include_thinking=args.thinking
            )
            print(f"\n✅ Successfully extracted {success}/{total} sessions")

    elif args.all:
        sessions = extractor.find_sessions()

        # Apply project filter
        if project_indices and projects:
            sessions = extractor.filter_sessions_by_projects(sessions, project_indices, projects)

        # Apply date filter
        if from_date or to_date:
            sessions = extractor.filter_sessions_by_date(sessions, from_date, to_date)
            if from_date:
                print(f"📅 Filtering from: {from_date.strftime('%Y-%m-%d')}")
            if to_date:
                print(f"📅 Filtering to: {to_date.strftime('%Y-%m-%d')}")

        indices = list(range(len(sessions)))

        if args.bash_commands:
            print(f"\n📤 Extracting bash commands from {len(sessions)} sessions...")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")
            success, total_cmds = extractor.extract_bash_commands_multiple(
                sessions, indices,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite
            )
            print(f"\n✅ Successfully extracted {total_cmds} commands from {success} sessions")
        elif args.tool_ops:
            # Parse tool filter
            tool_filter = None
            if args.tool_filter:
                tool_filter = [t.strip() for t in args.tool_filter.split(",")]

            print(f"\n📤 Extracting tool operations from {len(sessions)} sessions...")
            if tool_filter:
                print(f"🔧 Filter: {', '.join(tool_filter)}")
            if args.detailed:
                print("📋 Including detailed results")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")

            success, total_ops = extractor.extract_tool_operations_multiple(
                sessions, indices,
                tool_filter=tool_filter,
                detailed=args.detailed,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite
            )
            print(f"\n✅ Successfully extracted {total_ops} operations from {success} sessions")
        else:
            print(f"\n📤 Extracting {len(sessions)} sessions as {args.format.upper()}...")
            if args.detailed:
                print("📋 Including detailed tool use and system messages")
            if args.by_project:
                print("📂 Organizing by project folders")
            if args.by_day:
                print("📅 Organizing by date folders")
            if args.skip_existing:
                print("⏭️  Skipping existing files")
            if args.overwrite:
                print("🔄 Overwriting existing files")
            success, total = extractor.extract_multiple(
                sessions, indices, format=args.format, detailed=args.detailed,
                by_day=args.by_day, by_project=args.by_project,
                overwrite=args.overwrite, include_thinking=args.thinking
            )
            print(f"\n✅ Successfully extracted {success}/{total} sessions")


def launch_interactive():
    """Launch the interactive UI directly, or handle search if specified."""
    import sys
    
    # If no arguments provided, launch interactive UI
    if len(sys.argv) == 1:
        try:
            from .interactive_ui import main as interactive_main
        except ImportError:
            from interactive_ui import main as interactive_main
        interactive_main()
    # Check if 'search' was passed as an argument
    elif len(sys.argv) > 1 and sys.argv[1] == 'search':
        # Launch real-time search with viewing capability
        try:
            from .realtime_search import RealTimeSearch, create_smart_searcher
            from .search_conversations import ConversationSearcher
        except ImportError:
            from realtime_search import RealTimeSearch, create_smart_searcher
            from search_conversations import ConversationSearcher
        
        # Initialize components
        extractor = ClaudeConversationExtractor()
        searcher = ConversationSearcher()
        smart_searcher = create_smart_searcher(searcher)
        
        # Run search
        rts = RealTimeSearch(smart_searcher, extractor)
        selected_file = rts.run()
        
        if selected_file:
            # View the selected conversation
            extractor.display_conversation(selected_file)
            
            # Offer to extract
            try:
                extract_choice = input("\n📤 Extract this conversation? (y/N): ").strip().lower()
                if extract_choice == 'y':
                    conversation = extractor.extract_conversation(selected_file)
                    if conversation:
                        session_id = selected_file.stem
                        output = extractor.save_as_markdown(conversation, session_id)
                        print(f"✅ Saved: {output.name}")
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Cancelled")
    else:
        # If other arguments are provided, run the normal CLI
        main()


if __name__ == "__main__":
    main()
