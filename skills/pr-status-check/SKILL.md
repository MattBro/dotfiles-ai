---
name: pr-status-check
description: >-
  List my open PRs with CI/review status, then pick the local Claude chat that
  best matches each (CMD+click ▶ resume opens it in a new Ghostty tab).
  macOS + Ghostty for the resume tabs; the table works anywhere. Trigger —
  "/pr-status-check", "pr status", "which chats go with my PRs".
  Vendored from nava-claude-plugins (nava-experimental/pr-resume).
---

# PR status check

> **Skill directory (`SKILL_DIR`):** the directory containing this SKILL.md
> (shown as "Base directory for this skill" when the skill loads). Scripts live
> under `<SKILL_DIR>/scripts/`.

Run the checker (portable: just `gh` + reading local session files). It emits
JSON, not a finished table — the script gathers candidates, **you make the final
call**. Exclude the current session so it never matches itself:

```bash
python3 "<SKILL_DIR>/scripts/pr-status-check.py" --exclude "$CLAUDE_CODE_SESSION_ID"
```

## Parse the JSON

Shape: `{ "env": {os, term, handler_installed}, "prs": [ { pr, title, url, draft,
ci, review, updated, head_branch, candidates: [ {title, dir, age, date, signals,
score, resume_link} ] } ] }`.

`signals` per candidate: `branch-exact` (session was literally on the PR's head
branch — near-certain), `url` (transcript cites the PR URL), `branch-name`
(cites the branch), `same-repo` (session cwd is in the PR's repo).

## Pick the best chat per PR (this is the judgment the script can't safely do)

For each PR, choose **one** candidate for its ▶ resume link:
- A `branch-exact` candidate wins outright → mark it 🎯.
- Otherwise weigh: **does the candidate's title actually relate to this PR's
  title/topic?** (most important — a recent but unrelated chat like "Ramp up on
  repo structure" should lose to an older on-topic one), then signal strength
  (`url` > `branch-name`, `same-repo` is a plus), then recency. Mark it 💬.
- If nothing is plausibly related, show `—` (don't force a bad match).
- If the top two are genuinely close, you may add a tiny "(or [▶ alt](link))".

## Render the table (exactly these columns)

```
| PR | Title | CI | Review | Updated | Chat |
```
- **PR**: `[`<pr>`](<url>)` + ` (draft)` if draft.
- **Title**: the PR title (truncate ~48 chars).
- **CI**, **Review**, **Updated**: passthrough.
- **Chat**: `[▶ resume](<chosen resume_link>) <🎯|💬> <chosen candidate title, ~34 chars>`, or `—`.

Keep links intact and CMD-clickable. Add a one-line legend:
`_🎯 branch match · 💬 best-matching chat · CMD+click ▶ resume → new Ghostty tab._`

## Then adapt to the environment (don't print the raw `env`)

- `handler_installed` false on `darwin`: tell them to run the one-time setup in
  `<SKILL_DIR>/setup.md` — links won't open a tab until then.
- `os` != `darwin` or `term` != `ghostty`: note the ▶ resume *tabs* are
  macOS+Ghostty-only; offer the portable fallback below for any row.
- All green: at most one line, only if it seems like a first run.

## Portable resume fallback (any OS/terminal)

Each candidate's chat is resumable without the handler — its `dir` + the session
id (the `__<id>` in the resume_link filename, or read line 2 of that file):
`cd <dir> && claude --resume <id> --dangerously-skip-permissions`. Offer this if
they're off macOS/Ghostty or a click isn't working.

## Setup / uninstall

One-time handler setup (builds `~/Applications/ClaudeResume.app` + macOS
Automation grant): follow `<SKILL_DIR>/setup.md`.
