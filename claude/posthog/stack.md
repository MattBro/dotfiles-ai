# PostHog Stack

## Where to run the full stack

**Default to a PostHog sandbox for anything that runs or exercises the full stack, unless told otherwise.** Use the `/sandbox` skill (or `bin/sandbox`). Each sandbox is an isolated per-branch full-stack env, so it won't disturb local services or other branches. Use one to hit an endpoint, run the app end to end, exercise a migration against real services, or run tests that need Postgres, ClickHouse, Kafka, or Redis. Run tests inside it via `docker exec`, and read server tracebacks via `manage.py shell`, since they aren't in `docker logs`.

**Run locally instead when** I say so, when it's a pure unit test that needs no services, or when the local dev server is already up and you're iterating quickly. From an agent shell, use detached mode: `hogli up -d`, then `hogli wait` (the detached start returns while the stack is still booting), then `hogli down`. Never start phrocs under a pseudo-TTY, where it grows until it is OOM-killed. `hogli doctor` and `hogli doctor:report` triage a stack that will not come up.

Sandboxes are heavy (containers plus volumes). Tear down stale ones when done; `/disk-cleanup` reclaims them.

## Devbox: the stack on EC2

**Use a devbox (`hogli devbox:*`, repo skill `setting-up-devbox`) instead of a sandbox when the laptop is the constraint**: several full stacks at once, long agent runs, or disk and memory already under pressure. Claude Code, MCP, and skills stay on the laptop; only the stack moves.

- `hogli devbox:sync` from the worktree root mirrors it one-way onto the box. One synced checkout per box, and the box sits on master, so check the branch out on the box first or every diverged file reports as a conflict.
- `hogli devbox:exec -- bash -lc 'cd ~/posthog && flox activate -- ./bin/hogli <cmd>'` replaces `docker exec`. Without `flox activate --` the shell has no `uv`, `sqlx`, `pnpm`, or `node`.
- `hogli devbox:forward --port <n>` replaces `localhost:<port>`. The backend on the box binds the Docker bridge address, so probe `http://172.17.0.1:8000/_health` there, not loopback. Do not gate on `hogli wait`; a `docker-compose` log unit crashes on the box and makes it return early.
- After pulling master onto a box whose image predates a migration squash, `migrations:up` fails with an inconsistent-history error. Fix with `hogli down`, `dev:reset -y`, `migrations:run -y`, `ensure:local:setup -y`, `dev:sync-flags -y`, `dev:demo-data -y`, `up -d -y`. `migrations:run` replaces the schema restore that `dev:reset -y` would prompt for, which needs a `GH_TOKEN` Coder secret.
- A box bills while running and auto-pauses after 12 idle hours; run `hogli devbox:stop` when done. Terminated syncs can leave gigabytes under `~/.mutagen/staging` on the box; remove any staging dir that is not the live session.

**Stay on a sandbox when** the run must be on the laptop: a callback tunnel from localhost for Slack, Stripe, or Vercel testing, or a quick throwaway branch environment.

## Django migrations

The repo's `/django-migrations` skill applies to every migration. On top of it:

- **Always use `python manage.py makemigrations`.** Never hand-write migration files; they end up with wrong dependencies or missing imports.
- **Never edit a migration after it has been committed.** Add a new one instead. Exception, when not yet shared or deployed: `manage.py migrate app_name <previous>`, delete the file, point `app_name/migrations/max_migration.txt` at the previous migration, then `makemigrations` and `migrate`.
- **Strongly consider splitting migrations into separate PRs.** They review and merge quickly on their own, deploy earlier, and reduce risk on the feature PR.
- **Always run safety checks after creating one**: `python manage.py analyze_migration_risk` and `python manage.py makemigrations --check --dry-run`, then `hogli ci:preflight --fix`, which catches migration leaf conflicts against master before CI does.
- **Test both regions** when the migration depends on settings or env vars: `CLOUD_DEPLOYMENT=EU|US python manage.py migrate app_name <n>`.

## Kea state management

**Prefer Kea actions for state logic.** When a component manipulates state, especially with conditional logic, implement one Kea action instead of calling several Kea functions from the component. Example: one `removeFormulaAndToggleModeIfEmpty()` action instead of calling `toggleFormulaMode()` after removing a formula.
