# hogli

`hogli` is the single entry point for PostHog monorepo work. There is no Makefile. It wraps every bin script, build pipeline, and dev-env command, and `hogli --help` is the source of truth for what exists.

## It must be on PATH

Interactive shells get `hogli` from the repo venv via direnv/flox. Agent shells do not, and the repo's `.husky/pre-push` guards with `command -v hogli`, so without it `ci:preflight` **silently skips on every agent-driven push**.

- dotfiles-ai's `bin/hogli` is a PATH shim installed to `~/.local/bin/hogli`. It walks up from `$PWD` to the nearest `hogli.yaml` and execs that checkout's own `bin/hogli`. If `hogli` is missing, run `./install.sh --bin-only` in `~/dev/dotfiles-ai`.
- `No module named 'hogli'` or `No module named 'posthog_owners'` means the venv is stale: run `uv sync --active` in that checkout.
- Upstream bug: hogli run from a subdirectory crashes with `ModuleNotFoundError: No module named 'email.utils'; 'email' is not a package`, because `python -m hogli` puts the cwd on `sys.path[0]` and `posthog/email.py` shadows the stdlib `email`. The shim runs hogli from the repo root. An interactive shell resolves `.venv/bin/hogli` ahead of the shim, so `cd` to the repo root there first. The fix is one line in the repo's `bin/hogli` (`cd "$REPO_ROOT"`); report it with `hogli devex:feedback`.

## Use hogli instead of the raw command

| Instead of | Use |
|---|---|
| `pytest ...` / `jest` | `hogli test <path>`, `hogli test --changed`, `hogli test --watch` |
| `ruff check . --fix && ruff format .` | `hogli lint:python:fix`, `hogli format:python` |
| `pnpm --filter=@posthog/frontend fix` | `hogli lint`, `hogli format:js` |
| `bin/start-backend` + `bin/start-frontend` | `hogli up -d`, then `hogli wait`, then `hogli down` |
| `manage.py migrate` | `hogli migrations:up`, `hogli migrations:run`, `hogli migrations:status`, `hogli migrations:sync` |
| `psql` / `clickhouse client` | `hogli db:pg`, `hogli db:ch` |
| `docker compose up` | `hogli docker:services:up` |
| parsing `gh pr checks` by hand | `hogli ci:insights search` / `view` / `plan` |
| hand-rolled docker/node pruning | `hogli doctor:disk --area docker` |

`manage.py makemigrations` has no hogli equivalent. Keep using it.

Before every push, run `hogli ci:preflight --fix`, then `hogli ci:preflight --strict`, which exits non-zero on any failure. Preflight catches the deterministic CI failures reachable from the diff: formatting, lint, broken lockfiles, OpenAPI drift, migration conflicts, stale branch. A mypy run from before the last change is not evidence about the current tree.

## Other commands

- **Prod SQL**: `hogli metabase:login --region us`, then `hogli metabase:databases --region us` for the database id, then `hogli metabase:query --region us --database-id <id> --save out.tsv < query.sql`. This replaces driving the Metabase UI in a browser. Use `--save` so large result sets stay out of the transcript. Regions are `us`, `eu`, `dev`.
- **Reviewer routing**: `hogli owners:who <path>`, `hogli owners:resolve --json <paths>`, `hogli owners:unowned <prefix>`. Pick PR reviewers for the code actually touched, not one default team.
- `hogli pr:upload-image <file>` and `hogli pr:upload-video` print SHA-pinned markdown for PR bodies. The target repo is public, so never upload customer data, secrets, or internal-only screenshots.
- `hogli test:quarantine add|list|remove` parks a flaky test with a tracked entry instead of a silent skip.
- `hogli db:prime-test-db` and `hogli db:restore-schema` pull a pre-migrated schema from CI so `pytest --reuse-db` starts fast.
- `hogli dev:api-key` mints a stable local personal API key that survives `hogli dev:reset`.
- `hogli doctor`, `doctor:report`, `doctor:ports`, and `doctor:zombies` triage the dev env before hand-debugging.
- `hogli devex:feedback -c bug "<what broke>"` reports broken or slow repo tooling to the devex team. Skip it from cloud tasks and agent sandboxes, where it is a no-op.
