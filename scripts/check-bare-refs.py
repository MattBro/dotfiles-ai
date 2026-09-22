#!/usr/bin/env python3
"""Claude Code/Codex hook: block bare GitHub-style
issue/PR numbers (#NNNN) that aren't already a clickable link.

Rationale lives in ~/.claude memory feedback_always_include_links: a number on
its own ("merge #62534") is unreadable outside the terminal and forces a hunt.
This is the deterministic backstop for the self-gate that keeps slipping.

Reads hook JSON on stdin. Codex supplies the final response directly as
``last_assistant_message``; Claude Code supplies a transcript path. The hook
strips spans where a bare number is legitimate (code, links, URLs), and emits a
blocking response when a bare #NNNN survives."""

import json
import re
import sys


def last_assistant_text(transcript_path):
    text = None
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(rec, dict):
                    continue
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message", {})
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content", [])
                if isinstance(content, str):
                    text = content
                    continue
                if not isinstance(content, list):
                    continue
                parts = [
                    c.get("text", "")
                    for c in content
                    if isinstance(c, dict)
                    and c.get("type") == "text"
                    and isinstance(c.get("text"), str)
                ]
                if parts:
                    text = "\n".join(parts)
    except OSError:
        return None
    return text


# Spans where a bare number is fine and must not trip the check.
FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`]*`")
MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
BARE_URL = re.compile(r"https?://\S+")

# A 4+ digit issue/PR number not already inside a link/url/code span.
BARE_REF = re.compile(r"(?<!\w)#\d{4,}\b")

# Outbound text (Slack drafts, PR/issue comments) gets a stricter rule: a naked
# 4-6 digit number with no '#' is almost never legitimate prose there, and it is
# exactly how a PR reference slips out ("78516 is only the spinner"). Chat keeps
# the looser '#NNNN' rule, where ports and counts appear legitimately.
NAKED_REF = re.compile(r"(?<![\w#/.-])\d{4,6}(?![\w.-])")


def find_bare_refs(text, strict=False):
    if not isinstance(text, str):
        return []
    stripped = text
    for pat in (FENCED_CODE, INLINE_CODE, MD_LINK, BARE_URL):
        stripped = pat.sub(" ", stripped)
    pats = (BARE_REF, NAKED_REF) if strict else (BARE_REF,)
    found = set()
    for pat in pats:
        found.update(m.group(0) for m in pat.finditer(stripped))
    return sorted(found)


# PreToolUse: tools whose input carries text that reaches a human, and the field
# holding it. The Stop hook never sees these, so a reference written straight
# into a draft used to bypass the check entirely.
OUTBOUND_TEXT_FIELDS = {
    "mcp__slack__slack_send_message_draft": "message",
    "mcp__slack__slack_send_message": "message",
}


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)

    tool_name = payload.get("tool_name")
    if tool_name in OUTBOUND_TEXT_FIELDS:
        field = OUTBOUND_TEXT_FIELDS[tool_name]
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            sys.exit(0)
        text = tool_input.get(field) or ""
        refs = find_bare_refs(text, strict=True)
        if not refs:
            sys.exit(0)
        offenders = ", ".join(refs[:8])
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": (
                            f"Bare number(s) in the outbound message: {offenders}. "
                            "Matt reads these outside the terminal and cannot click a "
                            "number. Rewrite each as a plain-English name plus a "
                            "clickable link, e.g. [fix(onboarding): resolve step ids]"
                            "(https://github.com/PostHog/posthog/pull/78516), then "
                            "create the draft again."
                        ),
                    }
                }
            )
        )
        sys.exit(0)

    # Codex has a stable final-message field. Fall back to Claude Code's JSONL
    # transcript so this one script can be shared by both clients.
    if payload.get("stop_hook_active"):
        sys.exit(0)

    text = payload.get("last_assistant_message")
    if not text:
        transcript = payload.get("transcript_path")
        if not isinstance(transcript, str) or not transcript:
            sys.exit(0)
        text = last_assistant_text(transcript)
    if not text:
        sys.exit(0)

    refs = find_bare_refs(text)
    if not refs:
        sys.exit(0)

    offenders = ", ".join(refs[:8])
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    f"Bare issue/PR number(s) in your reply: {offenders}. "
                    "Rewrite every one as a plain-English name plus a clickable "
                    "link, e.g. [feat(oauth): @default union scope ceilings]"
                    "(https://github.com/PostHog/posthog/pull/64087) — never a "
                    "bare #NNNN the user has to go decode. Then finish."
                ),
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
