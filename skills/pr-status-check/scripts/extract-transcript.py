#!/usr/bin/env python3
"""extract-transcript: distill a Claude Code session .jsonl into readable
conversation text — user prompts and assistant prose only.

Tool calls, tool results, and thinking blocks are dropped: they're the bulk of
a transcript and the part that goes stale (old file reads, dead CI states).
What survives is the part worth carrying into a fresh session: what was asked,
what was decided, and why.

Output is tail-biased (--max-chars keeps the END of the conversation) because
decisions accumulate late in a session.

Usage:
  extract-transcript.py <session.jsonl | session-id> [--max-chars 40000]

A bare session id is resolved by searching ~/.claude/projects/*/<id>.jsonl.
"""

import argparse
import glob
import json
import os
import sys

PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")


def resolve(arg):
    if os.path.isfile(arg):
        return arg
    hits = glob.glob(os.path.join(PROJECTS, "*", f"{arg}.jsonl"))
    if not hits:
        sys.exit(f"No transcript found for: {arg}")
    return hits[0]


def text_of(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p).strip()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="path to session .jsonl, or a bare session id")
    ap.add_argument("--max-chars", type=int, default=40000,
                    help="cap output to the LAST N chars of conversation (default 40000)")
    args = ap.parse_args()

    path = resolve(args.session)
    turns = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = d.get("type")
            if role not in ("user", "assistant"):
                continue
            msg = d.get("message") or {}
            txt = text_of(msg.get("content"))
            if not txt:
                continue
            # skip harness-injected user messages (tool results arrive as type=user)
            if role == "user" and txt.startswith("<"):
                continue
            turns.append(f"{'USER' if role == 'user' else 'ASSISTANT'}: {txt}")

    out = "\n\n".join(turns)
    if len(out) > args.max_chars:
        out = "[…earlier conversation truncated…]\n\n" + out[-args.max_chars:]
    print(out)


if __name__ == "__main__":
    main()
