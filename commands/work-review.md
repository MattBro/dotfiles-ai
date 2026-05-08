---
description: Summarize my work over a date range — PRs, commits, meetings, Slack — across PostHog org repos only
allowed-tools: Bash, Read, Glob, mcp__granola__search_meetings, mcp__granola__get_meeting_details, mcp__slack__slack_search_public_and_private, mcp__slack__slack_search_users
---

# Work Review

Generate a markdown summary of my work over a date range. Useful for standup, weekly review, sprint retro, or self-reflection.

## Arguments

$ARGUMENTS — flexible date specifier. Examples:

- (empty) → last 7 days ending today
- `since last thursday`
- `since 4/27`
- `since 2026-04-27`
- `4/27..5/4` or `2026-04-27..2026-05-04` → explicit range

Parse the argument into `START_DATE` (ISO `YYYY-MM-DD`) and `END_DATE` (ISO, defaults to today). Use `date -v` (BSD) to resolve relative phrases. If the year is omitted in `M/D`, assume the most recent occurrence in the past (not the future).

## Scope

**Only include PostHog org work.** Exclude anything from `MattBro/*`, `brooker-family/*`, or other personal/family repos and channels. When in doubt, leave it out.

## Steps

### 1. Resolve the date range

Print the resolved range so the user can sanity-check:

```
Reviewing work from {START_DATE} to {END_DATE}
```

### 2. Gather PRs

Use `gh search prs` to find PRs I authored, updated in the window, in the PostHog org:

```bash
gh search prs --author=@me --owner=PostHog --updated=">=$START_DATE" --json number,title,url,state,isDraft,repository,updatedAt,closedAt,mergedAt --limit 100
```

Group results into:

- **Merged** — `mergedAt` falls in the window
- **Open (ready)** — open, not draft
- **Open (draft)** — open, draft
- **Closed unmerged** — closed without merge in the window (worth surfacing as wasted effort or pivots)

For each PR, render as `[repo#N — Title](url)`. Never bare PR numbers (per saved feedback).

### 3. Gather commits

For each PostHog org repo under `~/dev/*`, walk and check the remote:

```bash
for d in ~/dev/*/; do
  remote=$(git -C "$d" config --get remote.origin.url 2>/dev/null)
  case "$remote" in
    *PostHog/*|*posthog/*)
      git -C "$d" log --author="$(git -C "$d" config user.email)" \
        --since="$START_DATE" --until="$END_DATE 23:59" \
        --pretty=format:'%h %s' --no-merges
      ;;
  esac
done
```

Skip repos where the remote does not match. **Do not include any repo whose remote contains `MattBro` or `brooker-family`.**

Roll up commits per repo. If a commit's subject is already covered by a PR title above, do not duplicate it — fold it under the PR.

### 4. Gather Granola meetings

```
mcp__granola__search_meetings with date range START_DATE..END_DATE
```

Filter to meetings where the user actively participated (not just on the invite). For each meeting, include title, date, and a one-line takeaway from the summary. Skip 1:1s with no notable action items unless they look load-bearing.

**Do not include** anything from family/personal calendars or non-PostHog meetings. If a meeting title looks personal (e.g. doctor, school, family), drop it.

### 5. Gather Slack activity

Search for messages I sent in the window:

```
mcp__slack__slack_search_public_and_private with from:@me after:START_DATE before:END_DATE
```

Group by channel. Only include PostHog workspace channels — exclude DMs unless they contain substantive decisions. Summarize each channel's thread in 1-2 lines, not every message. Quote sparingly and only public-channel content (per `feedback_external_customer_comms` and `feedback_drafts_no_ai_tells` rules — never paste raw private Slack text into the output).

### 6. Render the summary

Output as markdown. Structure:

```markdown
# Work review: {START_DATE} → {END_DATE}

## Shipped
- [repo#N — Title](url) — one-line outcome
- ...

## In flight
- [repo#N — Title](url) — current state, any blockers
- ...

## Drafts / exploratory
- [repo#N — Title](url) — what it is

## Closed without merging
- [repo#N — Title](url) — why (if known)

## Commits not tied to a PR
- **repo**: short list

## Meetings
- **YYYY-MM-DD — Title**: one-line takeaway
- ...

## Slack threads
- **#channel**: what was discussed / decided
- ...

## Themes
{2-4 bullets clustering the work into coherent themes — what the week was actually about}
```

Skip any section that is empty.

### 7. Quality checks before finishing

- No em dashes anywhere (use hyphens or rewrite). Per saved feedback, this applies to my own output too.
- Every PR / issue / channel reference is a clickable link with a title, never a bare `#NNNN` or `#channel-name`.
- No file paths with trailing periods (breaks command-click).
- No personal / family / non-PostHog content leaked in.
- No raw private Slack/email/customer text pasted in.
- No time estimates (per `engineering.md` — "never estimate work in time units").

### 8. Offer to save

Ask: "Save this to `~/dev/.claude/docs/work-reviews/{START_DATE}_{END_DATE}.md`?" — only write if the user says yes.
