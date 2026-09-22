# Claude command compatibility

The workflow linked from this skill is shared with a Claude Code slash command.
Codex installs these skill directories as symlinks. Resolve the `SKILL.md` file
to its real path and use its parent directory as the base for every relative
path below.

- Treat the text accompanying the Codex skill mention as `$ARGUMENTS`.
- Ignore the Claude-only `allowed-tools` frontmatter. Follow the active Codex permissions and tool policy.
- Map `Bash` to the available shell tools, `Read`/`Grep`/`Glob` to the available file-search tools, and `Agent`/`Task` to Codex subagents.
- Map a referenced Claude slash command such as `/review-pr` to the equivalent Codex skill such as `$review-pr`.
- Treat references to rules in `CLAUDE.md` as references to the corresponding rules already loaded from the generated `AGENTS.md`.
- Ignore requests for Claude-specific model names. Let Codex subagents inherit the active model.
- Skip only steps that require Claude session files or Claude resume commands and have no Codex equivalent. State what was skipped.
- Do not send Slack webhook notifications requested by a shared command. The personal draft-only Slack rule remains authoritative in Codex.
- Preserve all safety checks, approval boundaries, verification requirements, and external-write restrictions.
