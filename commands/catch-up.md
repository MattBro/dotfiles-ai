---
description: Brief me on this session as if I know nothing about it - the goal, what's done, open decisions with tradeoffs, and what you need from me. Use when I say "catch me up", or when I ask a status question ("what are you doing?", "what's the status?", "what do you need from me?", "where were we?"), especially right after resuming a session.
allowed-tools: Bash, Read
---

# Catch Me Up

Two situations trigger this, and both get the same treatment:

1. **I walked away mid-session** and came back with no memory of what was said.
2. **I resumed this session cold** - hours or days later, possibly one of many agents I'm juggling. I don't know what this agent is doing, what its goals are, what it has done, or what it's waiting on.

Either way: I have NOT been following along. Do not answer like a collaborator who saw your last message. Answer like you're handing off to a new stakeholder who needs the full picture in 30 seconds.

## Source the briefing

Work from the conversation context you already have, including any compaction summary. Do not re-read the jsonl transcript.

If the context is thin (long-resumed sessions often carry only a summary), reconstruct the current state from the environment instead of guessing:

- `git status`, `git log --oneline -10`, `git diff --stat` if the session touched code
- Current branch, whether it's pushed, and any associated PR (`gh pr view` if one likely exists)
- Background processes, agents, or workflows still running - mention them so I know they're alive
- Recently modified files if git doesn't tell the story

Skip checks that add no signal. If the session never touched code, don't run git.

## Output format

Lead with a one-line TL;DR, then the sections below. Whole thing readable in under 30 seconds.

```markdown
**TL;DR:** {one sentence - what this session is for and the single most important thing right now}

### Goal
{1-2 sentences. The high-level objective, stated as if I never said it myself. If the work drifted from the original ask, say so: "Started on X, currently on Y."}

### Done so far
- {completed, verified outcome}
- {completed, verified outcome}

### In flight / not closed out
- {uncommitted changes, unpushed branches, running processes, draft messages, half-finished edits}
- {skip this section if nothing is pending}

### Open decisions
- **{Decision}** - {option A: its tradeoff} vs {option B: its tradeoff}. Recommendation: {pick one, one line of why}.
- {skip this section if there are none - do not invent decisions to fill it}

### What I need from you
{The specific input you're blocked on, phrased so I can answer it in one message - give me the choices, not an essay prompt. If you're not blocked, write "Nothing - next I will {concrete action}" instead.}
```

## Style rules

- **Assume zero memory.** No "as you'll recall", no "as we discussed". I do not recall.
- **Expand every codename and shorthand invented during the session.** If something got called "the v2 approach" or "option B" along the way, define it on first use. I never saw the naming happen.
- **Name files, PRs, commits, and IDs explicitly.** Not "the file we were editing" - `path/to/file.py:42`. Not "the PR" - title and URL.
- **Outcomes, not play-by-play.** I don't need how we got here, I need current state and next step.
- **Flag anything forgotten that bites.** Running processes, an unsent draft, an unpushed branch, a question of yours I never answered.
- **Distinguish verified from assumed.** If "done" means "code written but never run", say that.
- **Drop the AI tells.** No "Great, here's a recap!", no "Let me know if you'd like more detail."
- **No em dashes.** Use hyphens or rewrite.
- **If the session is genuinely empty or trivial**, say that in one line. Don't pad.

## When the conversation is long

If there have been multiple distinct threads, organize "Done so far" by thread and call out the current thread explicitly. Don't summarize every tangent - focus on the live work.
