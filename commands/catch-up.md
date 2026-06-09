---
description: Catch me up on this session as if I just walked back to my desk. Assume zero memory of what was said.
allowed-tools: Bash, Read
---

# Catch Me Up

I walked away from this Claude Code session and came back. I do not remember anything we talked about, anything I asked, or anything you said. Brief me like a colleague who's been watching my screen — what was I doing, where did I leave off, what's the next move.

## Source the briefing from this conversation

You already have the full conversation in your context window. Do NOT try to re-read the jsonl transcript — work from what you have. The point of this command is to *synthesize* a "where are we" briefing from the existing context, not to dig up new information.

Supplement with quick environment checks when relevant:

- `git status` and `git log --oneline -5` if we're in a git repo and have been editing code
- `git diff --stat` if there are uncommitted changes worth flagging
- Look at any background processes still running (build watchers, dev servers, agents) — mention them so I know they're alive

Skip checks that don't add signal. If we were drafting a Slack message and never touched code, don't run git.

## Output format

Lead with a one-line TL;DR. Then the sections below. Keep it short — I should be able to read the whole thing in under 30 seconds and know exactly what to do next.

```markdown
**TL;DR:** {one sentence — what we're doing and what the next move is}

### What we're working on
{1-2 sentences. The original goal, not the latest tangent. If we've drifted, say so: "Started on X, currently on Y."}

### What's done
- {completed step}
- {completed step}

### Where we left off
{The most recent state. What was the last thing you did or said? What was I about to do? If there's an unanswered question waiting for me, lead with that.}

### Pending / in flight
- {uncommitted changes, running processes, open PRs, draft messages — anything not yet closed out}
- {skip this section if nothing is pending}

### Suggested next step
{One concrete action. Not a menu of options — your best read on what I should do next.}
```

## Style rules

- **Assume zero memory.** Don't say "as you'll recall" or "we were just talking about". I do not recall. I was not just talking about it.
- **Name files, PRs, commits, and IDs explicitly.** Don't say "the file we were editing" — say `path/to/file.py:42`. Don't say "the PR" — give the title and URL.
- **No recap of *how* we got there.** I don't need the play-by-play. I need the current state and the next step.
- **Flag anything I might have forgotten that bites.** Background processes still running, a draft Slack message I never sent, a branch I never pushed, a question from you I never answered.
- **Drop the AI tells.** No "Great, here's a recap!", no "Let me know if you'd like more detail." Just the briefing.
- **No em dashes.** Use hyphens or rewrite.
- **If the session is genuinely empty or trivial** (just started, only small-talk so far), say that in one line. Don't pad.

## When the conversation is long

If we've been at this for a while and there have been multiple distinct threads, organize "What's done" by thread and call out the *current* thread explicitly. Don't try to summarize every tangent — focus on the live work.
