#!/usr/bin/env python3
"""Claude Code hook: surface repo instructions a session would otherwise miss.

PreToolUse (Edit/Write): a session started outside a checkout (for example in
~/dev) never loads the checkout's CLAUDE.md, and a cd into the repo later does
not load it either. The first Edit/Write under a repo whose instruction files
this session has not seen is denied once, with the file paths in the reason.
The retry passes.

SessionStart and SubagentStart: personal rules for one repo (PERSONAL_RULES)
stay out of the global CLAUDE.md so sessions in other repos do not carry them.
A session or subagent starting inside a matching checkout gets them injected
here; a subagent starts without the session's injected context, so it needs
its own copy. Any other session sees the rules listed in the first-edit
denial.

Reads hook JSON on stdin. State lives in ~/.claude/state/repo-instructions/,
one file per session id."""

import glob
import json
import os
import re
import subprocess
import sys
import time

STATE_DIR = os.path.expanduser("~/.claude/state/repo-instructions")
STATE_MAX_AGE_SECONDS = 7 * 24 * 3600
INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md")
DOTFILES_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PERSONAL_RULES = (
    (
        re.compile(r"github\.com[:/]PostHog/posthog(\.git)?/?$", re.IGNORECASE),
        os.path.join(DOTFILES_ROOT, "claude", "posthog"),
    ),
)


def read_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def target_path(tool_input):
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def global_instruction_paths():
    paths = set()
    for candidate in ("~/.claude/CLAUDE.md", "~/CLAUDE.md"):
        expanded = os.path.expanduser(candidate)
        if os.path.exists(expanded):
            paths.add(os.path.realpath(expanded))
    return paths


def personal_rules_for(repo_root):
    try:
        remote = subprocess.run(
            ["git", "-C", repo_root, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except Exception:
        return []
    for pattern, rules_dir in PERSONAL_RULES:
        if pattern.search(remote):
            return sorted(glob.glob(os.path.join(rules_dir, "*.md")))
    return []


def instruction_files_for(path):
    """Instruction files from the file's directory up to the enclosing repo root."""
    found = []
    skip = global_instruction_paths()
    home = os.path.realpath(os.path.expanduser("~"))
    directory = os.path.realpath(os.path.dirname(path))
    while True:
        for name in INSTRUCTION_FILES:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                real = os.path.realpath(candidate)
                if real not in skip and real not in found:
                    found.append(real)
                break
        is_repo_root = os.path.exists(os.path.join(directory, ".git"))
        parent = os.path.dirname(directory)
        if is_repo_root or directory in (home, parent):
            break
        directory = parent
    if is_repo_root:
        found.extend(p for p in personal_rules_for(directory) if p not in found)
    return found


def enclosing_repo_root(directory):
    home = os.path.realpath(os.path.expanduser("~"))
    while not os.path.exists(os.path.join(directory, ".git")):
        parent = os.path.dirname(directory)
        if directory in (home, parent):
            return None
        directory = parent
    return directory


def state_file(session_id):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    return os.path.join(STATE_DIR, f"{safe}.json")


def load_seen(session_id):
    try:
        with open(state_file(session_id), encoding="utf-8") as f:
            data = json.load(f)
        return set(data) if isinstance(data, list) else set()
    except Exception:
        return set()


def save_seen(session_id, seen):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_file(session_id), "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f)


def prune_old_state():
    try:
        cutoff = time.time() - STATE_MAX_AGE_SECONDS
        for name in os.listdir(STATE_DIR):
            full = os.path.join(STATE_DIR, name)
            if os.path.getmtime(full) < cutoff:
                os.remove(full)
    except Exception:
        pass


def deny(paths):
    listing = "\n".join(f"  - {p}" for p in paths)
    reason = (
        "Repo instructions not loaded in this session. Read these files, and every "
        "doc they mark as required for the files you are changing, then retry the "
        "edit:\n" + listing
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def personal_rules_at(data):
    root = enclosing_repo_root(os.path.realpath(data.get("cwd") or os.getcwd()))
    return personal_rules_for(root) if root else []


def render_rules(rules):
    bodies = []
    for path in rules:
        with open(path, encoding="utf-8") as f:
            bodies.append(f.read().strip())
    return (
        f"Personal rules for this repo, from {os.path.dirname(rules[0])}:\n\n"
        + "\n\n".join(bodies)
    )


def inject_into_session(data):
    rules = personal_rules_at(data)
    if not rules:
        return
    session_id = str(data.get("session_id") or "default")
    save_seen(session_id, load_seen(session_id) | set(rules))
    print(render_rules(rules))


def inject_into_subagent(data):
    rules = personal_rules_at(data)
    if not rules:
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": render_rules(rules),
                }
            }
        )
    )


def main():
    data = read_input()
    event = data.get("hook_event_name")
    if event == "SessionStart":
        inject_into_session(data)
        return 0
    if event == "SubagentStart":
        inject_into_subagent(data)
        return 0
    path = target_path(data.get("tool_input") or {})
    if not path:
        return 0
    session_id = str(data.get("session_id") or "default")
    prune_old_state()
    files = instruction_files_for(os.path.abspath(path))
    if not files:
        return 0
    seen = load_seen(session_id)
    unseen = [f for f in files if f not in seen]
    if not unseen:
        return 0
    save_seen(session_id, seen | set(unseen))
    deny(unseen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
