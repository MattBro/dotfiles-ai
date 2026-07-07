---
description: Tag @posthog in Slack #claude-code-notifier to delegate a task to the PostHog Claude Code agent. Drafts a tight, actionable message and sends it directly.
allowed-tools: mcp__slack__slack_send_message, Bash, Read
---

# Tag @posthog in Slack to delegate a task

Use when the user wants to delegate a task to the @posthog Claude Code agent in #claude-code-notifier rather than doing it locally. Common framings: "ask @posthog to drop X", "have @posthog fix Y", "tag @posthog for this", "delegate this to @posthog".

## Channel and tag (constants)

- Channel ID: `C0AKRM9P6VD` (#claude-code-notifier, private)
- Tag: `<@U03M3FNJ676|PostHog>` — render in the message exactly as shown so Slack resolves it as a real mention.

## Message format

Convention seen in past delegations in this channel:

```
<@U03M3FNJ676|PostHog> <RepoOwner>/<repo-name> <action verb> <concrete description with file:line refs>
```

Working example (the introspection-scope drop, sent 2026-05-07):

```
<@U03M3FNJ676|PostHog> PostHog/wizard drop the `introspection` scope from the authorize URL at `src/utils/setup-utils.ts` around line 495. It's not in `posthog/scopes.py` (the canonical scope list), isn't grantable, and the authorization server rejects it as `invalid_scope`. One-line removal plus any test updates. Verify token introspection still works without it as a granted scope (introspection is an endpoint per RFC 7662, not a scope).
```

Adversarial-review example pattern (also seen in the channel, useful for review tasks rather than fix tasks):

```
<@U03M3FNJ676|PostHog> PostHog/posthog adversarially review <PR URL> — find bugs, security issues, and edge cases I missed. Don't fix anything, just review.

Areas to scrutinise:
- <area 1>
- <area 2>

For each issue: file:line, what's wrong, why it matters, suggested fix. Skip nitpicks and style.

When you're done, post your findings as a reply in this Slack thread so I can see them.
```

## Style rules

- Lead with the action verb (drop, add, fix, refactor, run, review, audit).
- Name the exact file and line if known. Quote constants and identifiers in backticks.
- One sentence on context if it's not obvious from the task description alone.
- Add an acceptance or verification step when the change isn't a trivial one-liner.
- Drop AI tells: no greetings, no "can you / could you", no closing reassurance, no padding. Apply the conversational-style memory entries (no em dashes, no "X, not Y" rhetorical contrast, no scene-setting openers).
- Don't @-mention any other PostHog reviewer in the body; the @posthog agent is the recipient.

## Steps

1. Take the task from `$ARGUMENTS`. If the user's request is ambiguous, ask one clarifying question (which repo, which file, what's the acceptance criteria) before sending.
2. Identify the target repo. Common ones:
   - `PostHog/posthog` — main monorepo
   - `PostHog/wizard` — posthog-wizard CLI (sometimes referred to as "the wizard")
   - `PostHog/posthog.com` — public docs site
   - `PostHog/billing` (`billing-admin-provider` locally) — billing service
   - `PostHog/charts` — k8s charts
   Default is `PostHog/posthog` if the task wording makes the repo obvious; otherwise ask.
3. Format the message per the convention above.
4. Send via `slack_send_message` to `C0AKRM9P6VD` directly (not draft) — this channel's established pattern is to send tasks straight, since the user delegated the action and the @posthog agent will draft a PR which the user reviews before any code lands.
5. **The mention alone won't trigger the agent** (observed 2026-07-07): messages sent through the Slack MCP carry a "Sent using Claude" footer and the @posthog agent ignores them, even though the mention renders correctly. After sending, tell the user to drop a bare `@PostHog` tag as a reply in the message's thread — that human mention is what starts the task (the agent replies "Working on task…" in-thread).
6. Return the message link so the user can follow the agent's response thread, and remind them to tag @PostHog in-thread to kick it off.

## When not to use

- The task is local and reversible — just do it directly.
- The task affects production / shared state without explicit user authorization.
- The user wants to draft for review rather than send — use `slack_send_message_draft` instead.
- The task involves a Slack Connect channel (external customer channels) — the @posthog agent operates inside this private channel only.
