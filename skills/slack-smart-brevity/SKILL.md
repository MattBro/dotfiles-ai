---
name: slack-smart-brevity
description: >-
  Compose every outgoing Slack message in Smart Brevity format: audience-first,
  lead with the news, skimmable, with an opus subagent review pass. Draft only.
  This skill never sends.

  UNCONDITIONAL TRIGGER. Read this skill before writing any Slack message,
  reply, thread response, update, or announcement on Matt's behalf, and before
  any call to slack_send_message_draft. It applies even when the request is
  worded as "send X to #channel", "reply to that thread", "let the team know",
  or "post an update". Also use when asked to "smart brevity" any text.

  SKIP the review loop when the whole message is one line: an ack or
  single-sentence answer has nothing to compress. Draft it anyway, never send.
---

# Slack Smart Brevity (draft only)

Every Slack message should give the reader the whole point in about 10 seconds
and earn any further reading. Messages drafted from the writer's head open with
backstory and bury the ask. This skill forces the reader's-eye view: reflect on
the goal, draft in Smart Brevity, and let an opus reviewer play the busy
teammate before the draft lands.

The step order matters. Compression protects whatever the draft already
emphasizes, so audience-need comes first. Compression also rewrites claims, so
facts get re-checked after it, against source: audience, draft, compress,
verify, review.

## Never send

`slack_send_message` and any scheduling variant are out of bounds here,
whatever the request wording. "Send it", "post it", "let them know", and "tell
#channel" all resolve to: produce a draft.

The only write this skill performs is `slack_send_message_draft`, which saves
to Matt's Drafts & Sent in Slack and leaves the send button to him. Always
print the draft in chat as well, so he can read it without switching apps.

Owning a task is not send permission. If Matt reads the draft and gives an
explicit go, sending is his instruction and happens outside this skill.

Drafting mechanics:

- Thread reply? Pass `thread_ts` so the draft attaches to the right thread.
- `draft_already_exists` means an attached draft is already sitting in that
  channel. Do not delete or overwrite it. Report it and put the new text in
  chat instead.
- Slack Connect (externally shared) channels reject writes. Put the draft in
  chat and say so.
- The MCP draft tool takes standard markdown (`**bold**`) and converts it.
  Skip `#` headers; they read badly in a chat message regardless.

## Step 0: proportionality

Size the process to the message, not to the request. If the draft is one line
(an ack, a quick answer, a single-sentence update, even one carrying news or an
ask), skip the flow: one line has nothing to compress, and a review pass on
"sounds good, ship it" only adds latency. One-liners still keep the two-second
basics: you have read what you are replying to, the claim is true against
source, right thread.

The full loop is for anything with structure to get wrong: updates,
announcements, asks with context, any multi-sentence reply.

For time-critical incident comms, keep the format and skip the Step 5 review;
speed is part of serving the reader there. Never skip Step 4. Wrong numbers in
incident comms compound the incident.

## Step 1: gather context

- Replying in a thread? Read it first (`slack_read_thread`). Never draft a
  reply from memory of a thread you have not read this session.
- New message to a channel? Skim recent messages (`slack_read_channel`) if you
  have not already. Tone and prior context live there.
- Write the audience in one line: who actually reads this (thread
  participants, channel population), what they already know from the thread,
  and what they need from this message. That line feeds the reviewer later.

## Step 2: reflect before drafting

Answer each in one line, to yourself, not in the message:

1. Goal: inform, ask, decide, or unblock?
2. The ONE main point. Two points means two messages.
3. What does the reader need that they do not already have, and what do they
   already know that you should leave out?
4. The ask, if any: who does what, by when?
5. What is awkward here: a delay, bad news, work someone else offered to do, a
   decision that overrode them? The draft addresses it head-on, usually in the
   lede. Flagging the risk to Matt while leaving the dodge in the message is
   not a fix.

## Step 3: draft in Smart Brevity

- Line 1 carries the news. No throat-clearing ("Hey team, just wanted to..."),
  no greeting. Bold it; it is the headline and the lede at once.
- If the message exists to make an ask, the ask IS line 1, with owner and
  deadline explicit. An ask buried as a closer gets skimmed past.
- "Why it matters" is a question, not a slot: what changes for this reader? If
  nothing changes, drop the section. Filling it because the format has one is
  the format driving.
- Bolded lead-ins on bullets. The signpost family works where it fits:
  *What happened*, *The big picture*, *By the numbers*, *What's next*,
  *The bottom line*.
- One idea per bullet. Numbers over adjectives ("builds ran 14 min instead of
  5" beats "much slower"). No hedges, no jargon this audience lacks.
- 150 words is the default ceiling, not the goal. A lede that owns a delay
  earns its length; mechanical compression that keeps exposition and cuts what
  changed for the reader is worse than being long. Depth, logs, and code go in
  a thread reply, where the reader opts in.
- Edit pass: draft, then cut roughly in half. Brevity is confidence.

### Matt's Slack style rules

These override anything above if they conflict.

- **No em dashes.** Rewrite the sentence. Spaced hyphens are not a substitute.
- **No `~` for "approximately".** Slack pairs single tildes into strikethrough.
  Write "about 14 min" or just "14 min".
- **Just the facts.** No greetings, no hedging, no unsolicited suggestions.
  Matt adds his own framing.
- **No AI tells**: scene-setting openers, affirmations ("great question"),
  mechanism explanations nobody asked for, closing reassurance ("hope that
  helps", "let me know if you need anything").
- **No rhetorical "X, not Y"** when Y exists only for emphasis.
- **Never say "load-bearing" or "triad".**
- **External or Slack Connect channels**: no internal file paths, constant
  names, repo paths, or source links. Keep it product-facing.
- **Security threads**: draft to Matt only, and never carry an unverified
  sub-agent claim into one.
- Emoji sparingly, as visual anchors.

## Step 4: verify against source

Compression rewrites claims. After the edit pass, re-check every number, count,
name, date, and quoted phrase against its source: the thread, the file, the
command output. Never check against the previous draft; that is how a seven
becomes "six files" and survives three versions. The Step 5 reviewer only sees
the draft, so facts are yours.

Then sweep for notes-to-self: placeholders, TODOs, or lines addressed to Matt
rather than the audience ("@Pat needs to grant access first").

Every link in the draft gets a real URL. No bare `#54405` or `#team-growth`,
and PR references carry the title.

## Step 5: audience review (subagent)

Spawn one reviewer with the Agent tool: `subagent_type: general-purpose`,
`model: opus`, `run_in_background: false`. The reviewer stands in for the busy
reader doing a fit check on under 150 words. Its diagnosis is the part you
keep, so it gets a strong model. With no subagent tool available, run the
checklist yourself as a separate explicit pass.

Prompt template, brackets filled from Steps 1 and 2:

```
Review this draft Slack message for audience fit. Be terse and concrete.

Audience: [who reads this + what they already know]
Goal: [inform/ask/decide/unblock] | main point: [one line] | ask: [who/what/when, or "none"]

Draft:
---
[draft]
---

Standard: Smart Brevity, audience first. The message serves what the reader
needs.

Check in order:
1. Does line 1 alone give the reader the point?
2. If there is an ask: unmissable, owner + deadline explicit, and leading the
   message when the message exists to ask?
3. Exactly one main point?
4. Anything the reader already knows or does not need? Quote it, say cut.
5. Jargon or missing context for THIS audience?
6. Over 150 words, or formatting Slack renders badly (# headers, single tildes
   around numbers)?
7. Is the message avoiding something awkward it should address head-on (a
   delay, superseded work, an overridden offer)?
8. Any placeholders, bare issue/PR numbers without links, or lines addressed
   to the sender rather than the audience?
9. Any em dashes, greetings, hedges, or closing reassurance to cut?

Return "SHIP" or up to 5 numbered edits, each quoting the text to change and
giving a replacement. No praise. No full rewrite.
```

## Step 6: apply and deliver the draft

- Apply the edits you agree with. The reviewer advises, you decide. Trust its
  diagnosis over its remedy: reviewers name what is wrong precisely, including
  social risks, but their fixes for social problems run cosmetic (add a
  compliment) where the real fix is structural (own it in the lede).
- One round only. Re-review only if the goal itself changed.
- Create the draft with `slack_send_message_draft`, and print the final text in
  chat with the channel and thread it targets. Do not call `slack_send_message`.
- If the review or your own reflection surfaces a scope problem (wrong channel,
  an ask Matt never made, a decision that is not yours to announce), stop and
  raise it instead of writing the draft.
- Never change the recipient, channel, or thread target as part of a brevity
  edit.

## Example

Intent: "let #eng-platform know CI is fixed"

Weak draft, writer's-head order:

> Hey team! Quick update on the CI situation. We noticed builds taking longer
> than usual, and after some digging it turns out the cache wasn't restoring
> after last week's runner image update. I pushed a fix that should hopefully
> improve things. Let me know if you see issues! Also we should probably talk
> about pinning the runner image at some point.

Smart Brevity version:

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
