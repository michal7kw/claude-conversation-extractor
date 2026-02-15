"""Tests for Claude Conversation Extractor"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract_claude_logs import ClaudeConversationExtractor  # noqa: E402


class TestClaudeConversationExtractor(unittest.TestCase):
    """Test suite for the Claude Conversation Extractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = ClaudeConversationExtractor(output_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test extractor initialization"""
        self.assertEqual(self.extractor.output_dir, Path(self.temp_dir))
        self.assertTrue(self.extractor.claude_dir.name == "projects")

    def test_extract_text_content_string(self):
        """Test extracting text from string content"""
        content = "Hello, world!"
        result = self.extractor._extract_text_content(content)
        self.assertEqual(result, "Hello, world!")

    def test_extract_text_content_list(self):
        """Test extracting text from list content"""
        content = [
            {"type": "text", "text": "First part"},
            {"type": "text", "text": "Second part"},
            {"type": "other", "text": "Should ignore"},
        ]
        result = self.extractor._extract_text_content(content)
        self.assertEqual(result, "First part\nSecond part")

    def test_extract_text_content_other(self):
        """Test extracting text from other content types"""
        content = {"some": "dict"}
        result = self.extractor._extract_text_content(content)
        self.assertEqual(result, "{'some': 'dict'}")

    def test_save_as_markdown_empty_conversation(self):
        """Test saving empty conversation returns None"""
        result = self.extractor.save_as_markdown([], "test-session")
        self.assertIsNone(result)

    def test_save_as_markdown_with_conversation(self):
        """Test saving conversation to markdown"""
        conversation = [
            {
                "role": "user",
                "content": "Hello Claude",
                "timestamp": "2025-05-25T10:00:00Z",
            },
            {
                "role": "assistant",
                "content": "Hello! How can I help?",
                "timestamp": "2025-05-25T10:00:01Z",
            },
        ]

        result = self.extractor.save_as_markdown(conversation, "test-session-id")

        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertTrue(result.name.startswith("claude-conversation-"))
        self.assertTrue(result.name.endswith(".md"))

        # Check content
        content = result.read_text()
        self.assertIn("# Claude Conversation Log", content)
        self.assertIn("Session ID: test-session-id", content)
        self.assertIn("## 👤 User", content)
        self.assertIn("Hello Claude", content)
        self.assertIn("## 🤖 Claude", content)
        self.assertIn("Hello! How can I help?", content)

    def test_extract_conversation_valid_jsonl(self):
        """Test extracting conversation from valid JSONL"""
        # Create a temporary JSONL file
        jsonl_file = Path(self.temp_dir) / "test.jsonl"

        entries = [
            {
                "type": "user",
                "message": {"role": "user", "content": "Test message"},
                "timestamp": "2025-05-25T10:00:00Z",
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Test response"}],
                },
                "timestamp": "2025-05-25T10:00:01Z",
            },
        ]

        with open(jsonl_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        conversation = self.extractor.extract_conversation(jsonl_file)

        self.assertEqual(len(conversation), 2)
        self.assertEqual(conversation[0]["role"], "user")
        self.assertEqual(conversation[0]["content"], "Test message")
        self.assertEqual(conversation[1]["role"], "assistant")
        self.assertEqual(conversation[1]["content"], "Test response")

    def test_extract_conversation_invalid_file(self):
        """Test extracting conversation from non-existent file"""
        fake_path = Path(self.temp_dir) / "non_existent.jsonl"
        conversation = self.extractor.extract_conversation(fake_path)
        self.assertEqual(conversation, [])

    @patch("extract_claude_logs.Path.rglob")
    def test_find_sessions(self, mock_rglob):
        """Test finding session files"""
        # Mock some session files
        mock_files = [
            MagicMock(stat=MagicMock(return_value=MagicMock(st_mtime=1000))),
            MagicMock(stat=MagicMock(return_value=MagicMock(st_mtime=2000))),
            MagicMock(stat=MagicMock(return_value=MagicMock(st_mtime=1500))),
        ]
        mock_rglob.return_value = mock_files

        sessions = self.extractor.find_sessions()

        # Should be sorted by modification time, newest first
        self.assertEqual(len(sessions), 3)
        self.assertEqual(sessions[0].stat().st_mtime, 2000)
        self.assertEqual(sessions[1].stat().st_mtime, 1500)
        self.assertEqual(sessions[2].stat().st_mtime, 1000)


    def test_find_sessions_excludes_subagent_files(self):
        """Test that find_sessions skips subagent JSONL files."""
        import json
        projects_dir = Path(self.temp_dir) / "projects"
        project_dir = projects_dir / "test-project"
        project_dir.mkdir(parents=True)

        session_id = "aaaa-bbbb-cccc"
        main_file = project_dir / f"{session_id}.jsonl"
        main_file.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")

        subagent_dir = project_dir / session_id / "subagents"
        subagent_dir.mkdir(parents=True)
        sub_file = subagent_dir / "agent-abc123.jsonl"
        sub_file.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "task"}}) + "\n")

        self.extractor.claude_dir = projects_dir
        sessions = self.extractor.find_sessions()

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].name, f"{session_id}.jsonl")

    def test_find_subagent_files(self):
        """Test discovering subagent files for a session."""
        import json
        projects_dir = Path(self.temp_dir) / "projects"
        project_dir = projects_dir / "test-project"
        project_dir.mkdir(parents=True)

        session_id = "aaaa-bbbb-cccc"
        main_file = project_dir / f"{session_id}.jsonl"
        main_file.write_text(json.dumps({"type": "user"}) + "\n")

        subagent_dir = project_dir / session_id / "subagents"
        subagent_dir.mkdir(parents=True)
        (subagent_dir / "agent-abc123.jsonl").write_text(json.dumps({"type": "user"}) + "\n")
        (subagent_dir / "agent-def456.jsonl").write_text(json.dumps({"type": "user"}) + "\n")

        result = self.extractor.find_subagent_files(main_file)
        self.assertEqual(len(result), 2)
        self.assertIn("abc123", result)
        self.assertIn("def456", result)
        self.assertTrue(result["abc123"].exists())

    def test_find_subagent_files_no_subagents(self):
        """Test find_subagent_files when no subagent directory exists."""
        import json
        projects_dir = Path(self.temp_dir) / "projects"
        project_dir = projects_dir / "test-project"
        project_dir.mkdir(parents=True)

        main_file = project_dir / "session.jsonl"
        main_file.write_text(json.dumps({"type": "user"}) + "\n")

        result = self.extractor.find_subagent_files(main_file)
        self.assertEqual(result, {})

    def test_extract_new_format_basic(self):
        """Test basic extraction with new-format JSONL entries."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Hello Claude"),
            make_assistant_entry("Hi! How can I help?"),
            make_user_entry("What is Python?"),
            make_assistant_entry("Python is a programming language."),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)

        self.assertEqual(len(conversation), 4)
        self.assertEqual(conversation[0]["role"], "user")
        self.assertEqual(conversation[0]["content"], "Hello Claude")
        self.assertEqual(conversation[1]["role"], "assistant")
        self.assertEqual(conversation[1]["content"], "Hi! How can I help?")

    def test_extract_skips_progress_and_snapshot(self):
        """Test that progress and file-history-snapshot entries are skipped in normal mode."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, make_progress_entry,
            make_file_history_snapshot_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_progress_entry(),
            make_user_entry("Hello"),
            make_file_history_snapshot_entry(),
            make_assistant_entry("Hi there"),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)
        self.assertEqual(len(conversation), 2)
        self.assertEqual(conversation[0]["role"], "user")
        self.assertEqual(conversation[1]["role"], "assistant")

    def test_extract_tool_use_in_detailed_mode(self):
        """Test that tool_use blocks inside assistant content are shown in detailed mode."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry,
            make_user_entry_with_tool_results, write_jsonl
        )

        tool_use_id = "toolu_test123"
        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("List files"),
            make_assistant_entry("Let me list the files.", tool_uses=[
                {"id": tool_use_id, "name": "Bash", "input": {"command": "ls"}}
            ]),
            make_user_entry_with_tool_results([
                {"tool_use_id": tool_use_id, "content": "file1.py\nfile2.py"}
            ]),
            make_assistant_entry("Here are the files: file1.py and file2.py"),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)
        roles = [m["role"] for m in conversation]
        self.assertNotIn("tool_use", roles)
        self.assertNotIn("tool_result", roles)

        conversation_detailed = self.extractor.extract_conversation(jsonl_file, detailed=True)
        assistant_msgs = [m for m in conversation_detailed if m["role"] == "assistant"]
        self.assertTrue(any("Bash" in m["content"] for m in assistant_msgs))

    def test_extract_system_new_format_detailed(self):
        """Test new-format system entries in detailed mode."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry,
            make_system_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Hello"),
            make_assistant_entry("Hi"),
            make_system_entry(subtype="turn_duration", duration_ms=5000),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)
        self.assertEqual(len(conversation), 2)

        conversation = self.extractor.extract_conversation(jsonl_file, detailed=True)
        system_msgs = [m for m in conversation if m["role"] == "system"]
        self.assertEqual(len(system_msgs), 1)
        self.assertIn("5.0s", system_msgs[0]["content"])

    def test_extract_progress_detailed(self):
        """Test progress entries appear in detailed mode only."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry,
            make_progress_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_progress_entry(hook_event="SessionStart", hook_name="SessionStart:startup"),
            make_user_entry("Hello"),
            make_assistant_entry("Hi"),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file, detailed=True)
        system_msgs = [m for m in conversation if m["role"] == "system"]
        self.assertTrue(len(system_msgs) >= 1)
        self.assertTrue(any("SessionStart" in m["content"] for m in system_msgs))

    def test_extract_text_content_skips_tool_results(self):
        """Test that _extract_text_content skips tool_result blocks."""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "tool_result", "tool_use_id": "x", "content": "result data"},
            {"type": "text", "text": "World"},
        ]
        result = self.extractor._extract_text_content(content)
        self.assertEqual(result, "Hello\nWorld")
        self.assertNotIn("result data", result)

    def test_thinking_blocks_excluded_by_default(self):
        """Test thinking blocks are not included by default."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Explain recursion"),
            make_assistant_entry(
                "Recursion is a function calling itself.",
                thinking="Let me think about how to explain recursion simply..."
            ),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)
        roles = [m["role"] for m in conversation]
        self.assertNotIn("thinking", roles)
        self.assertEqual(len(conversation), 2)

    def test_thinking_blocks_included_with_flag(self):
        """Test thinking blocks included when include_thinking=True."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Explain recursion"),
            make_assistant_entry(
                "Recursion is a function calling itself.",
                thinking="Let me think about how to explain recursion simply..."
            ),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(
            jsonl_file, include_thinking=True
        )
        roles = [m["role"] for m in conversation]
        self.assertIn("thinking", roles)
        thinking_msgs = [m for m in conversation if m["role"] == "thinking"]
        self.assertEqual(len(thinking_msgs), 1)
        self.assertIn("explain recursion", thinking_msgs[0]["content"])

    def test_metadata_in_detailed_mode(self):
        """Test per-message metadata in detailed mode."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Hello"),
            make_assistant_entry("Hi!", model="claude-opus-4-6"),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file, detailed=True)
        assistant_msg = [m for m in conversation if m["role"] == "assistant"][0]

        self.assertIn("metadata", assistant_msg)
        self.assertEqual(assistant_msg["metadata"]["model"], "claude-opus-4-6")
        self.assertEqual(assistant_msg["metadata"]["input_tokens"], 1000)
        self.assertEqual(assistant_msg["metadata"]["output_tokens"], 200)

    def test_metadata_absent_in_normal_mode(self):
        """Test no metadata in non-detailed mode."""
        import json
        from fixtures.sample_conversations import (
            make_user_entry, make_assistant_entry, write_jsonl
        )

        jsonl_file = Path(self.temp_dir) / "test.jsonl"
        entries = [
            make_user_entry("Hello"),
            make_assistant_entry("Hi!"),
        ]
        write_jsonl(jsonl_file, entries)

        conversation = self.extractor.extract_conversation(jsonl_file)
        assistant_msg = [m for m in conversation if m["role"] == "assistant"][0]
        self.assertNotIn("metadata", assistant_msg)


if __name__ == "__main__":
    unittest.main()
