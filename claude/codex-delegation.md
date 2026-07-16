# Codex Delegation

Always use raw `codex exec` via Bash — never the Codex plugin's agents/skills (has wedged).

Template:

```bash
codex exec --json -C <dir> -s workspace-write -o <file> "<prompt>"
```

- Read the `-o` file for results, not the JSONL stream.
- **Resume**: `codex exec [opts] resume <thread_id>` — opts go before `resume`; the thread id is in the `thread.started` event.
- **Reviews**: `-s read-only` + an adversarial task prompt. Never `codex review`.
- **Watchdog**: use the Bash tool's `timeout` param — macOS has no `timeout` binary.
- Append `</dev/null` — piped stdin makes codex wait forever on "Reading additional input from stdin".
- Add `--skip-git-repo-check` for non-git dirs.
