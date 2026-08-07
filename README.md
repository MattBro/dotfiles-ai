# dotfiles-ai

My personal Claude Code configuration: composed `CLAUDE.md`, slash commands, and a setup script that symlinks everything into `~/.claude/`.

This is **my** config, not a framework. Fork it and adapt to your own workflow.

## Layout

```
CLAUDE.md          thin root file, @-imports the sub-files below
claude/
  slack.md         never send, always draft; Smart Brevity format
  engineering.md   code style, comments, debug-then-fix, observability, money types
  git-workflow.md  worktrees, branches, commits, PRs, pre-PR checklist
  posthog-stack.md PostHog-specific stack notes (sandboxes, Django migrations, Kea)
  secrets-mgmt.md  AWS Secrets Manager / `secrets` CLI workflow
  disagreement.md  push back, don't capitulate; explicit confidence levels
  delegation.md    parallelize implementation across Sonnet sub-agents
commands/          slash commands (/review-pr, /babysit-pr, /save-context, …)
skills/            personal skills (symlinked whole-dir into ~/.claude/skills/)
  html-doc/        self-contained HTML reports (D2 diagrams, charts, KPI cards, QA shots)
  make-pages-interactive/  live commenting surface over static HTML
  pr-status-check/ open-PR table with ▶ resume links to matching Claude chats (macOS+Ghostty)
  slack-smart-brevity/  Smart Brevity Slack drafts with an opus reviewer pass (drafts only, never sends)
  unambiguous-agent-text/  ASD-STE100 rewrite for machine-read text (tool descriptions, skill frontmatter, system prompts)
output-styles/     system-prompt styles (symlinked into ~/.claude/output-styles/)
  readable.md      plain engineering English: answer first, no invented jargon or metaphors
scripts/
  safety-scan.sh       greps for common secret patterns before you commit
  build-agents-md.py   flattens CLAUDE.md + claude/*.md into ~/.agents/AGENTS.md
install.sh         symlinks CLAUDE.md + claude/ + commands/ + skills/ + output-styles/ into ~/.claude/
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

**Import order is priority order.** Anything past 20k is silently truncated out of cloud runs, so hard rules (`slack.md`) are imported first. `build-agents-md.py` warns at 18k and names the dropped sections if you go over.

Granular installs:

```bash
./install.sh --claude-md-only
./install.sh --commands-only
./install.sh --output-styles-only
./install.sh --uninstall
```

## Output styles

`output-styles/*.md` land in `~/.claude/output-styles/`. Select one with `/config` → **Output style**; it applies after `/clear` or a new session. The standalone `/output-style` command was removed in Claude Code 2.1.91, so `/config` or the `outputStyle` key in a settings file is the only route now.

An output style modifies the system prompt, which makes it stickier than `CLAUDE.md` rules. It applies to the main conversation only: sub-agents run their own system prompt, so delegated and cloud runs don't inherit it. `readable.md` sets `keep-coding-instructions: true`, which keeps Claude Code's built-in engineering instructions in place. Leaving that out drops them.

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
