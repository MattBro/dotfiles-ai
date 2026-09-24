# Git Checkouts

## Main checkout: disposable, always refreshed

**Before reading or changing a repo, refresh its primary checkout to origin's default branch** (`main`, or `master` where applicable), for read-only questions too. Identify it with `git worktree list`; never mistake the current task worktree for it.

**The primary checkout is a disposable copy of origin. I authorize discarding its staged and unstaged changes, untracked source files, and local-only commits on the default branch without asking, stashing, or backing them up.** Everyone keeps work in task worktrees. A dirty primary checkout is never a reason to skip updating, preserve an old revision, or ask me. The authorization covers only the primary checkout; preserve work in linked worktrees and other branches.

Target the primary checkout explicitly, never the current directory (use `master` where that is origin's default):

```bash
set -e
git -C "$HOME/dev/<repo>" fetch origin
git -C "$HOME/dev/<repo>" switch --discard-changes main
git -C "$HOME/dev/<repo>" reset --hard origin/main
```

Discard nothing until the fetch succeeds. After a failed fetch, never call the checkout current: report it, then retry or use another verified source. `git pull --ff-only` is fine when the checkout is clean and can fast-forward. Then remove untracked source files: inspect `git -C "$HOME/dev/<repo>" clean -nd` first and exclude every registered nested worktree and its containing directories. Keep ignored config, secrets, dependencies, and caches: never `git clean -x`, double-force clean, or recursively delete a worktree container.

Never force-push the remote default branch. For current-state analysis, read the refreshed primary checkout or `origin/main`, never a feature worktree's older base. Check `git log origin/main` and deployment evidence before attributing a production issue to code.

## Worktrees for every edit

**Use a task worktree for every edit, including docs and single-file changes, unless I explicitly say otherwise.** Use one worktree per branch, PR, or task. Never make a fresh full clone of a large repo.

```bash
cd "$HOME/dev/<repo>"
git worktree add ../<repo>-<short-task> -b <branch> origin/main
git worktree add ../<repo>-<short-task> <existing-branch>
```

Base new work on origin's actual default branch. Keep existing PR work in its branch's worktree; refreshing primary does not authorize resetting a task branch. Run full-stack tests in the task's sandbox or worktree. After merging, refresh the primary checkout, then `git worktree remove <path>` and `git worktree prune`; never `rm -rf` a registered worktree. For bulk cleanup, use `hogli worktrees:clean`, which protects uncommitted and unpushed work. Always dry-run first; `--repo PATH` targets a repo that doesn't ship hogli.

```bash
hogli worktrees:clean --before 2w --mode deps --dry-run
hogli worktrees:clean --before 2w --mode full --dry-run
```

## Before the first edit in a repo

Before the first edit in any repo, read its `CLAUDE.md` or `AGENTS.md` and every doc it marks as required for the files you change; a session started outside the checkout never loaded them. In Claude Code, the `require-repo-instructions.py` hook denies the first edit per repo per session and lists the paths; the retry passes.
