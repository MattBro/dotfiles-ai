# hogli

`hogli` is the single entry point for PostHog monorepo work. There is no
Makefile. It wraps every bin script, build pipeline, and dev-env command, and
`hogli --help` is the current source of truth for what exists.

## It must be on PATH

Interactive shells get `hogli` from the repo venv via direnv/flox. Agent shells
and any session started outside the repo do not, which has two consequences:

- PostHog's `.husky/pre-push` guards with `command -v hogli`, so `ci:preflight`
  **silently skips on every agent-driven push**.
- Agents never reach for hogli because it looks like it does not exist.

`bin/hogli` in this repo is a PATH shim installed to `~/.local/bin/hogli`. It
walks up from `$PWD` to the nearest `hogli.yaml` and execs that repo's own
`bin/hogli`, so a worktree resolves to its own checkout. If `hogli` is missing,
run `./install.sh --bin-only`.

If a hogli command fails with `No module named 'hogli'` or `No module named
'posthog_owners'`, the venv is stale. Run `uv sync --active` in that checkout.

## Use hogli instead of the raw command

| Instead of | Use |
|---|---|
| `pytest ...` / `jest` | `hogli test <path>`, `hogli test --changed`, `hogli test --watch` |
| `ruff check . --fix && ruff format .` | `hogli lint:python:fix`, `hogli format:python` |
| `pnpm --filter=@posthog/frontend fix` | `hogli lint`, `hogli format:js` |
| `bin/start-backend` + `bin/start-frontend` | `hogli up -d`, then `hogli wait`, then `hogli down` |
| `manage.py migrate` | `hogli migrations:up`, `hogli migrations:run`, `hogli migrations:status` |
| `psql` / `clickhouse client` | `hogli db:pg`, `hogli db:ch` |
| `docker compose up` | `hogli docker:services:up` |
| parsing `gh pr checks` by hand | `hogli ci:insights search` / `view` / `plan` |
| `git worktree remove` in a loop | `hogli worktrees:clean --before 2w --mode full --dry-run` |
| hand-rolled docker/node pruning | `hogli doctor:disk --area docker` |

`manage.py makemigrations` has no hogli equivalent. Keep using it.

## Always run before pushing

```bash
hogli ci:preflight --fix     # auto-remediate what is safe
hogli ci:preflight --strict  # exit non-zero on any failure
```

It catches the deterministic CI failures reachable from the diff: formatting,
lint, broken lockfiles, OpenAPI drift, migration conflicts, stale branch. Every
one of those caught locally is a CI matrix not burned.

## Prod SQL through Metabase

```bash
hogli metabase:login --region us
hogli metabase:databases --region us              # find the database id
hogli metabase:query --region us --database-id <id> --save out.tsv < query.sql
```

This replaces driving the Metabase UI through a browser. Use `--save` so large
result sets do not land in the transcript. Regions are `us`, `eu`, `dev`.

## Reviewer and ownership routing

```bash
hogli owners:who <path>              # team, status, slack channel, source file
hogli owners:resolve --json <paths>  # machine output, accepts stdin
hogli owners:unowned <prefix>
```

Use this to pick a PR reviewer for the code actually touched, rather than
defaulting to one team on every PR.

## Other commands worth reaching for

- `hogli pr:upload-image <file>` and `hogli pr:upload-video` print embeddable,
  SHA-pinned markdown for PR bodies. The target repo is public, so never upload
  customer data, secrets, or internal-only screenshots.
- `hogli test:quarantine add|list|remove` parks a flaky test so it stops
  blocking CI, with a tracked entry rather than a silent skip.
- `hogli db:prime-test-db` and `hogli db:restore-schema` pull a pre-migrated
  schema from CI so `pytest --reuse-db` starts fast.
- `hogli dev:api-key` mints a stable local personal API key that survives
  `hogli dev:reset`.
- `hogli doctor`, `hogli doctor:report`, `hogli doctor:ports`,
  `hogli doctor:zombies` for dev-env triage before hand-debugging.
- `hogli devex:feedback -c bug "<what broke>"` reports broken or slow repo
  tooling to the devex team. The repo's AGENTS.md asks local agents to use it.
  Skip it from cloud tasks and agent sandboxes, where it is a no-op.

## Repo skills only load inside the repo

`~/dev/posthog/.claude/skills` symlinks to `.agents/skills` and carries about 80
maintained skills. They load only when the Claude session's project directory is
the repo or a worktree. A session started in `~/dev` gets none of them, and also
misses the `SessionStart` hook that puts the venv on PATH.

**Start PostHog sessions inside the checkout you are working in.** When work
spans repos and the session has to live in `~/dev`, read the relevant skill file
directly from `~/dev/posthog/.agents/skills/<name>/SKILL.md`.

The ones that supersede commands in this repo: `running-ci-preflight`,
`merging-prs`, `writing-pr-descriptions`, `debugging-ci-failures`,
`fixing-flaky-tests`, `establishing-code-ownership`. The ones with no local
equivalent: `stacking-prs`, `autoresolving-pr-conflicts`, `security-audit`,
`qa-frontend`, `run-posthog`, `django-migrations`, `clickhouse-migrations`,
`writing-tests`, `writing-kea-logics`.

## hogli in personal repos

hogli is a general framework, published to PyPI, that turns a `hogli.yaml` into
a discoverable `--help`-documented command surface. Personal projects
(`creekside-fields`, `buzz`, `brooker-wedding`) have none, so agents guess at
commands from `package.json`. A ten-line `hogli.yaml` fixes that. Note that the
PyPI package is the framework alone; PostHog's own commands live in the monorepo
under `tools/hogli-commands/`.
