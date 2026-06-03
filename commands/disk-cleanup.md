---
description: Diagnose disk usage and reclaim space autonomously — finds the biggest offenders by reclaim value and clears them top-down without pausing for approval, protecting unpushed/dirty work
allowed-tools: Bash, Read, Edit, Write
---

# Disk Cleanup

Find what's eating disk and reclaim it. Work top-down: biggest reclaim first.

**Run autonomously — do not pause for confirmation.** Execute every reclaim step in this doc without asking the user to approve or pick. The guards below are not confirmation gates; they are correctness checks that prevent *data loss*, and they always apply:

- Never destroy unpushed/uncommitted/detached-HEAD work (see §2). Removing a worktree is safe because the branch ref survives — but a dirty working tree or detached HEAD is not on any ref, so preserve those first.
- Never `rm -rf` a registered worktree; never `git push --all`; never force-push; never `--no-verify`.
- Only clean Chrome/Google caches while Chrome is closed.

Within those guards, delete freely and report what you did in the final summary (§7).

## 1. Current state — find the real free space

On macOS, `df -h /` reports the read-only system snapshot and **lies about free space**. The volume under pressure is the Data volume.

```bash
df -h /System/Volumes/Data 2>/dev/null || df -h /
du -sh "$HOME/dev" "$HOME/Library/Application Support" "$HOME/Library/Caches" "$HOME/.claude" /nix 2>/dev/null | sort -rh
docker system df 2>/dev/null
du -sh "$HOME/OrbStack" 2>/dev/null
```

Report free space and rank the buckets by size. The usual heavy hitters, in descending reclaim value:

1. Git worktrees on merged branches (§2)
2. Stale Docker / OrbStack sandbox containers + volumes (§3)
3. Duplicate repo clones (§4)
4. Nix store with no garbage collection (§5)
5. App caches and stale update installers (§6)

## 2. Git worktrees — usually the biggest `~/dev` win

Worktrees accumulate fast (one per branch/PR/sandbox) and each carries its own `node_modules`, `.venv`, build artifacts — often 3-5 GiB apiece. Dozens of them is normal.

```bash
cd "$HOME/dev/<main-repo>"
git worktree list | wc -l
git worktree list
```

**Key fact that makes this safe and autonomous:** `git worktree remove` deletes only the working-tree directory — the **branch ref survives** in the shared `.git`. So removing a worktree never loses committed work, even unpushed commits; you can always `git worktree add` it back later. The only things that *are* lost are (a) uncommitted changes in a dirty tree and (b) commits reachable only from a **detached HEAD**. Preserve those, reclaim everything else.

**Detecting merged branches: do NOT trust `git branch --merged`.** Repos that squash-merge PRs (e.g. PostHog) rewrite history, so a merged branch is *not* an ancestor of master and `--merged` misses it entirely. Use the PR state from GitHub instead:

```bash
cd "$HOME/dev/<main-repo>"
git fetch origin --quiet
gh pr list --state all --limit 300 --author "@me" --json headRefName,state,number > /tmp/my_prs.json
# map each worktree branch -> PR state (MERGED / CLOSED / OPEN / NO_PR)
git worktree list --porcelain | awk '/^branch /{sub("refs/heads/","",$2); print $2}' | sort -u | while read -r b; do
  st=$(jq -r --arg b "$b" '.[]|select(.headRefName==$b)|"\(.state) #\(.number)"' /tmp/my_prs.json | head -1)
  echo "$b -> ${st:-NO_PR}"
done
# per-worktree dirty / detached check (the only data-loss risks):
for wt in $(git worktree list --porcelain | awk '/^worktree/{print $2}'); do
  head=$(git -C "$wt" symbolic-ref -q --short HEAD || echo "DETACHED")
  dirty=$(git -C "$wt" status --porcelain | head -1)
  echo "$wt | $head | dirty:${dirty:+yes}"
done
```

Disposition, applied automatically:

- **MERGED or CLOSED PR** → remove the worktree (`--force`). Branch + origin retain the code.
- **OPEN PR** → keep (active work).
- **NO_PR, on a branch** → remove the worktree; the branch ref preserves any local commits. (Agent/babysit/temp leftovers like `.claude/worktrees/*`, `babysit-*`, `agent-*` are the bulk here.)
- **Dirty working tree** on a branch you're removing → if the diff is only build artifacts (`frontend/dist`, `node_modules`), `--force` is fine; if there are tracked source edits or untracked source/test files, copy them to `~/dev/.claude/docs/investigations/` first, then remove.
- **Detached HEAD with commits ahead** → rescue first: `git -C "$wt" branch rescue/<name>`, then remove.

```bash
git worktree unlock <path>          # if locked, before removing
git worktree remove --force <path>  # removes dir even with build artifacts; branch ref stays
git worktree prune                  # clean up dangling refs after
```

Never `rm -rf` a *registered* worktree (it leaves dangling refs — use `git worktree remove`). An already-orphaned/unregistered dir under a worktree container *is* fine to `rm -rf`, followed by `git worktree prune`. Never `git push --all` (it can resurrect branches deleted on origin).

## 3. Docker / OrbStack — the largest single pool

OrbStack's on-disk size is dominated by Docker volumes. `docker system df` shows "reclaimable" low because volumes attached to **existing** containers don't count — the win is removing stale **containers** so their volumes free up.

```bash
docker system df
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}' | sort
```

PostHog sandboxes (`bin/sandbox`) are per-branch full-stack envs — each is a heavy set of containers + volumes. Pruning is **safe by construction**: `prune` only touches *stopped* containers and *unattached* volumes, so a sandbox you're actively running (containers up) is never affected. Run all four unconditionally:

```bash
docker builder prune -af              # build cache — regenerates
docker image prune -af                # dangling + unreferenced images
docker container prune -f             # STOPPED containers only (running sandboxes untouched)
docker volume prune -a -f             # volumes attached to NO container — see -a note below
```

**`docker volume prune` gotcha:** without `-a` it removes only *anonymous* volumes. Named volumes (most sandbox data: postgres, clickhouse, kafka) survive even when orphaned. After removing stopped containers, their named volumes are orphaned — `docker system df` will still show a large "RECLAIMABLE" volume figure. Run `docker volume prune -a -f` to actually reclaim them. Order matters: remove containers *first*, then prune volumes, or the volumes stay pinned.

Caveat the autonomy: pruning stopped containers destroys any sandbox you'd paused but intended to resume (it's recreatable from the branch, just slow). That's the one judgement call — note in the final report which sandboxes went, don't withhold the prune.

Note: `docker system df` and prunes can take 30-60s and the daemon may be slow to first respond if the OrbStack VM was idle-stopped. Don't use `timeout` (absent on macOS); run in the background or use `gtimeout` if you need a budget. The real OrbStack disk lives in `~/Library/Group Containers/*orbstack/data/data.img.raw` (a sparse file — `ls -lah` over-reports; trust `docker system df` for actual usage). `du "$HOME/OrbStack"` can hang on the virtiofs mount — avoid it.

## 4. Duplicate repo clones

Large monorepos accumulate full clones (`repo`, `repo-code`, `repo-2`, `repo-x`) alongside worktrees — each can be tens of GiB. A second full clone is often redundant with worktrees off the primary.

```bash
du -sh "$HOME/dev/"*/ 2>/dev/null | sort -rh | head -20
```

Before deleting any clone, **check for unpushed work**:

```bash
cd "$HOME/dev/<repo>"
git status --short
git for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track)' refs/heads/ \
  | awk '$3 ~ /ahead/ || ($2 == "" && $3 == "")'
```

A second clone is only redundant if it has **no unique unpushed branches and a clean tree** — then remove it. If it carries its own branches with no upstream (a side project, a long-lived experiment), it is *not* a duplicate; keep it and note its size in the report. A clone checked out on an unfamiliar branch with its own worktrees is the classic "looks redundant, isn't" trap — verify before deleting.

### Monorepo elephants (inside a clone)

```bash
du -sh "$HOME/dev/<repo>/".git "$HOME/dev/<repo>"/{rust/target,node_modules,.venv} 2>/dev/null | sort -rh
```

- **`rust/target/`** — Cargo artifacts, 50-60 GiB when present. If cargo runs behind flox, `rm -rf rust/target` (a bare `cargo clean` outside the flox env won't find it). Safe to clear autonomously.
- **`node_modules/`, `.venv/`, `.flox/` in the *active* main clone** — leave these. They're recreatable but the rebuild is slow and you'd be kneecapping the repo the user works in daily. (Worktree copies of these go automatically when the worktree is removed in §2 — that's the intended reclaim.)
- **`.git/`** — the shared object store. If `git fetch`/`gc` warns about "too many unreachable loose objects" or a stale `.git/gc.log`, run `rm -f .git/gc.log && git gc --prune=now` (drops the loose objects; background it on a large repo). `--aggressive` shrinks more but is much slower — skip unless space is desperate.

## 5. Nix store

The flox/nix store at `/nix` never garbage-collects on its own and grows unbounded.

```bash
du -sh /nix 2>/dev/null
nix-collect-garbage -d          # removes all unreferenced store paths
```

Safe — it only drops paths no current generation references. Active flox/nix envs are untouched.

## 6. App caches and stale update installers — trivially safe

```bash
# Stale Sparkle/ShipIt update installers (downloaded, already applied) — all apps:
du -shc "$HOME/Library/Caches/"*ShipIt* 2>/dev/null | tail -1
rm -rf "$HOME/Library/Caches/"*ShipIt*

# Package manager caches (regenerate on next use):
brew cleanup -s
pnpm store prune
yarn cache clean 2>/dev/null

# Other regenerating caches:
rm -rf "$HOME/Library/Caches/ms-playwright"   # re-downloads browsers on next install
rm -rf "$HOME/Library/Caches/node-gyp"
```

Deep-dive the rest before touching:

```bash
du -sh "$HOME/Library/Caches/"*/ 2>/dev/null | sort -rh | head -15
du -sh "$HOME/Library/Application Support/"*/ 2>/dev/null | sort -rh | head -15
```

- **Chrome/Google** (Caches + App Support, often 10+ GiB combined): only clean while **Chrome is closed** — deleting a live profile corrupts it.
- **Claude / Slack / Spotify / Figma App Support**: large but live app data, not cache. Don't delete; mention size only.

## 7. Final report

Show before/after free space on the Data volume, per-step reclaimed amounts, and anything still large that wasn't touched (with why).

## Rules

**Autonomous by default — do not pause for approval.** Work top-down, biggest reclaim first, and execute each step. The rules below are data-loss guards, not confirmation gates:

- Detect merged branches by **PR state** (`gh pr list`), never `git branch --merged` — squash-merge defeats ancestry checks.
- Removing a worktree keeps its branch ref, so reclaim merged/closed/no-PR worktrees freely. Before removing, preserve only the two things that *aren't* on a ref: a **dirty tree** (copy real source/test edits to `~/dev/.claude/docs/investigations/` first; build artifacts like `frontend/dist`/`node_modules` need no saving) and a **detached HEAD** (`git branch rescue/<name>` first).
- Always `git worktree remove` (with `--force`/`unlock` as needed), never `rm -rf`, for *registered* worktrees. An already-orphaned/unregistered dir may be `rm -rf`'d, then `git worktree prune`.
- Docker: run all four prunes unconditionally (`prune` can't touch running containers or attached volumes); use `docker volume prune -a -f` to catch orphaned named volumes.
- Leave the active main clone's `node_modules/.venv/.flox`; clear `rust/target` and worktree-local copies freely.
- Never `git push --all`; never force-push; never `--no-verify`.
- Only clean Chrome/Google caches when Chrome is closed.
- Keep: open-PR worktrees, the main checkout, and any second clone with its own unpushed branches.
- Report everything done in §7 — autonomy means no prompts, not no transparency.
