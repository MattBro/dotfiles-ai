# PostHog Stack

PostHog-specific patterns for the [posthog](https://github.com/PostHog/posthog), [posthog-js](https://github.com/PostHog/posthog-js), and [posthog.com](https://github.com/PostHog/posthog.com) repos.

**Route repo commands through `hogli` first.** See [hogli](hogli.md) for the
command surface, the PATH requirement, and the ~80 repo skills that only load
when the session starts inside the checkout.

## Where to run the full stack: sandbox by default, devbox when the laptop is the limit

**Default to a PostHog sandbox for anything that needs to run or exercise the full stack, unless told otherwise.** Use the `/sandbox` skill (or `bin/sandbox`). Each sandbox is an isolated per-branch full-stack env, so it won't disturb local services or other branches.

Reach for one to hit an endpoint, run the app end to end, exercise a migration against real services, or run tests that need Postgres / ClickHouse / Kafka / Redis. Run tests inside it via `docker exec`; read server tracebacks via `manage.py shell`, since they aren't in `docker logs`.

**Run locally instead when**: I say so; it's a pure unit test that needs no services; or the local dev server is already up and you're iterating quickly.

To bring the local stack up from an agent shell, use detached mode: `hogli up -d`,
then `hogli wait` (the detached start returns while the stack is still booting),
then `hogli down`. Do not start phrocs under a pseudo-TTY, where it grows until
it is OOM-killed. `hogli doctor` and `hogli doctor:report` triage a stack that
will not come up.

Sandboxes are heavy (containers plus volumes). Tear down stale ones when done; `/disk-cleanup` reclaims them.

### Devbox: the same hybrid, with the stack on EC2

**Use a devbox (`hogli devbox:*`) instead of a sandbox when the laptop is the
constraint**: several full stacks at once, long agent runs, or disk and memory
already under pressure. Claude Code, MCP, and skills stay on the laptop; only
the stack moves. Repo skill: `setting-up-devbox`.

- `hogli devbox:sync` from the worktree root mirrors it one-way onto the box.
  One synced checkout per box, and the box sits on master, so check the branch
  out on the box first or every diverged file reports as a conflict.
- `hogli devbox:exec -- bash -lc 'cd ~/posthog && flox activate -- ./bin/hogli <cmd>'`
  replaces `docker exec`. Without `flox activate --` the shell has no `uv`,
  `sqlx`, `pnpm`, or `node`.
- `hogli devbox:forward --port <n>` replaces `localhost:<port>`. The backend on
  the box binds the Docker bridge address, so probe
  `http://172.17.0.1:8000/_health` there, not loopback. Do not gate on
  `hogli wait`; a `docker-compose` log unit crashes on the box and makes it
  return early.
- After pulling master onto a box whose image predates a migration squash,
  `migrations:up` fails with an inconsistent-history error. Fix with `hogli down`,
  `dev:reset -y`, `migrations:run -y`, `ensure:local:setup -y`,
  `dev:sync-flags -y`, `dev:demo-data -y`, `up -d -y`. `dev:reset -y` does not
  answer its nested schema-restore prompt, and that restore needs a `GH_TOKEN`
  Coder secret, which is why `migrations:run` replaces it.
- A box bills while running and auto-pauses after 12 idle hours. `hogli
  devbox:stop` when done. Terminated syncs can leave gigabytes under
  `~/.mutagen/staging` on the box; remove any staging dir that is not the live
  session.

**Stay on a sandbox when** the run must be on the laptop: a callback tunnel
from localhost for Slack, Stripe, or Vercel testing, or a quick throwaway
branch environment.

## Django migrations

- **Always use `python manage.py makemigrations`.** Never hand-write migration files; they end up with wrong dependencies or missing imports.
- **Never edit a migration after it has been committed.** Treat committed migrations as immutable and add a new one instead.
  - Exception, when not yet shared or deployed: `manage.py migrate app_name <previous>`, delete the file, point `app_name/migrations/max_migration.txt` at the previous migration, then `makemigrations` and `migrate`.
- **Strongly consider splitting migrations into separate PRs.** They review and merge quickly on their own, deploy earlier, and reduce risk on the feature PR.
- **Always run safety checks after creating one**: `python manage.py analyze_migration_risk` and `python manage.py makemigrations --check --dry-run`. Then `hogli ci:preflight --fix`, which catches migration leaf conflicts against master before CI does.
- Apply and inspect migrations with `hogli migrations:up`, `hogli migrations:run`, `hogli migrations:status`, and `hogli migrations:sync`. `makemigrations` stays raw Django; there is no hogli equivalent.
- **Test both regions** when the migration depends on settings or env vars: `CLOUD_DEPLOYMENT=EU|US python manage.py migrate app_name <n>`.

## Kea state management

**Prefer Kea actions for state logic.** When a component needs to manipulate state, especially with conditional logic, implement it as a Kea action rather than calling several Kea functions directly from the component. It keeps business logic in the logic layer, makes the behavior unit-testable and reusable, and the action name documents the intent.

Example: instead of calling `toggleFormulaMode()` directly after removing a formula, create one action, `removeFormulaAndToggleModeIfEmpty()`, that encapsulates the whole behavior.

## posthog.com (docs site)

Lives at `~/dev/posthog.com`. Setup, the `pnpm build` memory trap, and the MDX gotchas are in that repo's `CLAUDE.local.md`, which loads only when working there.

## File organization for working notes

Working files live in `~/dev/.claude/docs/`, organized by project. Project-specific files go in their project dir (`stripe/`, `vercel/`), each holding `specs/`, `scripts/`, `drafts/`, `investigations/`. Everything else goes in the top-level `specs/`, `scripts/`, `drafts/`, `investigations/`, `plans/`.

Use descriptive filenames (`test_provisioning_pat.py`, not `test.py`). Drafts are ephemeral, clean them up after sending. The directory is private by default; see its `README.md` for the safety policy.
