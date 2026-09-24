---
description: Investigate a PostHog Conversations support ticket - find root cause via git/code/PostHog data, verify whether a fix already shipped, then draft a customer-facing reply that strips internal references and AI tells
allowed-tools: Bash, Read, Grep, Glob, Agent, WebFetch, mcp__posthog__exec, mcp__slack__slack_read_thread
---

# Support Ticket Investigation + Reply Draft

Support tickets live in **PostHog Conversations** (`/support/tickets` in project 2), not Zendesk. Find the root cause, establish whether a fix has already shipped, and draft a clean customer reply.

This command works one ticket at a time. To find which tickets a team has open, use
`/support-queue <team>`, which sweeps the queue and returns a per-ticket recommendation. Reach
for it whenever the ask is "what's in my queue" rather than "what do I say to this person".

## Input

`$ARGUMENTS` may be a ticket number, a ticket UUID, a ticket URL, a Slack notification link, or pasted text. Fetch the ticket rather than asking Matt to paste it.

```text
posthog:exec({ "command": "call conversations-tickets-retrieve {\"id\":\"64882\"}" })
posthog:exec({ "command": "call conversations-tickets-messages-retrieve {...}" })
```

`conversations-tickets-retrieve` accepts the numeric ticket number or the UUID and returns status, assignee, tags, SLA, session replay URL, `session_context.current_url`, and the full person record. The response includes `_posthogUrl`, the staff-side ticket link - surface it verbatim at the top of the report.

For a Slack support-notification message, `slack_read_thread` gets the ticket number, then fetch the ticket for the real data. The Slack blurb is a summary, not a source.

## 1. Parse the ticket

From the ticket record, not from the Slack summary:

- Customer name, email, and their description of the symptoms
- `created_at` (the report time; the incident is usually earlier)
- `person.distinct_ids` - **capture all of them**, they matter in step 3
- `person.properties`: `joined_at`, `$geoip_time_zone` / project timezone, `is_organization_first_user`, `signup_backend_processor`, `onboarding_skipped_reason`
- Org id, project id, region (us / eu)
- `session_context.session_replay_url`, `current_url`

Convert every relative or local timestamp to UTC and state the offset you used. Screenshot filenames often carry a local timestamp; reconcile it against the customer's timezone before trusting any elapsed-time arithmetic.

If something obvious is missing, say so and investigate what you can rather than blocking.

## 2. Identify the product area

Common areas and their PostHog repo paths:

- **Onboarding / setup wizard** -> `frontend/src/scenes/onboarding/`, `posthog/api/wizard/`, `products/tasks/backend/`
- **Managed reverse proxy** -> `posthog/api/proxy_record.py`, `posthog/models/proxy_record.py`, `posthog/temporal/proxy_service/`, `frontend/src/scenes/settings/environment/{proxyLogic.ts,ManagedReverseProxy.tsx}`
- **Ingestion / events missing** -> `posthog/api/capture.py`, `rust/capture/`, `plugin-server/`
- **Billing** -> `ee/billing/`, `posthog/models/organization.py`, `posthog/api/billing.py`
- **Feature flags** -> `posthog/api/feature_flag.py`, `rust/feature-flags/`
- **Session recording** -> `ee/session_recordings/`, `posthog/session_recordings/`
- **Auth / login** -> `posthog/api/authentication.py`, `posthog/api/signup.py`
- **Data warehouse** -> `posthog/temporal/data_imports/sources/`
- **LLM analytics** -> `products/llm_observability/`

If the area isn't obvious, grep the repo for a distinctive string from the customer's screenshot or message. Verbatim UI copy is the fastest route to the responsible file.

## 3. Establish what actually happened to this customer

Do this **before** forming a code hypothesis. Reconstructing the customer's real timeline kills more wrong theories than reading code does.

### 3a. Query by distinct_id, never by person email

PostHog app telemetry lands in project 2, so the MCP can see it.

**Person-on-events means `person.properties.email` reflects the value at ingestion time.** Events from before identity merge carry no email and will be silently missing. Filtering on email will hand you a truncated timeline and a confident wrong answer.

```text
call execute-sql {"query":"SELECT timestamp, event, distinct_id, properties.$current_url AS url
FROM events WHERE distinct_id IN ('<all>','<of>','<them>')
AND timestamp >= '<start>' AND timestamp < '<end>'
ORDER BY timestamp ASC LIMIT 300","truncate":true}
```

Exclude noise (`$feature_flag_called`, `$autocapture`, `$pageview`, `$pageleave`, `$web_vitals`) to fit a real window in one query. If you hit the LIMIT, paginate. **Do not conclude from a truncated result set.**

### 3b. Follow the flow to its terminal event

Find the events that say how it ended, not just how it started. A run that emits `*_started` may well have emitted `*_completed` an hour later. Look for the terminal pair (`task_run_completed` / `task_run_failed`, `setup wizard finished`, `pr_merged`, `onboarding completed`) and the status property on it.

Never report a flow as broken because you only looked at its first minute.

### 3c. Sanity-check the account shape

`user signed up` + `is_organization_first_user` + `signup_backend_processor` distinguish a self-serve signup from a partner-provisioned one. Code paths gated on `isProvisionedUser` / `onboarding_skipped_reason` behave differently for each, so getting this wrong inverts the root cause. Check it, don't infer it from the absence of an event in a query that may have been filtered wrong.

## 4. Read the code, on fresh master

```bash
cd ~/dev/posthog && git fetch origin master --quiet
git log -1 --format="%h %ad %s" --date=short origin/master
```

**The local checkout is routinely weeks stale.** Always fetch, then read via `git show origin/master:<path>` or `git grep <pattern> origin/master`. Analysing a stale working tree produces conclusions about code that no longer exists.

Look for the change that explains the symptom in the days before the report:

```bash
git log --since="<report-4d>" --until="<report+1d>" \
  --pretty=format:"%h %ad %s" --date=short origin/master -- <paths>
```

Read any suspicious commit's diff in full with `git show <hash>`.

## 5. Fix status: has it already shipped? (mandatory gate)

**Run this immediately before writing the draft, and again before sending.** Fixes land continuously. A check performed at the start of the investigation is stale by the time the draft exists, and telling a customer "we're tracking this" about something that shipped hours ago is worse than saying nothing.

### 5a. Re-fetch and look for follow-up commits

```bash
cd ~/dev/posthog && git fetch origin master --quiet
git log --since="<report_date>" --pretty=format:"%h %an %ad %s" --date=short \
  origin/master -- <paths-from-step-2>
```

Also search by symptom, since the fix may sit outside the paths you identified:

```bash
gh search prs --repo PostHog/posthog --merged --limit 20 "<distinctive keyword>"
```

Read each candidate's diff and confirm it actually covers **this** customer's path. A matching title is not proof; the fix may address an adjacent case.

### 5b. Merged is not live - verify the deploy

Use the `posthog:checking-deploy-timing` skill, or directly:

```text
call annotations-list {"search":"deploy","limit":40}
```

Deploy markers are hidden `GIT` annotations reading `Deployed PostHog/posthog@<sha> to prod-us|prod-eu|dev`. They come back newest-first. Then prove the deployed commit contains the fix:

```bash
gh api repos/PostHog/posthog/compare/<fix_sha>...<deployed_sha> --jq '{status,behind_by}'
```

`behind_by: 0` means it shipped. Walk back through earlier deploys to find the first one containing it if you need a "live since" time. Check the customer's own region.

### 5c. Report one of three states, never a hedge

- **Shipped and live** - name the PRs, the deploy sha, and the time. The reply can say it's fixed and tell them what to do (usually reload).
- **Merged, not yet deployed** - say so, with the expected region.
- **Not fixed** - say "we're tracking this" in the reply and stop. Do not imply a fix exists.

If the customer needs no action because the fix is already live, that changes the entire reply. Do not draft the workaround version and then bolt a fix note on top.

## 6. Build the root cause hypothesis

Map each symptom to a mechanism in the code. If the mechanism doesn't fully explain the symptoms, keep digging. Don't ship a half-fit hypothesis.

A good hypothesis covers:

- What changed, or what state the customer landed in
- Why it hit this customer specifically (deploy window, cache, flag, plan, region, account type)
- Why the symptoms did or didn't self-resolve

State a confidence level (high / moderate / low) and name what you could not verify. If a claim rests on something you can't read (a DB row, their browser state), label it an inference, not a finding.

**If new evidence contradicts an earlier conclusion, correct it plainly and move on.** Don't defend the first theory.

## 7. Output the internal report

Print this for Matt. Internal references are fine here.

```
[Ticket #<n>](<_posthogUrl>) - <status>, <assignee>, SLA due <date>

## Root cause

<one paragraph>

## Verified timeline

| When (tz) | What |

## Why the symptoms match

| Symptom | Cause |

## Files

- <path:line> - <what>
- Commit `<hash>` ([#<PR>](https://github.com/PostHog/posthog/pull/<PR>))

## Fix status

Shipped and live / merged not deployed / not fixed - with PR links, deploy sha, deploy time
```

## 8. Draft the customer reply

**Load `writing-user-facing-copy` from the posthog repo before writing a word.** Its own
description says it governs support replies and to use it ALWAYS. Read it at
`~/dev/posthog/.agents/skills/writing-user-facing-copy/SKILL.md` when the session is outside the
repo and the skill does not load. The rules below are additional to it, not a replacement.

**Check the ticket is ours to answer first.** Billing is handled exclusively by the billing
engineers, and legal requests have their own escalation path. Pricing, invoices, plans, credits,
and add-on costs are billing. Drafting a reply for someone else's ticket wastes the work and
risks contradicting the person who owns it.

**Match the voice of the replies already on the ticket.** Read what support actually sent this
customer and write the next message in the same register. The house voice greets the customer by
name, explains the reasoning behind an answer rather than only stating it, lays out choices as
numbered options, recommends one, and closes warmly. A clipped, transactional reply about
someone's money or contract reads as hostile even when every fact in it is right.

Save to `~/dev/.claude/docs/drafts/<customer>_<short-slug>_reply.md` with the internal report in frontmatter plus a `## Draft reply (copy-paste ready)` section. Also print the reply in the conversation and link the saved file.

The reply body must be plain prose. No blockquote `>` markers, no code fences, no "Reply:" label. It gets pasted straight into the ticket.

### Strip internal references

- No file paths, line numbers, function names, class names, constant names
- No PR numbers, commit hashes, GitHub links
- No internal Slack channels, internal docs, internal team names
- No source code references - translate to product behaviour

### Drop the AI tells

- Scene-setting openers ("Quick update", "Just wanted to let you know")
- Affirmations ("Great question", "Thanks for flagging this")
- Mechanism explanations dressed as reassurance ("This is a known pattern", "We have safeguards in place")
- Intensifiers ("really", "definitely", "absolutely", "certainly")
- Generic closing reassurance ("Let us know if you need anything else!") in place of the warm, specific close the house voice uses
- Em dashes - use hyphens or restructure
- The rhetorical "X, not Y" contrast when Y adds emphasis rather than information

### Style

- **No longer than the house voice needs.** Cut every sentence that doesn't change what the customer knows or does; the greeting, the reasoning behind the answer, and the options stay.
- **Lead with the thing that changes their next action.** If their setup actually worked, that is the first sentence, with the concrete evidence. A customer sitting on a wrong belief needs it corrected before anything else.
- Give a concrete action they can verify in seconds (reload, retry, re-run) over an abstract status.
- The mechanism explanation is usually for us, not them. Cut it to one sentence or drop it.
- Sound like a human support engineer wrote it.

### Tone calibration

- Match their tone. A terse reporter gets a terse reply; a frustrated one gets the impact acknowledged first.
- One "sorry" line maximum.
- **Never promise a fix that isn't shipped.** "It should be fixed" is a hedge that is both unverifiable to them and often wrong. Either it's live (say so, tell them what to do) or it isn't (say we're tracking it).
- Add a one-line fallback ("if it's still there after a reload, tell us") whenever the outcome depends on state you cannot observe, like their browser.

### Final scrub

Read it back. If a coworker would roll their eyes, rewrite it. Re-run step 5 if more than an hour has passed since you checked.

## 9. Ask what's next

Offer to refine the wording, dig further, or post the reply via `conversations-tickets-reply-create`.

**Never send automatically.** Present for approval first, every time. An approval covers that draft only; a reworded draft needs a fresh go.
