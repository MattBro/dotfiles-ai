# dotfiles-ai

My personal Claude Code and Codex configuration: shared instructions, reusable
workflows, native status lines, skills, safety hooks, and one installer.

This is **my** config, not a framework. Fork it and adapt to your own workflow.

## Layout

```
CLAUDE.md          thin root file, @-imports the sub-files below
claude/
  slack.md         never send, always draft; Smart Brevity format
  engineering.md   code style, comments, debug-then-fix, observability, money types
  git-workflow.md  worktrees, branches, commits, PRs, pre-PR checklist
  hogli.md         PostHog dev CLI: command routing, ci:preflight, PATH shim, repo skills
  posthog-stack.md PostHog-specific stack notes (sandboxes, Django migrations, Kea)
  secrets-mgmt.md  AWS Secrets Manager / `secrets` CLI workflow
  disagreement.md  push back, don't capitulate; explicit confidence levels
  delegation.md    when to parallelize implementation across sub-agents
commands/          slash commands (/review-pr, /babysit-pr, /save-context, …)
codex/
  AGENTS.md         Codex root instructions; reuses compatible claude/*.md rules
  config.toml       managed config fragment, merged into ~/.codex/config.toml
  hooks.json        link-quality and draft-only Slack safety hooks
  delegation.md     Codex-native sub-agent rules
  skills/           Codex wrappers for compatible Claude slash-command workflows
skills/            personal skills (all go to ~/.claude/skills/; compatible ones
                   are also linked individually into ~/.agents/skills/)
  html-doc/        self-contained HTML reports (D2 diagrams, charts, KPI cards, QA shots)
  make-pages-interactive/  live commenting surface over static HTML
  pr-status-check/ open-PR table with ▶ resume links to matching Claude chats (macOS+Ghostty)
  slack-smart-brevity/  Smart Brevity Slack drafts with an opus reviewer pass (drafts only, never sends)
  unambiguous-agent-text/  ASD-STE100 rewrite for machine-read text (tool descriptions, skill frontmatter, system prompts)
output-styles/     system-prompt styles (symlinked into ~/.claude/output-styles/)
  readable.md      plain engineering English: answer first, no invented jargon or metaphors
bin/               PATH shims (symlinked into ~/.local/bin/)
  hogli            resolves hogli from the nearest hogli.yaml, so agent shells and
                   the PostHog pre-push hook can find it outside an activated venv
scripts/
  safety-scan.sh       greps for common secret patterns before you commit
  build-agents-md.py   flattens imports for PostHog Code and Codex
  update-codex-config.py  safely merges only the settings this repo owns
install.sh         installs both clients; bootstraps the standalone Codex runtime,
                   symlinks shared files, and merges Codex config in place
EXTERNAL.md        third-party skills/plugins I rely on but don't vendor
```

## Install

```bash
git clone https://github.com/MattBro/dotfiles-ai.git ~/dev/dotfiles-ai
cd ~/dev/dotfiles-ai
./install.sh
```

`install.sh` backs up conflicts under the relevant `~/.claude`, `~/.codex`, or
`~/.agents` directory. Claude Code files are symlinked. When the managed
standalone Codex runtime is missing, the script bootstraps it with OpenAI's
official installer. Existing npm or Homebrew installs are left in place. The
Codex config installer merges a marked block into `~/.codex/config.toml`,
preserving its model, MCP, plugin, trusted-project, and other machine-local
settings. The result is loaded with Codex's strict config validation. Re-run
after pulling updates; the operation is idempotent.

Each install regenerates two flattened files because neither destination
expands these repo-local `@` imports: `~/.agents/AGENTS.md` for PostHog Code
and `~/.codex/AGENTS.md` for Codex. Codex shares the compatible engineering,
Slack, git, PostHog, secrets, disagreement, briefing, and readable-output rules,
with Codex-native delegation guidance substituted for Claude's.

**Import order is priority order for PostHog Code.** Its cloud personalization
sync truncates content after 20k characters, so hard rules (`slack.md`) are
imported first. `build-agents-md.py` warns at 18k and names the sections that
PostHog Code would drop. Codex uses the separate byte limit in `codex/config.toml`.

Granular installs:

```bash
./install.sh --codex-only
./install.sh --claude-md-only
./install.sh --commands-only
./install.sh --output-styles-only
./install.sh --status-line-only
./install.sh --uninstall
```

After the first Codex install, open `/hooks` in Codex CLI and review the new
hooks. Codex requires this one-time trust step before user hooks can execute.
Direct Slack sends, scheduling, canvas edits, and conversation creation are
also disabled in the Slack MCP config. That protects the MCP path before hook
trust is granted. The hooks add the clickable-link check and a second safeguard.

## Codex status line

The managed Codex `tui.status_line` uses native items:

```
current directory · git branch · context used · five-hour limit · weekly limit · model + reasoning
```

It is the closest native equivalent to `status-line.sh`. Codex displays the
live context-window percentage and the usage-limit windows it receives from the
account. Unlike the Claude script, the native line does not calculate
ahead/behind-pace annotations or print reset timestamps. Run `/statusline` in
Codex to reorder or change items interactively; rerunning this installer restores
the version tracked here. Codex omits a limit item when the account does not
return that window.

## Codex agents overview

Run `codex agents` to open the shared agent command center, or use `/agent`
inside an interactive session to switch between that session's agent threads.
The installer also bootstraps OpenAI's standalone runtime at
`~/.codex/packages/standalone/current/codex`, even when an npm or Homebrew
Codex CLI remains first on `PATH`.

## Shared Claude workflows in Codex

Codex uses skills instead of custom slash-command files. The installer exposes
the compatible workflows as `$babysit-pr`, `$babysit-prs`, `$catch-up`,
`$ci-check`, `$conversation-reply`, `$disk-cleanup`, `$pr-ready`, `$review-pr`,
and `$sandbox`. It also installs the client-independent personal skills into
`~/.agents/skills`.

Claude-only workflows are deliberately omitted when they depend on Claude chat
resume links, Claude memory files, or a missing external integration. This
currently excludes `pr-status-check`, `/save-context`, `/memory-audit`,
`/review-assigned`, `/tag-posthog`, and `/work-review`.

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
