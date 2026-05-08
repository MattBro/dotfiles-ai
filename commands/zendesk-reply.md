---
description: Investigate a pasted Zendesk support ticket — find root cause via git/code/PostHog data, then draft a customer-facing reply that strips internal references and AI tells
allowed-tools: Bash, Read, Grep, Glob, Agent, WebFetch, mcp__posthog__exec
---

# Zendesk Ticket Investigation + Reply Draft

The user pastes a Zendesk-style support ticket. Find the root cause and draft a clean customer reply.

## Input

`$ARGUMENTS` — usually the ticket text is already pasted in the conversation. If a ticket URL or ID is provided, ask the user to paste the body.

## 1. Parse the ticket

Extract from the pasted text:

- Customer name + their description of the symptoms
- Reported timestamp (the message date, e.g. `Feb 18 06:08`)
- Session replay URL (if present, e.g. `https://us.posthog.com/project/.../replay/...`)
- Error tracking URL (if present)
- Admin URL → org ID, project ID, user ID
- Region (us / eu) — from the URL host

Convert relative timestamps to absolute. The ticket message date is the **report time**; the actual incident is usually shortly before that.

If the ticket is missing any obvious pieces (no project ID, no timestamp), ask the user to clarify before investigating.

## 2. Identify the product area

From the customer's description, pick which area to investigate. Common areas and their PostHog repo paths:

- **Managed reverse proxy** → `posthog/api/proxy_record.py`, `posthog/models/proxy_record.py`, `posthog/temporal/proxy_service/`, `frontend/src/scenes/settings/environment/{proxyLogic.ts,ManagedReverseProxy.tsx}`
- **Ingestion / events missing** → `posthog/api/capture.py`, `rust/capture/`, `plugin-server/`
- **Billing** → `ee/billing/`, `posthog/models/organization.py`, `posthog/api/billing.py`
- **Feature flags** → `posthog/api/feature_flag.py`, `rust/feature-flags/`
- **Session recording** → `ee/session_recordings/`, `posthog/session_recordings/`
- **Auth / login** → `posthog/api/authentication.py`, `posthog/api/signup.py`
- **Data warehouse** → `posthog/temporal/data_imports/sources/`
- **LLM analytics** → `products/llm_observability/`

If the area isn't obvious, search the repo for keywords from the customer's description.

## 3. Investigate

Run these in parallel where possible.

### 3a. Git history around the incident

The most common root cause is a recent change. Look at commits in the affected area in the **3 days before** the report:

```bash
cd ~/dev/posthog
REPORT_DATE="2026-02-18"  # from the ticket
SINCE_DATE=$(python -c "from datetime import date,timedelta; d=date.fromisoformat('$REPORT_DATE'); print((d-timedelta(days=4)).isoformat())")
UNTIL_DATE=$(python -c "from datetime import date,timedelta; d=date.fromisoformat('$REPORT_DATE'); print((d+timedelta(days=1)).isoformat())")

git log --since="$SINCE_DATE" --until="$UNTIL_DATE" --pretty=format:"%h %ad %s" --date=short -- <paths-from-step-2>
```

Look for:

- Non-backwards-compatible API contract changes (response shape, field renames, removed fields)
- Deploys that landed within hours of the report
- Migrations
- Feature flag rollouts (look for `posthoganalytics.feature_enabled` or related)
- "remove", "rename", "refactor" in commit messages on hot paths

For any suspicious commit, run `git show <hash>` and read the diff in full.

### 3b. Customer state in PostHog (via MCP)

Use the `posthog:exec` tool to check the customer's actual state. Examples:

```text
# Check error tracking issues for the session
posthog:exec({ "command": "info query-error-tracking-issues" })
posthog:exec({ "command": "call query-error-tracking-issues {...}" })

# Check whether events arrived during the incident window
posthog:exec({ "command": "call execute-sql {\"query\":\"SELECT count() FROM events WHERE team_id = <project_id> AND timestamp BETWEEN '...' AND '...'\",\"truncate\":true}" })
```

The MCP is currently scoped to the project listed in the active environment block — if the customer's project isn't accessible, note that and skip this step rather than guessing.

### 3c. Read the suspicious code

For each candidate commit found in 3a, read the full file at HEAD and the diff. Confirm the symptoms match.

### 3d. Look for follow-up fixes

```bash
git log --since="$REPORT_DATE" --until="<today>" --pretty=format:"%h %ad %s" --date=short -- <paths>
```

If there's already a follow-up fix, mention it in the internal summary so we know whether the customer is still affected.

## 4. Build the root cause hypothesis

Map each symptom the customer described to a mechanism in the code. If the mechanism doesn't fully explain the symptoms, keep digging — don't ship a half-fit hypothesis.

A good hypothesis covers:

- What changed (commit + PR)
- Why it broke for this customer specifically (deploy window, cache, feature flag, plan, region, etc.)
- Why the symptoms self-resolved (if they did)

If you can't reach a confident hypothesis, say so — don't fabricate one.

## 5. Output the internal report

Print this **for me** (matt) — internal references are fine here:

```
## Root cause

<one paragraph>

## Why the symptoms match

| Symptom | Cause |
| ... | ... |

## Files

- <path:line> — <what>
- Commit `<hash>` ([#<PR>](https://github.com/PostHog/posthog/pull/<PR>))

## Status of fix

<is there a follow-up fix? is the customer still at risk?>
```

## 6. Draft the customer reply

Save the reply to a file at `~/dev/.claude/docs/drafts/<customer>_<short-slug>_reply.md`. The slug should describe the issue area in 2-4 kebab-case words (e.g. `acme_managed_reverse_proxy_reply.md`). Use this format:

```markdown
---
ticket: <UUID if present>
customer: <name>
org: <org name> (<org id>)
project: <project name> (<project id>)
report_date: <YYYY-MM-DD>
draft_date: <today YYYY-MM-DD>
---

## Root cause (internal)

<the internal report from step 5, condensed>

---

## Draft reply (copy-paste ready)

<reply text — plain prose, NO blockquote `>` markers, NO surrounding fence, NO leading "Reply:" label. The customer pastes this directly into Zendesk, so it must be paste-clean.>
```

The reply body must be plain prose — do NOT prefix lines with `>` or wrap in code fences. Use hyphens (` - `) for inline asides instead of em dashes.

Then also print the reply in the conversation under `## Draft reply for <customer name>` and include a line pointing to the saved file.

The reply MUST follow these rules (from auto-memory):

### Strip internal references

- No file paths, line numbers, function names, class names, constant names
- No PR numbers, commit hashes, GitHub links
- No internal Slack channels, internal docs, internal team names
- No source code references — translate to product behavior

### Drop the AI tells

Banned (rewrite if found):

- Scene-setting openers ("Honest update on where this lands", "Quick update", "Just wanted to let you know")
- Affirmations ("Great question", "Thanks for flagging this — really helpful")
- Mechanism explanations dressed up as reassurance ("This is a known pattern", "We have safeguards in place")
- Intensifiers ("really", "definitely", "absolutely", "certainly")
- Closing reassurance ("Let us know if you need anything else!", "Happy to help further!")
- Em dashes — use hyphens or restructure

### Style

- Lead with what we found, in plain product terms
- Explain why they saw what they saw
- Give them a workaround (hard refresh, retry, etc.) if applicable
- Acknowledge briefly, thank briefly, sign off briefly
- 4-6 short paragraphs max
- Sound like a human support engineer wrote it, not an AI

### Tone calibration

- Match the customer's tone — if they were polite and detailed, be warm but concise; if they were frustrated, lead with acknowledgment of the impact
- Don't over-apologize. One "sorry for the trouble" line is enough
- Don't promise fixes that aren't shipped — if there's no follow-up fix, say "we're tracking this" and stop

### Final scrub

Read the draft aloud mentally. If a coworker would roll their eyes, rewrite it. If it sounds like ChatGPT, rewrite it.

## 7. Ask what's next

After printing the internal report and the draft reply, ask:

- Want me to refine the wording?
- Should I dig further (e.g. check this customer's specific state, look for repeat occurrences across other tickets)?
- Anything to add or remove from the draft?

Do NOT send the reply anywhere automatically — always present it for approval first.
