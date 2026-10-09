# Slack

## Never send, always draft

**Never call `slack_send_message` or any scheduling variant.** Not for updates,
not for replies, not for "just let the team know". Owning a task is not send
permission, and a request phrased as "send X to #channel" means draft X for
#channel.

The only Slack writes allowed are `slack_send_message_draft`, which saves to my
Drafts & Sent and leaves the send button to me, and revising an unsent draft in
the Slack app (below). Always print the draft in the chat too, so I can read it
without switching apps.

If I read a draft and explicitly say send it, that go covers that message
only. A new commit, a new comment, or a reworded draft needs a fresh go.

## Revising a saved draft

The Slack MCP can create a draft but cannot edit, list, or delete one. To
revise a draft you already saved, edit it in the Slack desktop app with
computer use. Calling `slack_send_message_draft` again on the same thread
leaves a second draft beside the first.

1. Request Slack with clipboard write. Slack runs full-screen on its own Space,
   where background clicks are refused, so take full-screen control.
2. Open Drafts & sent and click the draft. A thread draft opens in the thread
   panel.
3. Put the new text on the clipboard, click into the draft, then `cmd+a` and
   `cmd+v`. Never type the text and never press Return: Return in a Slack
   message box sends it.
4. Screenshot the box, then check Drafts & sent: the entry shows the new text
   and the draft count did not grow. `slack_read_thread` confirms nothing
   posted.

Edit only drafts you saved or ones I name. To discard a draft you saved, clear
the box with `cmd+a` and Backspace; Slack drops an empty draft. After saving a
top-level draft in a channel, check it in Drafts & sent: opening a channel where
the app already holds a draft can replace yours with the app's copy.

## Format

Compose in Smart Brevity via the `slack-smart-brevity` skill: lead with the
news, one main point, ask up front with owner and deadline, under 150 words,
depth in a thread reply. The skill carries the full loop, including the
reviewer pass and my style rules (no em dashes, no greetings, no `~` for
"approximately", no AI tells).
