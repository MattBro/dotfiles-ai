---
description: Save pertinent context from the current conversation to a markdown file for future reference
allowed-tools: Bash, Read, Write, Glob
---

# Save Conversation Context

Save the most important context from this conversation to a file in `.claude/docs/convos/`.

## Arguments

$ARGUMENTS — optional short label for the file (e.g. "stripe-webhook-bug"). If not provided, generate a short descriptive slug from the conversation topic.

## Steps

**The output directory `.claude/docs/convos/` already exists. Do NOT run mkdir.**

### 1. Get conversation ID

The conversation ID is the basename (without `.jsonl`) of the most recently modified jsonl in the project session dir. Find it:

```bash
PROJECT_SLUG=$(echo "$HOME" | sed 's|/|-|g')-dev
CONVO_ID=$(ls -t ~/.claude/projects/${PROJECT_SLUG}/*.jsonl 2>/dev/null | head -1 | xargs basename | sed 's/.jsonl//')
echo "Conversation ID: $CONVO_ID"
```

If `~/.claude/projects/` uses a different naming scheme on your machine, list the directory and pick the most recently modified `*.jsonl` matching the current working directory.

### 2. Determine the filename

If $ARGUMENTS was provided, use it as the slug. Otherwise generate a 2-4 word kebab-case slug from the main topic of the conversation.

Filename format: `{slug}_{convo_id_first8}.md`

Example: `stripe-webhook-bug_a5280f3f.md`

### 3. Review the conversation and extract context

Think about what's most useful to preserve for a future conversation that picks up this work. Focus on:

- **What we were working on** (1-2 sentences)
- **Key decisions made** and why
- **Current state** — what's done, what's left, any blockers
- **Important file paths** that were central to the work
- **Non-obvious findings** — things that took investigation to discover and would be costly to re-derive
- **Open questions** or next steps

Do NOT include:

- Full code snippets (the code is in the repo)
- Obvious things derivable from git log or file contents
- Conversation pleasantries or back-and-forth
- API keys, personal API keys, OAuth tokens, refresh tokens, webhook secrets, private keys, passwords, or copied credential values
- Raw private Slack/email/support text, customer identifiers, account IDs, org IDs, workspace IDs, or non-public meeting transcript excerpts
- Production command output unless it has been summarized and fully sanitized

### 4. Write the file

Write the context file to `.claude/docs/convos/{filename}` using this format:

```markdown
---
conversation_id: {full conversation ID}
date: {today's date YYYY-MM-DD}
topic: {one-line summary}
---

## Context

{What we were working on and why}

## Key Decisions

{Bulleted list of decisions and rationale — skip if none}

## Current State

{What's done, what's in progress, what's left}

## Important Files

{List of key file paths relevant to this work — skip if not applicable}

## Findings

{Non-obvious things discovered during investigation — skip if none}

## Next Steps

{What to do next — skip if work is complete}
```

Only include sections that have meaningful content. Skip empty sections entirely.

### 5. Confirm

Print the path to the saved file so the user can reference it.
