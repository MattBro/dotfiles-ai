---
description: Work with PostHog sandbox environments - create, manage, and run commands in isolated full-stack dev environments
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

# PostHog Sandbox Manager

Manage isolated PostHog dev environments. Each sandbox gets its own Postgres, ClickHouse, Redis, Kafka, etc.

Arguments: $ARGUMENTS (e.g. "create matt/my-feature", "test", "run pytest path/to/test.py", "list", "destroy matt/my-feature")

## Reach for a sandbox first for anything that needs to run

If a task requires manual/browser testing, starting Celery workers, exercising an end-to-end flow, or anything beyond a pytest run, **`bin/sandbox create <branch>` is the right first move.** Don't try to run the local dev loop (`bin/start-backend` + `bin/start-frontend`) from a worktree — it has two recurring failure modes that cost tens of minutes of debugging:

1. **Zombie Vite.** Long-running `pnpm start-vite` processes can leave the `concurrently` / `turbo` wrappers alive while the Vite child has died silently. `ps` shows everything "running" but `lsof -nPi :8234 -sTCP:LISTEN` returns nothing — the Django template still ships `<script src="http://localhost:8234/@vite/client">`, so pages render blank white with no obvious error. **If you see a blank PostHog page, check the Vite listener first** (`lsof -nPi :8234`); a dead listener is the usual cause.
2. **`bin/start-frontend` can exit 0 without hosting.** With the node engine mismatch (repo wants `>=24 <25`, nvm default is often 22) and turbo's daemon mode, the script returns immediately after `pnpm install` without leaving Vite bound.

The sandbox container supervises both backend and Vite, restarts dead children, and isolates Postgres / ClickHouse / Redis / Kafka per branch — none of the above can bite.

## Registry

The sandbox registry lives at `~/.posthog-sandboxes/registry.json`. Each entry maps a branch name to:
```json
{"slug": "matt-my-feature", "port": 48001, "worktree": "/Users/mattbrooker/.worktrees/posthog/matt/my-feature"}
```

## Naming conventions

- Slug: branch name lowercased, `/` replaced with `-`, non-alphanumeric replaced with `-`
- Docker project: `sandbox-{slug}`
- App container: `sandbox-{slug}-app-1`
- Worktree path: `~/.worktrees/posthog/{branch}`

## Commands

### Determine the active sandbox

If no branch is specified, detect it from the current git branch or working directory:

```bash
# Check if we're in a worktree
BRANCH=$(cd "$PWD" && git branch --show-current 2>/dev/null)
# Check registry for this branch
cat ~/.posthog-sandboxes/registry.json
```

### Create a sandbox

```bash
HUSKY=0 bin/sandbox create <branch>
```

Note: `HUSKY=0` is required to skip a post-checkout hook that fails with SSL errors.

If this is the first-ever sandbox, the database cache build takes ~10 minutes. Subsequent creates take ~1-2 minutes.

**Non-interactive create exits 1 but still works.** When an agent runs `bin/sandbox create` (no TTY), it errors at the very end with `cannot attach stdin to a TTY-enabled container because stdin is not a terminal`. The sandbox is still created and running — the failure is only the final attach-to-window step. Don't treat the exit-1 as a failed create or re-run it: check `bin/sandbox list`, confirm the branch shows `running`, and proceed via `docker exec`.

The sandbox web UI is accessible at `http://localhost:<port>` (check `bin/sandbox list` for the port). Login: `test@posthog.com` / `12345678`.

**Migrations run on first boot (~3-5 min) before Django serves.** Until they finish, the port returns 502 and `manage.py shell` is slow/cold. Watch `docker exec <c> cat /tmp/sandbox-progress`, or poll the port for non-502.

**Testing Django admin doesn't need the frontend.** The admin (`/admin/...`) is server-rendered, so it works even when the SPA is blank or Vite/esbuild has crashed (`[plugin:vite:esbuild] ... EPIPE`, blank white page on first boot). `/admin/login/` redirects through the SPA `/login`, so if Vite is down: log in once the SPA renders, or reuse an existing session, then navigate straight to the server-rendered admin URL. A user needs `is_staff` + `is_superuser` for `/admin` — set it via shell if the seeded user lacks it.

### Run commands inside a sandbox

**This is the key pattern.** Claude Code runs on the host and keeps access to all tools (MCP, skills, filesystem). Test and management commands are routed through `docker exec`:

```bash
# Get the container name from the registry
SLUG=$(python3 -c "import json; r=json.load(open('$HOME/.posthog-sandboxes/registry.json')); e=r.get('$BRANCH',{}); print(e.get('slug',''))")
CONTAINER="sandbox-${SLUG}-app-1"

# Run tests
docker exec $CONTAINER pytest posthog/api/test/test_foo.py -v

# Run Django management commands
docker exec $CONTAINER python manage.py migrate
docker exec $CONTAINER python manage.py shell -c "from posthog.models import Team; print(Team.objects.count())"

# Run frontend commands
docker exec $CONTAINER pnpm --filter=@posthog/frontend typescript:check
docker exec $CONTAINER pnpm --filter=@posthog/frontend test

# Run linting
docker exec $CONTAINER ruff check . --fix
docker exec $CONTAINER ruff format .
```

File edits happen on the host (in the worktree at `~/.worktrees/posthog/<branch>`) and are immediately visible inside the container via the volume mount.

### List sandboxes

```bash
bin/sandbox list
```

### Stop / start / destroy

```bash
bin/sandbox stop <branch>
bin/sandbox start <branch>
bin/sandbox destroy <branch>
```

### View logs

```bash
bin/sandbox logs <branch>
# Or directly:
docker logs sandbox-<slug>-app-1 --tail 50
```

## Workflow

When the user asks to work on something that needs testing:

1. Check if a sandbox is already running for the current branch (`bin/sandbox list`)
2. If not, offer to create one
3. Edit files on the host (in the worktree or main repo)
4. Run tests via `docker exec` into the sandbox container
5. Iterate until tests pass

When using agents with `isolation: "worktree"`, the agent works in a git worktree on the host. If a sandbox exists for that branch, the agent can run tests through the sandbox container.

## Iterating on code without rebuilding

`bin/sandbox create` checks out the branch at the commit that existed when you ran it. For quick iteration after you've made local changes on top of that commit:

- **Single-file edits**: `docker cp <host-path> sandbox-<slug>-app-1:/workspace/<path>`. Vite and Django's `runserver --noreload`-style supervisor will pick up most changes automatically.
- **New Python imports / migrations**: after `docker cp`, run `docker exec sandbox-<slug>-app-1 python manage.py migrate` or restart the app container.
- **If you've pushed your branch remotely**, `docker exec <container> git -C /workspace fetch host <branch> && git reset --hard FETCH_HEAD` (if the host-git remote exists) is cleaner than per-file `docker cp`.

## Troubleshooting

- Blank white PostHog page in the browser: check Vite listener on the sandbox's Vite port, then the app container logs. (Inside the sandbox this is supervised; if it's broken, the container itself is sick.)
- If sandbox is stuck: `bin/sandbox logs <branch>` to check container logs
- Nuclear option: `bin/sandbox nuke` destroys everything and rebuilds cache on next create
- If the proxy returns 502, the app may still be booting - wait and retry
- Health check: `curl -s http://localhost:<port>/_health`. Until it returns 200 or 302, the app is still booting.
- If the sandbox was created from an old commit and doesn't have your latest code, either `docker cp` the changed files or `bin/sandbox destroy <branch> && bin/sandbox create <branch>` to rebuild from the tip of the branch.
- **`pkill -f` is dangerous in the app container.** Patterns like `pkill -f vite` will kill turbo/pnpm/concurrently wrappers AND the long-lived `node` process holding the pnpm node_modules lock. Side effect: next start of the frontend triggers a full `pnpm install` (10+ min over slow npm registry mirrors). Restart granian by killing only the supervisor PID (the parent `granian asgi …` process), not by pattern. For Vite, prefer `bin/sandbox restart <branch>` over manual pkill.
- **`bin/start-frontend` needs a TTY.** Spawning it via `docker exec -d` (detached) errors with `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`. Set `CI=true` in the env so pnpm skips the interactive remove.

## Exposing a sandbox via ngrok (for OAuth redirect testing, etc.)

Some flows (Stripe marketplace install, OAuth callbacks from third parties) require Stripe/the partner to redirect back to a public HTTPS URL that lands on your local code. ngrok in front of a sandbox works, but requires three patches:

1. **Caddy site address must be host-agnostic.** The default `Caddyfile` has `http://localhost:8000 {` as the site block. Caddy refuses to serve responses for unknown Host headers, so requests proxied via ngrok come back as `200`/empty body. Replace the first line with `:8000 {` so any Host matches:
   ```bash
   docker exec sandbox-<slug>-proxy-1 sh -c "sed -i '1s|.*|:8000 {|' /etc/caddy/Caddyfile && caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile"
   ```
   Do NOT add `https://` for the ngrok hostname — Caddy will try to obtain a Let's Encrypt cert and fail (ngrok terminates TLS, Caddy never sees the public 443).

2. **Vite assets must proxy through Caddy on the same origin.** Django emits `<script src="{JS_URL}/@vite/client">` where `JS_URL=http://localhost:49008` (the host's mapped Vite port). Loading those over an HTTPS ngrok page is mixed-content and the browser blocks. Two fixes are needed in tandem:

   a. **Add a Vite path matcher to Caddy** that rewrites `Host: localhost` so Vite's allowed-host check accepts it:
   ```caddyfile
   :8000 {
       @vite path /@vite/* /@id/* /@fs/* /@react-refresh /src/* /node_modules/.vite/* /node_modules/* /__vite_ping
       handle @vite {
           reverse_proxy app:8234 {
               header_up Host localhost
           }
       }
       # ... existing matchers ...
   }
   ```

   b. **Make `posthog/utils.py:get_js_url` return `''`** so the rendered tags become same-origin `/`, served through Caddy:
   ```python
   def get_js_url(request: HttpRequest) -> str:
       return ''
   ```
   Edit on the host worktree (so the volume mount picks it up). Restart granian (kill the supervisor PID, then `nohup ./bin/start-backend > /tmp/backend.log 2>&1 &` inside the container if phrocs doesn't respawn it).

3. **Cookies are origin-scoped.** A login session on `localhost:<port>` will not transfer to the ngrok hostname. Log in *via* the ngrok URL once both patches above are in place.

After the patches: `curl -sI https://<your>.ngrok-free.dev/_health` should return 200, and `/integrations/<kind>/callback?…` should return the SPA HTML rather than empty body.
