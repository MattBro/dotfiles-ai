# dotfiles-ai

My personal Claude Code configuration: composed `CLAUDE.md`, slash commands, and a setup script that symlinks everything into `~/.claude/`.

This is **my** config, not a framework. Fork it and adapt to your own workflow.

## Layout

```
CLAUDE.md          thin root file, @-imports the four sub-files below
claude/
  engineering.md   code style, comments, debug-then-fix, money types
  git-workflow.md  branches, commits, PRs, pre-PR checklist
  posthog-stack.md PostHog-specific stack notes (Kea, Django, mypy-baseline, monorepo)
  secrets-mgmt.md  AWS Secrets Manager / `secrets` CLI workflow
commands/          slash commands (/review-pr, /babysit-pr, /save-context, …)
skills/            personal skills (symlinked whole-dir into ~/.claude/skills/)
  html-doc/        self-contained HTML reports (D2 diagrams, charts, KPI cards, QA shots)
  make-pages-interactive/  live commenting surface over static HTML
  pr-status-check/ open-PR table with ▶ resume links to matching Claude chats (macOS+Ghostty)
scripts/
  safety-scan.sh       greps for common secret patterns before you commit
  build-agents-md.py   flattens CLAUDE.md + claude/*.md into ~/.agents/AGENTS.md
install.sh         symlinks CLAUDE.md + claude/ + commands/ + skills/ into ~/.claude/
EXTERNAL.md        third-party skills/plugins I rely on but don't vendor
```

## Install

```bash
git clone https://github.com/MattBro/dotfiles-ai.git ~/dev/dotfiles-ai
cd ~/dev/dotfiles-ai
./install.sh
```

`install.sh` backs up your existing `~/.claude/CLAUDE.md` and any conflicting commands to `~/.claude/backups/<timestamp>/`, then creates symlinks. Re-run after pulling updates and the symlinks stay current.

Each install also regenerates `~/.agents/AGENTS.md` — a flattened copy of `CLAUDE.md` with its `@`-imports expanded inline. PostHog Code's Personalization sync reads that file with a plain `readFile` (no `@`-import expansion, 20k char cap), so the flattened copy is what ships the full ruleset to local and cloud runs.

Granular installs:

```bash
./install.sh --claude-md-only
./install.sh --commands-only
./install.sh --uninstall
```

## Required env vars

Some commands read secrets/config from your shell. Add to your `~/.zshrc` (or equivalent):

```bash
# Slack webhook for /babysit-pr and /review-assigned notifications
# Create one at https://api.slack.com/apps and route to your DM channel
export SLACK_BABYSITTER_WEBHOOK="https://hooks.slack.com/services/..."

# Repos that /review-assigned and /babysit-prs scan for assigned/open PRs
# Space-separated owner/name pairs
export REVIEW_REPOS="PostHog/posthog PostHog/posthog-js"
```

If a command needs an env var that isn't set, it'll fail loudly with a message telling you which one to set.

## Safety scan

Before committing anything to this repo:

```bash
./scripts/safety-scan.sh
```

Greps for common token shapes (Slack webhooks, Stripe keys, GitHub PATs, PEM blocks, etc.). Useful but not exhaustive — also do a manual diff review.

## See also

- `EXTERNAL.md` — upstream skills and plugins this config assumes you have installed
- [PostHog/posthog `.claude/commands/`](https://github.com/PostHog/posthog/tree/master/.claude/commands) — repo-scoped commands that ride along with the codebase
- [PostHog/posthog `products/*/skills/`](https://github.com/PostHog/posthog/tree/master/products) — PostHog-specific agent skills, distributed via [PostHog/skills](https://github.com/PostHog/skills)

## License

MIT — see [LICENSE](LICENSE).
