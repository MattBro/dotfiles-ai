#!/usr/bin/env python3
"""Codex PreToolUse hook: keep Slack writes draft-only."""

import json
import sys


BLOCKED_TOOLS = {
    "mcp__slack__slack_create_conversation",
    "mcp__slack__slack_create_canvas",
    "mcp__slack__slack_update_canvas",
    "mcp__slack__slack_schedule_message",
    "mcp__slack__slack_send_message",
}


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if not isinstance(payload, dict):
        return

    tool_name = payload.get("tool_name")
    if tool_name not in BLOCKED_TOOLS:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"{tool_name} is disabled by the personal draft-only Slack "
                        "policy. Create a Slack draft instead and show the text in chat."
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
