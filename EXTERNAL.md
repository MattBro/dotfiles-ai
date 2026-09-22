# External Skills & Plugins

This config relies on a handful of skills and plugins I don't vendor. Install them separately so they update from upstream.

## Vendored skills (copied into `skills/`, updated manually)

| Skill | Source | Notes |
|-------|--------|-------|
| `html-doc` | nava-corp/nava-claude-plugins (`nava-core`) | Self-contained HTML report generator. Vendored 2026-06-11. |
| `make-pages-interactive` | nava-corp/nava-claude-plugins (`nava-core`) | Live commenting surface over static HTML. Vendored 2026-06-11. |
| `pr-status-check` | nava-corp/nava-claude-plugins (`nava-experimental/pr-resume`) | PR table + ▶ resume links (macOS + Ghostty 1.3.0+). Paths adapted from `${CLAUDE_PLUGIN_ROOT}` to skill-relative; one-time setup in `skills/pr-status-check/setup.md`. Vendored 2026-06-11. |

These don't auto-update — re-copy from upstream to pick up changes.

## Plugins (installed via Claude Code plugin marketplace)

These are managed via `~/.claude/settings.json` under `enabledPlugins`. Install via `/plugin install` or by editing settings directly.

| Plugin | Marketplace | Source | Purpose |
|--------|-------------|--------|---------|
| `posthog` | `claude-plugins-official` | [Anthropic plugin marketplace](https://www.claude.com/build) | PostHog-specific skills (auditing experiments, investigating replays, querying analytics, …) |
| `frontend-design` | `claude-plugins-official` | Anthropic plugin marketplace | Distinctive UI / frontend interface generation |

## Codex equivalents

Codex plugin and MCP server definitions are machine-managed rather than
symlinked from this repo. This repo merges only its Slack deny list. On this
machine, the PostHog plugin/MCP and Slack MCP already cover the corresponding
Claude integrations. I use Codex's Sites, browser, and visualization plugins
for related interactive UI work; they are not exact replacements for
`frontend-design`.

On a new machine, Codex's `/import` command can inspect another agent's setup
and offer to convert instructions, settings, skills, plugins, MCP servers,
hooks, slash commands, and subagents. Review the proposed changes rather than
blindly replacing the managed files installed by this repo.

## MCP servers

Configured separately in `~/.claude/mcp.json` and Claude.ai's MCP integration UI. Not managed by this repo. Examples I run:

- PostHog (analytics queries, error tracking, feature flags)
- Slack
- GitHub / GitLab
- Google Calendar / Google Drive
- Granola (meeting notes)
- Spotify, Moku Coach, family calendar (personal)

## Shared team skills (PostHog-specific)

Not personal — these live in [PostHog/posthog `products/*/skills/`](https://github.com/PostHog/posthog/tree/master/products) and are distributed via [PostHog/skills](https://github.com/PostHog/skills) and `PostHog/ai-plugin`. Loaded automatically when the PostHog plugin is enabled.
