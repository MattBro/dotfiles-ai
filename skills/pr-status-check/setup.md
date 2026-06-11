# pr-resume setup (one-time, macOS + Ghostty)

`pr-status-check` renders `file://` links that, when CMD+clicked in the Claude
Code TUI, open a **new Ghostty tab** running `claude --resume <id>`. That
requires a tiny local handler app (`ClaudeResume.app`) plus a one-time macOS
Automation permission. This walks the build and the grant.

> Paths below are relative to this skill's directory (`SKILL_DIR`).

## Prerequisites (check first, tell the user if missing)

- **macOS** (`uname` == Darwin). This tool is macOS-only.
- **Ghostty 1.3.0+** (`ghostty --version` or `/Applications/Ghostty.app`). The
  AppleScript dictionary used to spawn tabs landed in 1.3.0.
- **gh** authenticated (`gh auth status`).
- **claude** on PATH — the resumed tab runs `claude --resume`.

## Steps

1. **Build + register the handler.** Run:

   ```bash
   bash "<SKILL_DIR>/scripts/build-handler.sh"
   ```

   This compiles `~/Applications/ClaudeResume.app`, declares it as the owner of
   the `.clauderesume` file type, ad-hoc signs it, and registers it with Launch
   Services. Idempotent.

2. **Trigger the one-time Automation grant.**

   > **Tell the user, before running the command below, exactly what to expect —
   > verbatim:**
   >
   > "macOS is about to pop up a dialog: **'ClaudeResume' wants access to control
   > 'Ghostty'**. Click **Allow**. This is the one-time permission that lets the
   > resume links open a new Ghostty tab — it only happens once. Please click it
   > now and **don't walk away**: if the dialog sits unanswered for ~10 min it
   > times out and we just retry."

   Then write a harmless test file and open it:

   ```bash
   printf '/tmp\nTEST-not-a-real-session\n' > /tmp/test.clauderesume
   open /tmp/test.clauderesume
   ```

   **Expected:** a dialog titled **"ClaudeResume" wants access to control
   "Ghostty"** → user clicks **Allow** → a new Ghostty tab opens running
   `claude --resume TEST-not-a-real-session` (which shows "No sessions match" —
   that's correct, the id is fake). Permission persists; no prompt next time.

   **Fallbacks (older macOS / edge cases), in order:**
   - **"AppleEvent timed out (-1712)"** — the prompt sat too long (user away).
     Harmless; just re-run the `open`. The handler waits up to 10 min, so this
     is rare.
   - **"Not authorized to send Apple events to Ghostty (-1743)"** — no clean
     prompt appeared. Click **Edit** on that dialog → it deep-links to *System
     Settings → Privacy & Security → Automation* with a **ClaudeResume → Ghostty**
     toggle. Turn it **ON**.
   - **No dialog at all** — open the pane directly:
     `open "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"`
     and enable **ClaudeResume → Ghostty**.
   - **ClaudeResume not listed there** — reset and retry the open:
     `tccutil reset AppleEvents com.nava.clauderesume` then re-run the `open`.

   > **Note on updates:** the handler is ad-hoc signed, so a future change to
   > the AppleScript may make macOS ask for the grant again. Same drill: click
   > **Allow**.

3. **Verify.** Re-run the open and confirm a new tab appears:

   ```bash
   before=$(osascript -e 'tell application "Ghostty" to count of tabs of front window')
   open /tmp/test.clauderesume
   osascript -e 'delay 2' -e 'tell application "Ghostty" to count of tabs of front window'
   ```

   The count should increase by 1 (the new tab runs `claude --resume
   TEST-not-a-real-session`, which errors harmlessly — that's expected). Tell the
   user they can close that test tab.

4. **Done.** Now `/pr-status-check` works: each ▶ resume link opens its chat in a
   new Ghostty tab. The same links are CMD+clickable from the assistant's
   messages too, not just the slash-command output.

## Uninstall

```bash
rm -rf ~/Applications/ClaudeResume.app
rm -rf ~/.claude/pr-resume
tccutil reset AppleEvents com.nava.clauderesume
```

## Notes

- **Why a generated app, not a shipped binary:** macOS TCC (Automation) is
  per-user/per-machine and won't carry across machines, and an unsigned shipped
  app would be quarantined. So we ship the AppleScript source + build script and
  generate the app locally.
- **Other terminals:** iTerm2 / Terminal / Warp would each need a different
  handler (different scripting bridge). Only Ghostty is supported today.
