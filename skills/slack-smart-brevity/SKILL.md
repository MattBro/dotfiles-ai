---
name: slack-smart-brevity
description: >-
  Compose Slack messages in Smart Brevity format: audience-first, lead with the
  news, skimmable, with an opus reviewer pass. Draft only, never sends.

  UNCONDITIONAL TRIGGER. Read before writing any Slack message, reply, thread
  response, update, or announcement on Matt's behalf, and before any call to
  slack_send_message_draft. Applies even when the request is worded "send X to
  #channel", "reply to that thread", or "let the team know". Also use when
  asked to "smart brevity" any text.

  SKIP the review loop when the whole message is one line: an ack or
  single-sentence answer has nothing to compress. Draft it anyway, never send.
---

# Slack Smart Brevity (draft only)

A Slack message should give the reader the whole point in about 10 seconds and
earn any further reading. Messages drafted from the writer's head open with
backstory and bury the ask. This skill forces the reader's-eye view.

Step order matters. Compression protects whatever the draft already emphasizes,
so audience need comes first; compression also rewrites claims, so facts get
re-checked after it, against source.

**Never send.** `claude/slack.md` carries the rule and the drafting mechanics
(`thread_ts`, `draft_already_exists`, Slack Connect, markdown flavor). Short
version: `slack_send_message_draft` only, echo the draft in chat too.

## Step 0: proportionality

One-line messages skip the whole flow, including the review. An ack or
single-sentence answer has nothing to compress. It still needs the two-second
basics: you read what you're replying to, the claim is true, right thread.

The full loop is for anything with structure to get wrong: updates,
announcements, asks with context, any multi-sentence reply.

Incident comms keep the format but skip Step 5; speed serves the reader there.
Never skip Step 4, since wrong numbers in incident comms compound the incident.

## Step 1: gather context

- Thread reply? Read it first with `slack_read_thread`. Never draft a reply from
  memory of a thread you have not read this session.
- New channel message? Skim with `slack_read_channel`. Tone and prior context
  live there.
- Write the audience in one line: who reads this, what they already know, what
  they need from this message. That line feeds the reviewer.

## Step 2: reflect before drafting

One line each, to yourself:

1. Goal: inform, ask, decide, or unblock?
2. The ONE main point. Two points means two messages.
3. What the reader needs and does not already have, and what to leave out.
4. The ask, if any: who does what, by when?
5. What is awkward here (a delay, bad news, work someone else offered to do, a
   decision that overrode them)? The draft addresses it head-on, usually in the
   lede. Flagging the risk to Matt while leaving the dodge in the message is not
   a fix.

## Step 3: draft in Smart Brevity

- Line 1 carries the news, bolded. No greeting, no "just wanted to...".
- If the message exists to make an ask, the ask IS line 1, owner and deadline
  explicit. A buried ask gets skimmed past.
- "Why it matters" is a question, not a slot: what changes for this reader? If
  nothing changes, drop the section.
- Bolded lead-ins on bullets. Signposts where they fit: *What happened*, *By the
  numbers*, *What's next*, *The bottom line*.
- One idea per bullet. Numbers over adjectives ("builds ran 14 min instead of 5"
  beats "much slower"). No hedges, no jargon this audience lacks.
- 150 words is the default ceiling, not the goal. A lede that owns a delay earns
  its length; compression that keeps exposition and cuts what changed for the
  reader is worse than being long. Depth, logs, and code go in a thread reply.
- Edit pass: draft, then cut roughly in half.

Style rules that override the above:

- **No em dashes.** Rewrite the sentence; spaced hyphens are not a substitute.
- **No `~` for "approximately"**, Slack pairs single tildes into strikethrough.
  Write "about 14 min".
- **Just the facts.** No greetings, hedging, or unsolicited suggestions. Matt
  adds his own framing.
- **No AI tells**: scene-setting openers, affirmations, unrequested mechanism
  explanations, closing reassurance ("hope that helps").
- **Links, not bare identifiers.** Real URLs, PR references carry the title.
- **External or Slack Connect**: no internal file paths, constant names, or
  source links. Product-facing only.
- **Security threads**: draft to Matt only, never carry an unverified sub-agent
  claim into one.

## Step 4: verify against source

Compression rewrites claims. Re-check every number, count, name, date, and
quoted phrase against its source (the thread, the file, the command output),
never against the previous draft. That is how a seven becomes "six files" and
survives three versions. The reviewer only sees the draft, so facts are yours.

Then sweep for placeholders, TODOs, and lines addressed to Matt rather than the
audience ("@Pat needs to grant access first").

## Step 5: audience review (subagent)

One reviewer via the Agent tool: `subagent_type: general-purpose`, `model: opus`,
`run_in_background: false`. It stands in for the busy reader doing a fit check on
under 150 words. Its diagnosis is what you keep, so it gets a strong model. With
no subagent available, run the checklist yourself as a separate explicit pass.

```
Review this draft Slack message for audience fit. Be terse and concrete.

Audience: [who reads this + what they already know]
Goal: [inform/ask/decide/unblock] | main point: [one line] | ask: [who/what/when, or "none"]

Draft:
---
[draft]
---

Standard: Smart Brevity, audience first. The message serves what the reader needs.

Check in order:
1. Does line 1 alone give the reader the point?
2. If there is an ask: unmissable, owner + deadline explicit, and leading the
   message when the message exists to ask?
3. Exactly one main point?
4. Anything the reader already knows or does not need? Quote it, say cut.
5. Jargon or missing context for THIS audience?
6. Over 150 words, or formatting Slack renders badly (# headers, single tildes
   around numbers)?
7. Is it avoiding something awkward it should address head-on (a delay,
   superseded work, an overridden offer)?
8. Placeholders, bare issue/PR numbers without links, or lines addressed to the
   sender rather than the audience?
9. Em dashes, greetings, hedges, or closing reassurance to cut?

Return "SHIP" or up to 5 numbered edits, each quoting the text to change and
giving a replacement. No praise. No full rewrite.
```

## Step 6: apply and deliver

- Apply the edits you agree with. The reviewer advises, you decide. Trust its
  diagnosis over its remedy: reviewers name what is wrong precisely, including
  social risks, but their fixes for social problems run cosmetic (add a
  compliment) where the real fix is structural (own it in the lede).
- One round only. Re-review only if the goal itself changed.
- Create the draft with `slack_send_message_draft` and print the final text in
  chat with the channel and thread it targets.
- If the review or your own reflection surfaces a scope problem (wrong channel,
  an ask Matt never made, a decision that isn't yours to announce), stop and
  raise it instead of writing the draft.
- Never change the recipient, channel, or thread target as part of a brevity edit.

## Example

Intent: "let #eng-platform know CI is fixed"

Writer's-head order:

> Hey team! Quick update on the CI situation. We noticed builds taking longer
> than usual, and after some digging it turns out the cache wasn't restoring
> after last week's runner image update. I pushed a fix that should hopefully
> improve things. Let me know if you see issues! Also we should probably talk
> about pinning the runner image at some point.

Smart Brevity:

> **CI is fast again. Cache restore broke in last week's runner-image update,
> fix is live.**
>
> • **What happened:** builds ran about 14 min instead of 5 because the
> dependency cache never restored.
>
> • **What's next:** I'll propose pinning the runner image so an update can't
> silently do this again. Thread if you want in.
>
> 👀 Still seeing 6 min+ builds after a re-run? Flag it here.

Delivered as a Slack draft in #eng-platform. Matt sends it.
