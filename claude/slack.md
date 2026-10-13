# Slack

## Never send, always draft

**Never call `slack_send_message` or any scheduling variant.** Not for updates,
not for replies, not for "just let the team know". Owning a task is not send
permission, and a request phrased as "send X to #channel" means draft X for
#channel.

The only Slack write allowed is `slack_send_message_draft`, which saves to my
Drafts & Sent and leaves the send button to me. Always print the draft in the
chat too, so I can read it without switching apps.

If I read a draft and explicitly say send it, that go covers that message
only. A new commit, a new comment, or a reworded draft needs a fresh go.

## Revising a saved draft

The Slack MCP can create a draft but cannot edit, list, or delete one. Saving
again on the same thread leaves the saved draft unchanged (tested 2026-10-13).
The draft panel ChatGPT shows only edits its own copy and sends it from there;
it never updates the saved draft either. **Never use computer use to change a
draft.**

To revise a saved draft, print the new text in chat with the channel and thread
it replaces, so I can paste it over the old one. Don't save the revision as
another draft. After saving a top-level draft in a channel, ask me to check it
in Drafts & sent: the app can replace it with its own copy of that channel's
draft.

## Format

Compose in Smart Brevity via the `slack-smart-brevity` skill: lead with the
news, one main point, ask up front with owner and deadline, under 150 words,
depth in a thread reply. The skill carries the full loop, including the
reviewer pass and my style rules (no em dashes, no greetings, no `~` for
"approximately", no AI tells).
