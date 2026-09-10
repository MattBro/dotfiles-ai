---
description: Sweep a team's PostHog support queue, find every unresolved ticket including the ones the team view hides, check whether promised fixes have since shipped, and report a per-ticket recommendation
allowed-tools: Bash, Read, Grep, Glob, Agent, WebFetch, mcp__posthog__exec
---

# Support Queue Sweep

Find every open support request for a team and say what to do about each one.

`$ARGUMENTS` is a team name (`growth`, `replay`, `feature flags`). Default to the team whose
code the session is working in; if that is ambiguous, ask once, then proceed.

This command finds and triages tickets. To investigate one ticket in depth and draft the
customer reply, use `/conversation-reply <ticket>`.

## The trap: the team view lies

**Never answer from the saved team view alone.** A team view returns zero while the team has
nine open tickets, because the saved filters exclude most of them:

- `status` is usually `new,open,on_hold`, which **excludes `pending`**. Pending means "we
  replied, waiting on the customer", and that is where answered-but-never-closed tickets pile
  up. Most of a team's live queue is pending.
- `assignee` is usually the team **role**, which **excludes tickets assigned to individuals**.
  The support-hero handbook says it outright: anything left assigned to a person does not show
  up in the team view.

So an empty team view is evidence about the view, not about the queue. Always sweep by tag as
well, and say so in the report when the two disagree.

## 1. Resolve the team's view and tag

```text
call conversations-views-list {"limit":100}
```

Views are named `Team <name>`. Take the `short_id`. Then read its saved filters, which is how
you learn what it hides:

```text
call conversations-views-retrieve {"short_id":"<short_id>"}
```

Record the `assignee.id` (the team role uuid) and the `status` list. Both go in the report when
they explain a discrepancy.

The tag is `team_<name>` in snake case (`team_growth`, `team_feature_flags`). Tickets also carry
`support_sme_<area>` tags and an `ai-task:<uuid>` tag from triage.

## 2. Sweep, widest first

Run all three. They find different tickets.

```text
# a. by tag, every unresolved status. This is the one that finds the whole queue.
call conversations-tickets-list {"tags":"[\"team_<name>\"]","status":"new,open,pending,on_hold","date_from":"all","limit":50,"order_by":"-created_at"}

# b. the team view as saved, to see what the team believes its queue is
call conversations-tickets-list {"view":"<short_id>","limit":60}

# c. recently closed, for context on what the team just handled
call conversations-tickets-list {"view":"<short_id>","status":"new,open,pending,on_hold,resolved","date_from":"-30d","limit":60}
```

Then check for tickets that should be the team's but were never routed:

```text
call conversations-tickets-list {"assignee":"unassigned","status":"new,open,pending,on_hold","channel_source":"widget","date_from":"all","limit":40,"order_by":"-created_at"}
```

**Filter the unassigned sweep to `widget` and `email`.** The unassigned pool runs to hundreds of
tickets and is dominated by internal Slack threads: papercuts, PR-shepherding bots, team
chatter. Those are not customer support requests. `channel_source` of `widget` or `email` is
what isolates genuine customer reports.

Check an unrouted ticket's `tags` before claiming it belongs to the team. A ticket tagged
`team_replay` is Replay's, whatever it appears to be about.

`assignee` accepts `unassigned`, `me`, `user:<id>`, and `role:<uuid>`, comma-separated.

## 3. Read each ticket's last message, not its subject

The last message decides the recommendation, and it is in the list response as
`last_message_text`. Three shapes recur:

- **The customer already confirmed it works** ("It worked, thank you!") and the ticket is still
  pending at high priority. Nothing to do but close it.
- **Support answered fully** and nobody closed the ticket. Close it.
- **Support promised something** ("retiring soon", "we're tracking this", "I'll check with the
  team"). This is the one that needs work. Go to step 4.

For full detail on one ticket:

```text
call conversations-tickets-retrieve {"id":"<ticket_number or uuid>"}
```

The response carries `tags`, `person.properties`, `session_context`, and `_posthogUrl`. Surface
`_posthogUrl` verbatim. Its `_agentNote` points at `inbox-reports-list` for any prior AI
investigation, which holds findings the ticket messages do not.

## 4. Check whether the promise has since shipped (mandatory)

Every "we're tracking it" and "retiring soon" is a claim with a date on it. Support wrote it
weeks ago. Verify it against master before repeating it to anyone.

```bash
cd ~/dev/posthog && git fetch origin master --quiet
git grep -n "<symptom keyword>" origin/master | head
gh search prs --repo PostHog/posthog --merged --limit 20 "<keyword>"
```

Merged is not live. Confirm the deploy:

```text
call annotations-list {"search":"Deployed","limit":15}
```

Take the newest `prod-us` (or `prod-eu`, matching the customer's region) sha, then prove it
contains the fix:

```bash
gh api repos/PostHog/posthog/compare/<fix_sha>...<deployed_sha> --jq '{status,behind_by}'
```

`behind_by: 0` means it shipped. Anything else means it has not.

### What a shipped fix actually means for the ticket

**Usually: resolve it, and send nothing.** The handbook standard is to refer the customer to the
GitHub issue and solve the ticket. The linked issue is where they track it, so a later "it
shipped" reply is not owed and is usually noise.

A follow-up reply is owed only when someone deliberately opted into carrying it. That is what
`on_hold` plus a snooze is for: the handbook names "a PR in review, and you intend to let the
customer know once it ships" as its use case. If the ticket is `on_hold` with a snooze, send the
update. If it is `pending`, the status is already wrong.

So the recommendation a shipped fix produces is nearly always **"resolve this"**, not "reply".
Reserve a reply for a ticket whose customer still has to do something, or whose question was
never answered.

### Status is the finding, not a footnote

Read every ticket's status against what the handbook says it means:

- `pending` means waiting on the customer. A ticket where we owe nothing and they owe nothing is
  mis-statused, not open work.
- `on_hold` must be paired with a snooze, or it sits forever.
- `resolved` is correct once you are 90% confident the response settles it. It does not require
  the customer to confirm.

Tickets parked in `pending` are the most common finding in a sweep, and they are the reason a
team view reads empty while the queue is not. Report the mis-statused ones as a group.

## 5. Look across the tickets, not just at each one

Per-ticket recommendations miss the findings that matter most. Check for:

- **The same complaint twice.** Two customers hitting one confusion within days is a product
  defect, not two support requests. Name the fix, not the two replies.
- **A tag collecting work the team does not own.** If most of a team's tickets are legal,
  billing, or another team's product, the routing is wrong. Say so.
- **Tickets aging in `pending` with no customer reply.** Pending is not a parking space.

## 6. Report

Lead with what to act on. Group by action, not by date or priority.

```
## Why the view disagrees

<one line, only when the view count and the tag count differ, naming the excluded status and assignee filter>

## Act on these

| Ticket | Do this |

## Resolve these, the work is done

- <linked ticket> - <one line on what settled it, and no reply unless it says otherwise>

## Leave these

- <linked ticket> - <what it is waiting on>

## Worth questioning

<cross-ticket patterns from step 5, or omit the section>
```

Every ticket gets a link with a plain-English name, never a bare number:
`[71046 - HIPAA BAA coverage and the is_hipaa flag](https://us.posthog.com/project/2/support/tickets/<uuid>)`.
Same for every PR and issue you cite as evidence.

State a confidence level. High for anything verified against master and a deploy annotation,
lower for a call made from ticket text alone.

## 7. Offer the next step

Name the one or two tickets worth a full `/conversation-reply` pass and stop. Do not draft
customer replies during a sweep, and never post or resolve anything without being asked.
