---
description: Diagnose disk usage and reclaim space safely — surfaces biggest offenders, proposes wins, pauses for approval before anything destructive
allowed-tools: Bash, Read
---

# Disk Cleanup

Find what's eating disk and reclaim space safely. **Never delete without confirmation** for anything non-trivial — surface options, wait for the user to pick.

## 1. Current state

```bash
df -h /
du -sh "$HOME/Library/Caches" "$HOME/dev" "$HOME/.claude" /var/folders 2>/dev/null
```

Report free space and the big three buckets.

## 2. Safe quick wins (ask before running)

These are almost always safe — regenerating caches. Ask user if they want all of them or a subset.

```bash
# Stale app-update installers (ShipIt)
rm -rf "$HOME/Library/Caches/com.*.ShipIt"

# Rust compiler cache (regenerates on next build)
rm -rf "$HOME/Library/Caches/Mozilla.sccache"

# Package manager caches
brew cleanup -s
yarn cache clean
pnpm store prune
```

Skip Chrome/Google cache unless Chrome is closed — deleting while running can corrupt the profile.

## 3. Library/Caches deep dive

```bash
du -sh "$HOME/Library/Caches/"* 2>/dev/null | sort -h | tail -15
```

## 4. `~/dev` — duplicate repo clones

Large monorepos accumulate clones (`repo`, `repo-2`, `repo-3`, `repo-x`, etc.) and each can be tens of GiB.

```bash
du -sh "$HOME/dev/"* 2>/dev/null | sort -h | tail -15
```

Before deleting any repo, **always check for unpushed work**:

```bash
cd "$HOME/dev/<repo>"
git status --short
git for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track)' refs/heads/ | awk '$3 ~ /ahead/ || ($2 == "" && $3 == "")'
```

Flag any branch that is `[ahead N]` or has no upstream. Offer to push your own branches before deletion. Do NOT push other people's branches or use `git push --all` — that can recreate branches that were intentionally deleted on origin.

**If the target is a git worktree (not a clone)**: use `git worktree remove <path>` from the main repo, not `rm -rf`, to avoid dangling worktree references. Check with `git worktree list`.

## 5. Large monorepo elephants

Inside the main monorepo (replace `<repo>` with the actual name):

```bash
du -sh "$HOME/dev/<repo>/"* "$HOME/dev/<repo>/".[^.]* 2>/dev/null | sort -h | tail -15
```

Common huge dirs:

- **`rust/target/`** — Cargo artifacts, can be 50-60 GiB. `rm -rf rust/target` (if cargo lives behind flox; `cargo clean` from outside flox env won't find it).
- **`.claude/worktrees/`** — Claude sandbox worktrees, often a few GiB each. List with `git worktree list`. Remove stale ones with `git worktree remove --force <path>`.
- **`node_modules/`**, **`.venv/`**, **`.flox/`** — can be recreated but takes time. Only touch if user confirms.
- **`.git/`** — can be 5+ GiB. `git gc --aggressive --prune=now` shrinks it but is slow.

## 6. Docker / OrbStack

```bash
docker system df
```

If containers are stopped, `docker volume prune -f` and `docker builder prune -af` can free a lot. **Note:** `docker system df` shows "reclaimable" but volumes attached to running containers won't actually free. Stop unneeded containers first.

## 7. Final report

Show before/after free space, per-step reclaimed amounts, and anything still worth investigating that wasn't touched.

## Rules

- Never `git push --all` — push branches one at a time after verifying they're your own work.
- Never skip hooks (`--no-verify`) unless user explicitly asks.
- Never delete `.flox/`, `node_modules/`, `.venv/` without explicit confirmation — rebuilds are slow even though they're "safe".
- Always use `git worktree remove` for worktrees, not `rm -rf`.
- For Chrome/Google cache, only clean if Chrome is closed.
