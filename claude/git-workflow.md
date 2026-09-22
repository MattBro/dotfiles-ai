# Git Workflow

## Main checkout: disposable, always refreshed

**Before reading or changing a repo, refresh its primary checkout to origin's default branch (`main`, or `master` where applicable).** This applies to investigations and read-only questions too. Identify the primary checkout with `git worktree list`; do not mistake the current task worktree for it.

**The primary checkout is a disposable copy of origin. I authorize discarding its staged and unstaged changes, untracked source files, and local-only commits on the default branch without asking, stashing, or backing them up.** Everyone must keep work in task worktrees. A dirty primary checkout is not a reason to skip updating, preserve an old revision, or ask me for confirmation. This authorization applies only to the primary checkout; preserve work in linked worktrees and other branches.

Fetch successfully before discarding anything. In the primary checkout, switch to the default branch, discard local changes, and make it match the fetched remote branch exactly. A normal `git pull --ff-only` is fine when the checkout is clean and can fast-forward; otherwise use the reset workflow below. A fetch failure is not permission to describe the checkout as current: report that limitation and retry or use another verified source.

```bash
# Run only after identifying the primary checkout and origin's default branch.
# Use master instead of main when that is origin's default.
set -e
git -C "$HOME/dev/<repo>" fetch origin
git -C "$HOME/dev/<repo>" switch --discard-changes main
git -C "$HOME/dev/<repo>" reset --hard origin/main
```

Remove untracked source files in the primary checkout as part of the refresh. Inspect `git clean -nd` first and exclude every registered nested worktree and its containing directories before cleaning. Keep ignored local configuration, secrets, dependencies, and caches; do not use `git clean -x`, double-force clean, or recursively delete a worktree container. Never force-push the remote default branch to match local state.

For current-state analysis, use the refreshed primary checkout or explicit `origin/main` reads. Check `git log origin/main` and deployment evidence before attributing a production issue to code. A feature worktree can contain an older base; do not present that as current main.

## Workspaces: all edits in git worktrees

**Use a task worktree for every edit, including documentation and single-file changes, unless I explicitly instruct otherwise.** The primary checkout is for refreshing and reading, never in-progress work. Never make a fresh full clone of a large repo: worktrees share its Git objects.

```bash
cd "$HOME/dev/<repo>"
git worktree add ../<repo>-<short-task> -b <branch> origin/main
git worktree add ../<repo>-<short-task> <existing-branch>
```

Use origin's actual default branch as the base for new work. Keep existing PR work in its branch's worktree; refreshing primary does not authorize resetting a task branch. One worktree per branch/PR/task lets parallel jobs run without fighting over a checkout. Full-stack testing belongs in the task's sandbox/worktree.

After merging, refresh the primary checkout again. Remove the finished task worktree with `git worktree remove <path>`, then `git worktree prune`; never `rm -rf` a registered worktree.

For bulk cleanup of task worktrees, use `hogli worktrees:clean` rather than a removal loop. Its protection for uncommitted or unpushed task work still applies:

```bash
hogli worktrees:clean --before 2w --mode deps --dry-run
hogli worktrees:clean --before 2w --mode full --dry-run
```

Always `--dry-run` first. `--repo PATH` points it at a repo that doesn't ship hogli.

## Read the repo's own CLAUDE.md before the first edit

A session started outside a checkout never loads that checkout's `CLAUDE.md`, and a cd into the repo later does not load it either. Before the first edit in any repo, read its `CLAUDE.md` (or `AGENTS.md`) and every doc it marks as required for the files being changed. `scripts/require-repo-instructions.py`, wired as a PreToolUse hook on Edit and Write in `~/.claude/settings.json`, denies the first edit per repo per session and prints the paths to read; the retry passes.

## Pre-commit and pre-push checks

Always lint before committing in repos with lint configs:

- PostHog monorepo: `hogli lint` and `hogli format`. See [hogli](hogli.md) for the
  full routing table.
- Other JS/TS monorepos: `pnpm run lint` (auto-fix with `pnpm run lint --fix`)
- Other Python repos: `ruff check . --fix && ruff format .`

**In the PostHog monorepo, run `hogli ci:preflight --fix` before every push.**
It catches the deterministic CI failures reachable from the diff (formatting,
lint, broken lockfiles, OpenAPI drift, migration conflicts, stale branch) so a
CI matrix is not burned on them. The repo's `.husky/pre-push` hook runs it too,
but only when `hogli` resolves on PATH, so do not rely on the hook alone.

**Preflight's type check is advisory and does not gate.** Run the authoritative one,
`uv run mypy --cache-fine-grained .`, after the final edit, and count test-only edits as
edits. A clean run from before the last change is not evidence about the current tree.

If pre-commit hooks fail with `command not found` (e.g. `pnpm`), run git through flox so dev dependencies are on PATH: `flox activate -- bash -c "git commit -m 'message'"`.

## CI size budgets: never raise them

**Never fix a failing size-budget check (bundle size, asset size) by increasing the budget.** The budgets exist to stop size degrading in tiny increments; bumping the limit whenever it trips defeats the check.

Treat a budget failure as a real regression: find what grew (new dependency, accidental import, duplicated chunk) and shrink it. If the increase seems genuinely justified, raise it with me or a colleague first. Never bump a budget unilaterally, and never as an automatic CI fix in `/babysit-pr` or `/ci-check`.

## Branch naming

PostHog conventions: `matt/description` is the most common, or a `feat/`, `fix/`, `refactor/`, `chore/` prefix. Check current PRs for the latest patterns.

## Commits

**Never amend commits.** Amending requires a force push; separate commits show the evolution of changes and let reviewers see the progression. Add a second commit instead: `fix: use line item periods for invoices`, then `refactor: extract _get_billing_period helper`.

## Git push

**Never force push unless explicitly asked.** Always try `git push` first. Use `git push --force-with-lease` only when I request it.

## Merging PRs and auto-merge

**Never arm auto-merge, or merge a PR into its base branch, without checking with me first.** Before asking, sweep the PR for unaddressed review comments, human AND bot (greptile, veria), and address or answer them. Then tell me what's outstanding, or that nothing is, and wait for my go.

This rule is about landing a PR. Updating a branch from its base is the opposite direction and needs no approval: merge master into a feature branch whenever it unblocks CI or clears a conflict, and just say you did.

A prior "ready to merge" covers the PRs it was said about, not later re-arms after new commits or new comments land.

Since 2026-07-28, **every PR in `posthog/posthog` merges through the [trunk.io merge queue](https://docs.trunk.io/merge-queue/merge-queue)**, not `gh pr merge`. After I give the go, enqueue with a `/trunk merge` comment or the `trunk-merge-queue-submit` label; removing the label dequeues. The queue applies its own state labels as the PR moves through.

**Read the existing comments immediately before posting one.** Not the copy fetched earlier in the session, a fresh read at the moment of posting. A colleague may have said the same thing while I was working, and a duplicate `/trunk merge`, "fixed in abc123", or bot reply is noise on a PR other people are reading. If the comment I was about to write already exists, say so and post nothing.

## Pull requests

- **Never post PR comments without being asked.**
- **Always create PRs via the `/pr-ready` slash command**, never bare `gh pr create`. It owns draft status, reviewer assignment, the PR template, the pre-flight self-review, and the pre-PR checklists (lint, types, tests, plus the auth and billing extras). Never assign reviewers while the PR is a draft; assign them only after marking it ready for review.
- Everything else uses `gh`: `gh pr view|list|checks|diff|checkout|comment|review <number>`, and `gh pr edit <number> --add-reviewer <username>`.
- Titles use Conventional Commits with a **lowercase** type: `feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert: Description`. `refactor:` not `Refactor:`.
- If addressing a specific review comment, add that person as a reviewer.
- PR descriptions in the PostHog monorepo come from the repo's `writing-pr-descriptions` skill, with no extra style pass and no word cap on top. In other repos, fill the PR template plainly. Keep the description in sync with the code on every later push.
