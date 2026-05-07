---
description: Find PRs where I'm a requested reviewer, review each one, and send a Slack summary
allowed-tools: Bash, Read, Grep, Glob, Agent, WebSearch, WebFetch, Skill, mcp__slack__slack_send_message, mcp__slack__slack_search_channels
---

# Review Assigned PRs

Find all PRs assigned to me for review that I haven't reviewed yet, run `/review-pr` on each, and send a Slack summary.

## Notification setup

```bash
# Set in your shell rc:
#   export SLACK_BABYSITTER_WEBHOOK="https://hooks.slack.com/services/..."

if [ -z "$SLACK_BABYSITTER_WEBHOOK" ]; then
  echo "SLACK_BABYSITTER_WEBHOOK not set — Slack notification will be skipped"
fi

GH_USER=$(gh api user --jq .login)
```

Send Slack messages with:

```bash
if [ -n "$SLACK_BABYSITTER_WEBHOOK" ]; then
  curl -s -X POST -H 'Content-type: application/json' \
    --data '{"text":"<message>"}' \
    "$SLACK_BABYSITTER_WEBHOOK"
fi
```

macOS notification:

```bash
osascript -e 'display notification "<brief summary>" with title "PR Reviewer" sound name "default"'
```

## 1. Find PRs awaiting my review

```bash
# Set in your shell rc, space-separated:
#   export REVIEW_REPOS="PostHog/posthog PostHog/posthog-js"
REVIEW_REPOS="${REVIEW_REPOS:-PostHog/posthog PostHog/posthog-js}"

for repo in $REVIEW_REPOS; do
  gh pr list --repo "$repo" --search "review-requested:@me" --state open --json number,title,url,author,headRefName
done
```

Filter out PRs that already have reviews:

```bash
# For each PR, check total review count from non-bot reviewers
gh api "repos/<owner>/<repo>/pulls/<number>/reviews" --jq '[.[] | select(.user.type != "Bot")] | length'
```

If the count is > 0, someone has already reviewed it — skip it. Only keep PRs with zero human reviews.

Also filter out PRs I've already reviewed:

```bash
gh api "repos/<owner>/<repo>/pulls/<number>/reviews" --jq "[.[] | select(.user.login == \"$GH_USER\")] | length"
```

If > 0, I've already reviewed it — skip.

## 2. Review each PR

For each PR that still needs my review, use an agent to run the `/review-pr` skill:

- Spawn one agent per PR, running them in parallel
- Each agent should:
  1. `cd` into the appropriate local repo clone (e.g. `~/dev/<repo-name>`)
  2. Run `/review-pr <PR number>` via the Skill tool
  3. Return the full review output (the numbered list of comments)

Collect all review results.

## 3. Send Slack ping (terse — feedback stays in this session)

Do NOT dump per-PR findings into Slack. Findings stay in this Claude Code session; Slack is just a "come look" ping.

Build the message: list each reviewed PR by `repo#number` + title + author + severity counts so I can decide which to open first. Skip per-finding bullets, top-issue excerpts, and the per-PR `Review:` URL footer.

Get the current session id so the Slack message can include a resume command:

```bash
PROJECT_DIR=~/.claude/projects/$(pwd | sed 's|/|-|g')
SESSION_ID=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1 | xargs -I{} basename {} .jsonl)
if [ -z "$SESSION_ID" ]; then
  RESUME_CMD="cd $(pwd) && claude -c"   # fallback: continue most recent in this dir
else
  RESUME_CMD="cd $(pwd) && claude --resume ${SESSION_ID}"
fi
```

Slack format:

```
*PR Reviewer — {count} PRs reviewed, feedback ready*

• <{url}|{repo}#{number}> — {title} (@{author}) — {comment_count} comments ({critical}c/{important}i/{suggestions}s)
• <{url}|{repo}#{number}> — {title} (@{author}) — {comment_count} comments ({critical}c/{important}i/{suggestions}s)

Pick up the convo:
`{RESUME_CMD}`
```

If no PRs need review:

```
PR Reviewer — inbox zero, no reviews pending
```

macOS notification:

- Reviews done: `"Reviewed {count} PRs — feedback ready in Claude Code"`
- Inbox zero: `"No reviews pending"`

## 4. Final terminal response

Print a concise summary to the terminal — clickable PR URLs and the resume command.

```
Reviewed {count} PRs:
- {repo}#{number} ({comment_count} comments, {critical}c/{important}i/{suggestions}s): https://github.com/OWNER/REPO/pull/NUMBER
- {repo}#{number} ({comment_count} comments, {critical}c/{important}i/{suggestions}s): https://github.com/OWNER/REPO/pull/NUMBER

Resume this session anytime: claude --resume {SESSION_ID}
```

Then offer to walk through the findings PR-by-PR and post when I approve. Never reference a PR by `#number` alone without the full URL next to it.

## Important

- NEVER post review comments to GitHub automatically — only present them and wait for approval
- Each agent running `/review-pr` follows its full process (analysis agents, verification gate, audit pass)
- If a repo clone doesn't exist locally, skip it and note it in the Slack message
- Findings live in this session, not in Slack — Slack is the doorbell, not the inbox
