#!/usr/bin/env python3
"""Merge dotfiles-ai's managed settings into an existing Codex config.

Codex owns and updates other parts of ~/.codex/config.toml (plugins, MCP
servers, model choices, trusted projects). Replacing that file with a symlink
would destroy those settings, so the installer owns only marked setting blocks.
"""

import argparse
import os
import re
import tempfile


TOP_BEGIN = "# >>> dotfiles-ai: Codex top-level settings >>>"
TOP_END = "# <<< dotfiles-ai: Codex top-level settings <<<"
TUI_BEGIN = "# >>> dotfiles-ai: Codex status line >>>"
TUI_END = "# <<< dotfiles-ai: Codex status line <<<"
TUI_TABLE_BEGIN = "# >>> dotfiles-ai: Codex [tui] table >>>"
TUI_TABLE_END = "# <<< dotfiles-ai: Codex [tui] table <<<"
SLACK_BEGIN = "# >>> dotfiles-ai: Codex Slack safety policy >>>"
SLACK_END = "# <<< dotfiles-ai: Codex Slack safety policy <<<"

TOP_KEYS = {"project_doc_max_bytes", "project_doc_fallback_filenames"}
TUI_KEYS = {"status_line"}
SLACK_KEYS = {"disabled_tools"}
SECTION_RE = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?$")
MARKER_BLOCKS = {
    TOP_BEGIN: (TOP_END, TOP_KEYS, frozenset()),
    TUI_BEGIN: (TUI_END, TUI_KEYS, frozenset()),
    TUI_TABLE_BEGIN: (TUI_TABLE_END, frozenset(), {"[tui]"}),
    SLACK_BEGIN: (SLACK_END, SLACK_KEYS, frozenset()),
}


def source_blocks(path):
    """Return managed section bodies from the repository fragment."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    top = []
    tui = []
    slack = []
    section = None
    for line in lines:
        match = SECTION_RE.match(line)
        if match:
            section = match.group(1)
            continue
        if section is None:
            top.append(line)
        elif section == "tui":
            tui.append(line)
        elif section == "mcp_servers.slack":
            slack.append(line)

    return (
        select_assignments(top, TOP_KEYS, path, "top-level"),
        select_assignments(tui, TUI_KEYS, path, "[tui]"),
        select_assignments(slack, SLACK_KEYS, path, "[mcp_servers.slack]"),
    )


def trim_blank_lines(lines):
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def assignment_key(line):
    match = re.match(r"^\s*([A-Za-z0-9_-]+)\s*=", line)
    return match.group(1) if match else None


def assignment_end(lines, start):
    """Return the first index after one scalar or bracketed TOML assignment."""
    depth = bracket_delta(lines[start])
    index = start + 1
    while depth > 0 and index < len(lines):
        depth += bracket_delta(lines[index])
        index += 1
    return index


def select_assignments(lines, keys, path, section_name):
    """Extract exactly the settings this installer owns from a source section."""
    selected = []
    found = set()
    index = 0
    while index < len(lines):
        key = assignment_key(lines[index])
        if key not in keys:
            index += 1
            continue
        if key in found:
            raise ValueError(f"{path} defines {key} more than once in {section_name}")
        end = assignment_end(lines, index)
        selected.extend(lines[index:end])
        found.add(key)
        index = end

    missing = keys - found
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(
            f"{path} is missing managed {section_name} setting(s): {names}"
        )
    return selected


def preserve_unowned(block, managed_keys, managed_statements):
    """Keep assignments another process wrote inside one of our marker blocks."""
    preserved = []
    pending_comments = []
    index = 0
    while index < len(block):
        line = block[index]
        if line.strip() in managed_statements:
            pending_comments = []
            index += 1
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            pending_comments.append(line)
            index += 1
            continue

        key = assignment_key(line)
        if key is not None:
            end = assignment_end(block, index)
            if key not in managed_keys:
                preserved.extend(pending_comments)
                preserved.extend(block[index:end])
            pending_comments = []
            index = end
            continue

        # A table header or other TOML statement cannot belong to one of the
        # small generated assignment blocks. Preserve it and everything after
        # it rather than risking deletion after a truncated end marker.
        preserved.extend(pending_comments)
        preserved.extend(block[index:])
        break
    return trim_blank_lines(preserved)


def strip_marker_blocks(lines):
    """Remove managed values while retaining machine-owned values inside them."""
    result = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line not in MARKER_BLOCKS:
            result.append(line)
            index += 1
            continue

        expected_end, managed_keys, managed_statements = MARKER_BLOCKS[line]
        index += 1
        block_start = index
        try:
            block_end = lines.index(expected_end, block_start)
            next_index = block_end + 1
        except ValueError:
            block_end = len(lines)
            for candidate in range(block_start, len(lines)):
                candidate_line = lines[candidate]
                if candidate_line in MARKER_BLOCKS:
                    block_end = candidate
                    break
                if (
                    SECTION_RE.match(candidate_line)
                    and candidate_line.strip() not in managed_statements
                ):
                    block_end = candidate
                    break
            next_index = block_end

        result.extend(
            preserve_unowned(
                lines[block_start:block_end], managed_keys, managed_statements
            )
        )

        # Treat the next marker, table, or EOF as the end of a truncated block.
        # preserve_unowned retained any settings that were not ours.
        index = next_index
        # Every managed block owns the one blank line it appends.
        if index < len(lines) and not lines[index].strip():
            index += 1
    return result


def bracket_delta(line):
    """Enough TOML awareness to skip a multi-line array assignment."""
    depth = 0
    quote = None
    escaped = False
    for character in line:
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if quote == "'":
            if character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "#":
            break
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
    return depth


def remove_unmarked_assignments(lines):
    """Remove earlier manual copies of settings now owned by dotfiles-ai."""
    result = []
    section = None
    index = 0
    while index < len(lines):
        line = lines[index]
        match = SECTION_RE.match(line)
        if match:
            section = match.group(1)
            result.append(line)
            index += 1
            continue

        key = assignment_key(line)
        managed = (
            (section is None and key in TOP_KEYS)
            or (section == "tui" and key in TUI_KEYS)
            or (section == "mcp_servers.slack" and key in SLACK_KEYS)
        )
        if not managed:
            result.append(line)
            index += 1
            continue

        index = assignment_end(lines, index)
    return result


def merge(existing, top, tui, slack):
    lines = existing.splitlines()
    lines = strip_marker_blocks(lines)
    lines = remove_unmarked_assignments(lines)

    top_block = [TOP_BEGIN, *top, TOP_END, ""]
    first_section = next(
        (i for i, line in enumerate(lines) if SECTION_RE.match(line)), len(lines)
    )
    if first_section > 0 and lines[first_section - 1].strip():
        top_block.insert(0, "")
    lines[first_section:first_section] = top_block

    tui_index = next(
        (
            i
            for i, line in enumerate(lines)
            if (match := SECTION_RE.match(line)) and match.group(1) == "tui"
        ),
        None,
    )
    if tui_index is None:
        # A parent table must be declared before subtables such as
        # [tui.model_availability_nux].
        tui_index = next(
            (
                i
                for i, line in enumerate(lines)
                if (match := SECTION_RE.match(line))
                and match.group(1).startswith("tui.")
            ),
            len(lines),
        )
        prefix = [TUI_TABLE_BEGIN, "[tui]", TUI_TABLE_END]
        if tui_index > 0 and lines[tui_index - 1].strip():
            prefix.insert(0, "")
        lines[tui_index:tui_index] = prefix
        tui_index = next(
            i
            for i, line in enumerate(lines)
            if (match := SECTION_RE.match(line)) and match.group(1) == "tui"
        )

    tui_block = [TUI_BEGIN, *tui, TUI_END, ""]
    status_index = tui_index + 1
    if status_index < len(lines) and lines[status_index] == TUI_TABLE_END:
        status_index += 1
    lines[status_index:status_index] = tui_block

    # The MCP server itself is machine-managed. Apply the safety policy only
    # when Slack is already configured; do not create an unusable partial server.
    slack_index = next(
        (
            i
            for i, line in enumerate(lines)
            if (match := SECTION_RE.match(line))
            and match.group(1) == "mcp_servers.slack"
        ),
        None,
    )
    if slack_index is not None:
        slack_block = [SLACK_BEGIN, *slack, SLACK_END, ""]
        lines[slack_index + 1 : slack_index + 1] = slack_block
    return "\n".join(lines).rstrip() + "\n"


def remove(existing):
    lines = strip_marker_blocks(existing.splitlines())
    content = "\n".join(lines).rstrip()
    return content + ("\n" if content else "")


def atomic_write(path, content):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    try:
        mode = os.stat(path).st_mode & 0o777
    except FileNotFoundError:
        mode = 0o600
    fd, temporary = tempfile.mkstemp(prefix=".config.toml.", dir=directory)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.target, encoding="utf-8") as f:
            existing = f.read()
    except FileNotFoundError:
        existing = ""

    if args.remove:
        updated = remove(existing)
    else:
        top, tui, slack = source_blocks(args.source)
        updated = merge(existing, top, tui, slack)
        if not any(
            (match := SECTION_RE.match(line)) and match.group(1) == "mcp_servers.slack"
            for line in existing.splitlines()
        ):
            print("warning: Slack MCP is not configured; skipped its safety policy")

    if updated == existing:
        print(f"unchanged {args.target}")
        return
    atomic_write(args.target, updated)
    print(f"updated {args.target}")


if __name__ == "__main__":
    main()
