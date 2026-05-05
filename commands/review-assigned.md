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

## 3. Send Slack summary

After all reviews complete, compile the results and send a single Slack message.

**Always include the full PR URL in the Slack message AND in the terminal response.** Use Slack's `<url|text>` link syntax so the `repo#number` is clickable, and put the bare URL on its own line for easy copy-paste.

Slack format:

```
*PR Reviewer — {count} PRs reviewed*

*<{url}|{repo}#{number}>* — {title} (by @{author})
{count} comments: {critical} critical, {important} important, {suggestions} suggestions
Top issues:
• `{file}:{line}` — {one-line problem summary}
• `{file}:{line}` — {one-line problem summary}
Review: {url}

*<{url}|{repo}#{number}>* — {title} (by @{author})
…
```

If no PRs need review, send:

```
PR Reviewer — inbox zero, no reviews pending
```

Also trigger a macOS notification:

- Reviews done: "Reviewed {count} PRs — check Slack for details"
- Inbox zero: "No reviews pending"

## 4. Final terminal response

After sending the Slack message, always print a concise summary to the terminal with clickable PR URLs — this is what I'll see first in the CLI.

```
Reviewed {count} PRs:
- {repo}#{number} ({comment_count} comments): https://github.com/OWNER/REPO/pull/NUMBER
- {repo}#{number} ({comment_count} comments): https://github.com/OWNER/REPO/pull/NUMBER
```

Never reference a PR by `#number` alone without the full URL next to it — I need to be able to click through directly.

## Important

- NEVER post review comments to GitHub automatically — only present them and wait for approval in the `/review-pr` output
- Each agent running `/review-pr` should follow its full process (3 parallel analysis agents, dedup, de-AI, etc.)
- If a repo clone doesn't exist locally, skip it and note it in the Slack message
- The Slack summary should be concise — just the highlights, not the full review
