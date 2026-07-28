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

## Format

Compose in Smart Brevity via the `slack-smart-brevity` skill: lead with the
news, one main point, ask up front with owner and deadline, under 150 words,
depth in a thread reply. The skill carries the full loop, including the
reviewer pass and my style rules (no em dashes, no greetings, no `~` for
"approximately", no AI tells).
