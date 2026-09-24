# Personal Claude Code Settings

> **Source**: this file is sourced from [`MattBro/dotfiles-ai`](https://github.com/MattBro/dotfiles-ai) and symlinked into `~/.claude/CLAUDE.md`. Edit the repo (`~/dev/dotfiles-ai/`), commit + push; the symlink follows. The same applies to files under `~/.claude/commands/` and `~/.claude/claude/`. To add a new command or skill: drop the file in the repo, run `./install.sh`, commit + push. After changing anything under `claude/`, rerun `./install.sh`: PostHog Code and Codex read flattened copies, not these symlinks.

This is the root of my personal `CLAUDE.md`, composed from the files under `claude/`. Each sub-file is loaded via `@`-import below, highest priority first. `claude/posthog/` is not imported here; `scripts/require-repo-instructions.py` loads it in PostHog/posthog checkouts.

@./claude/slack.md
@./claude/secrets-mgmt.md
@./claude/disagreement.md
@./claude/delegation.md
@./claude/engineering.md
@./claude/git-workflow.md
@./claude/git-checkouts.md
@./claude/workspace.md
@./claude/session-briefings.md
@./claude/aws-access.md
