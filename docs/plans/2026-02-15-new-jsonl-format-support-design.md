# Design: New JSONL Format Support

**Date:** 2026-02-15
**Approach:** Incremental Refactor (Approach A)
**Scope:** Drop old format, support new format only, inline subagents, optional thinking, detailed metadata

---

## Background

Claude Code has overhauled its JSONL conversation storage format. The changes are:

1. **Entry types changed:** Old standalone `tool_use`, `tool_result`, `summary` types are gone. New types: `progress`, `file-history-snapshot`.
2. **Tool interactions consolidated:** `tool_use` blocks now live inside `assistant.message.content[]`, `tool_result` blocks inside `user.message.content[]`.
3. **Subagent directory structure:** Each session can spawn subagents at `{sessionId}/subagents/agent-{agentId}.jsonl`.
4. **New content block types:** `thinking` (extended thinking), `tool_use.caller` field.
5. **New fields on every entry:** `uuid`, `parentUuid`, `sessionId`, `version`, `gitBranch`, `cwd`, `isSidechain`.
6. **Rich usage metadata:** Token counts include cache breakdown, server tool use counts, inference geo, speed tier.
7. **System entries restructured:** Now have `content` + `subtype` fields instead of `message` field. Subtypes: `local_command`, `turn_duration`.

## Decisions

| Decision | Choice |
|----------|--------|
| Old vs new format | New format only (drop old) |
| Subagent handling | Inline in main conversation at Task tool invocation point |
| Thinking blocks | Optional via `--thinking` flag, hidden by default |
| Metadata/stats | In `--detailed` mode: per-message metadata + summary stats block |

## Section 1: Entry Parsing Overhaul

### Changes to `extract_conversation()`

- **Remove** the `elif detailed:` block handling standalone `tool_use`, `tool_result`, `system` (old format types).
- **Update** assistant handler: iterate `message.content[]` for `text`, `tool_use`, and optionally `thinking` blocks.
- **Update** user handler: iterate `message.content[]` for `tool_result` blocks (for Q&A matching).
- **Add** handling for `progress` entries (hook events) in detailed mode.
- **Add** handling for new `system` entry structure (`content` + `subtype` fields).
- **Add** `include_thinking` parameter. When True, extract `thinking` content blocks.
- **Add** per-message metadata dict in detailed mode: `model`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cwd`, `git_branch`.

### New `--thinking` CLI flag

```
--thinking    Include Claude's thinking/reasoning blocks in output
```

### Per-message metadata dict (detailed mode only)

```python
{
    "role": "assistant",
    "content": "...",
    "timestamp": "...",
    "metadata": {
        "model": "claude-opus-4-6",
        "input_tokens": 3500,
        "output_tokens": 120,
        "cache_read_tokens": 40000,
        "cwd": "/mnt/d/...",
        "git_branch": "main"
    }
}
```

## Section 2: Subagent Discovery & Inline Merging

### Directory structure

```
{sessionId}.jsonl                              <- main conversation
{sessionId}/subagents/agent-{agentId}.jsonl    <- one per subagent
```

### New method: `find_subagent_files(session_path) -> Dict[str, Path]`

Returns mapping of agentId -> Path for subagent JSONL files associated with a session.

### New method: `extract_subagent_conversation(subagent_path, detailed, include_thinking) -> Dict`

Returns `{"agent_id": str, "description": str, "model": str, "messages": [...]}`.

### Inline merging strategy

1. When a `tool_use` block with `name == "Task"` is found in assistant content, record the `tool_use_id`, `description`, `subagent_type`.
2. When the corresponding `tool_result` arrives in a user message, extract the `agentId` from the result text via `re.search(r'agentId:\s*(\w+)', text)`.
3. Look up the subagent JSONL file, extract its conversation, insert as a `"role": "subagent"` message block.

### Changes to `find_sessions()`

Filter out subagent files from session listing:

```python
if "/subagents/" in str(jsonl_file) or "\\subagents\\" in str(jsonl_file):
    continue
```

### Changes to `extract_bash_commands()` and `extract_tool_operations()`

- Remove dead code for old standalone `tool_use`/`tool_result` entries.
- Add tool_result extraction from user message content arrays.
- Optionally recurse into subagent files.

## Section 3: Tool Result Matching (New Format)

### Old flow (broken)

```
assistant entry -> standalone tool_use entry -> standalone tool_result entry
```

### New flow

```
assistant entry (with tool_use in content[]) -> user entry (with tool_result in content[])
```

### Changes to `extract_bash_commands()` and `extract_tool_operations()`

- **Remove** `elif entry_type == "tool_use"` blocks (dead code).
- **Remove** `elif entry_type == "tool_result"` blocks (dead code).
- **Add** tool_result extraction inside `elif entry_type == "user"` block, iterating `message.content[]` for `tool_result` items.
- **Handle** result content format: can be plain string or list of `{"type": "text", "text": "..."}` blocks.

### Changes to `_extract_text_content()`

Skip `tool_result` blocks when extracting user message text (they're handled separately).

## Section 4: System Entries, Progress Entries & Metadata Stats

### New system entry handling (detailed mode)

Parse `subtype` field:
- `turn_duration`: Format as "Turn completed in {durationMs/1000}s"
- `local_command`: Format as "Command: {content}"

### New progress entry handling (detailed mode)

Extract `data.hookEvent` and `data.hookName`, format as system-like message.

### `file-history-snapshot` entries

Skip entirely — internal bookkeeping, not useful in extracted output.

### Summary stats block

Accumulated during parsing, appended as `"role": "stats"` message:

```python
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
```

## Section 5: CLI Changes & Output Formatter Updates

### New CLI argument

```
--thinking    Include Claude's thinking/reasoning blocks in output
```

### Markdown formatter new roles

- `thinking`: Rendered in `<details>` collapse block
- `subagent`: Nested section with agent metadata header and indented sub-messages
- `stats`: Table at end of conversation
- Per-message metadata: Blockquote line after assistant header

### HTML formatter

Same roles with CSS classes: collapsible thinking, indented subagent container, HTML stats table.

### JSON formatter

No changes needed — new fields serialize naturally.

### Search functionality

`find_sessions()` fix propagates to search. Subagent content searchable via inline merging.

## Section 6: Testing Strategy

### Fixture rewrite

All fixtures in `tests/fixtures/sample_conversations.py` produce new-format entries with common fields: `uuid`, `parentUuid`, `sessionId`, `timestamp`, `isSidechain`, `userType`, `cwd`, `version`, `gitBranch`.

### New test cases

- `test_extract_new_format_basic` — basic user/assistant parsing
- `test_tool_result_in_user_content` — tool results from user content arrays
- `test_thinking_blocks_excluded_by_default` — thinking omitted without flag
- `test_thinking_blocks_included` — thinking present with flag
- `test_subagent_discovery` — `find_subagent_files()` works
- `test_subagent_inline` — subagent spliced at correct position
- `test_subagent_skipped_in_session_list` — `find_sessions()` excludes subagent files
- `test_metadata_in_detailed_mode` — per-message metadata populated
- `test_stats_block` — stats appended with correct totals
- `test_progress_entries_detailed` — progress entries in detailed mode
- `test_system_entries_new_format` — new system structure parsed
- `test_bash_commands_new_format` — bash extraction with new tool_result location
- `test_tool_ops_new_format` — tool operations with new format
- `test_markdown_subagent_rendering` — subagent blocks in markdown
- `test_markdown_thinking_rendering` — thinking in `<details>`
- `test_markdown_stats_rendering` — stats table

## File Change Summary

| File | Change Type | Scope |
|------|-------------|-------|
| `src/extract_claude_logs.py` | Major refactor | Entry parsing, subagent discovery, tool result matching, thinking, metadata, stats, CLI |
| `src/interactive_ui.py` | Minor update | Thread `include_thinking` parameter |
| `src/search_conversations.py` | Minor update | Exclude subagent files from session listing |
| `src/realtime_search.py` | Minor update | Same subagent exclusion |
| `tests/fixtures/sample_conversations.py` | Rewrite | All fixtures produce new-format entries |
| `tests/conftest.py` | Update | Shared fixtures use new format |
| `tests/test_extractor.py` | Major update | Fixtures + new test cases |
| `tests/test_extract_comprehensive.py` | Major update | Fixtures + new test cases |
| `tests/test_extract_claude_logs_aligned.py` | Major update | Fixtures |
| `tests/test_search*.py` | Minor updates | Fixture data |
| `tests/test_interactive_ui.py` | Minor update | New parameter |
