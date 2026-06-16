#!/usr/bin/env python3
"""Stop hook: block when the last assistant message contains bare GitHub-style
issue/PR numbers (#NNNN) that aren't already a clickable link.

Rationale lives in ~/.claude memory feedback_always_include_links: a number on
its own ("merge #62534") is unreadable outside the terminal and forces a hunt.
This is the deterministic backstop for the self-gate that keeps slipping.

Reads the hook JSON on stdin, finds the last assistant turn in the transcript,
strips the spans where a bare number is legitimate (code, links, URLs), and if a
bare #NNNN survives, emits {"decision":"block"} so the model must rewrite."""

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
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                parts = [
                    c.get("text", "")
                    for c in msg.get("content", [])
                    if isinstance(c, dict) and c.get("type") == "text"
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


def find_bare_refs(text):
    stripped = text
    for pat in (FENCED_CODE, INLINE_CODE, MD_LINK, BARE_URL):
        stripped = pat.sub(" ", stripped)
    return sorted(set(m.group(0) for m in BARE_REF.finditer(stripped)))


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript = payload.get("transcript_path")
    if not transcript:
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
