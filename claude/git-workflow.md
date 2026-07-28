# Git Workflow

## Workspaces: default to git worktrees

**Default to a git worktree for any task that creates or modifies code, unless told otherwise.** Don't work in the main checkout (keep it clean for parallel tasks), and never make a fresh full clone of a large repo: worktrees share one `.git`, whereas a second clone of a monorepo wastes tens of GiB.

```bash
cd "$HOME/dev/<main-repo>"
git worktree add ../<repo>-<short-task> -b <branch>   # new branch
git worktree add ../<repo>-<short-task> <existing>    # existing branch / PR
```

One worktree per branch/PR/task. That's what lets parallel work (`/babysit-prs`) run without several jobs fighting over a single checkout. Tear it down when the branch is merged or closed: `git worktree remove <path>` (never `rm -rf`), then `git worktree prune`. The branch ref survives, so nothing committed is lost.

**Work in place instead when**: I say so; it's a trivial read-only or single-file change on the current branch; or it's e2e/full-stack testing, which belongs in a sandbox.

## Pre-commit checks

Always lint before committing in repos with lint configs:

- JS/TS monorepos: `pnpm run lint` (auto-fix with `pnpm run lint --fix`)
- Python: `ruff check . --fix && ruff format .`

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

**Never arm auto-merge (or merge) without checking with me first.** Before asking, sweep the PR for unaddressed review comments, human AND bot (greptile, veria), and address or answer them. Then tell me what's outstanding, or that nothing is, and wait for my go.

A prior "ready to merge" covers the PRs it was said about, not later re-arms after new commits or new comments land.

Since 2026-07-28, **every PR in `posthog/posthog` merges through the [trunk.io merge queue](https://docs.trunk.io/merge-queue/merge-queue)**, not `gh pr merge`. After I give the go, enqueue with a `/trunk merge` comment or the `trunk-merge-queue-submit` label; removing the label dequeues. The queue applies its own state labels as the PR moves through.

## Pull requests

- **Never post PR comments without being asked.**
- **Always create PRs via the `/pr-ready` slash command**, never bare `gh pr create`. It owns draft status, reviewer assignment, the PR template, the pre-flight self-review, and the pre-PR checklists (lint, types, tests, plus the auth and billing extras).
- Everything else uses `gh`: `gh pr view|list|checks|diff|checkout|comment|review <number>`, and `gh pr edit <number> --add-reviewer <username>`.
- Titles use Conventional Commits with a **lowercase** type: `feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert: Description`. `refactor:` not `Refactor:`.
- If addressing a specific review comment, add that person as a reviewer.
