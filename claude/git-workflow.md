# Git Workflow

## Pre-commit and pre-push checks

- Outside the PostHog monorepo, lint before committing in repos with lint configs: `pnpm run lint` (`--fix` to auto-fix) for JS/TS, `ruff check . --fix && ruff format .` for Python.
- In the PostHog monorepo, run `hogli lint` and `hogli format` before committing and `hogli ci:preflight --fix` before every push. Don't rely on the pre-push hook: it skips preflight when `hogli` is not on PATH. Preflight's type check is advisory; run `uv run mypy --cache-fine-grained .` after the final edit, counting test-only edits.
- If hooks fail with `command not found` (e.g. `pnpm`), commit through flox: `flox activate -- bash -c "git commit -m 'message'"`.

## CI size budgets: never raise them

**Never fix a failing size-budget check (bundle size, asset size) by raising the budget.** Find what grew (new dependency, accidental import, duplicated chunk) and shrink it. If an increase seems justified, raise it with me or a colleague first. Never bump a budget unilaterally, or as an automatic CI fix in `/babysit-pr` or `/ci-check`.

## Branches, commits, pushes

- PostHog branch conventions: `matt/description`, or a `feat/`, `fix/`, `refactor/`, `chore/` prefix. Check current PRs for the latest patterns.
- **Never amend commits.** Amending needs a force push and hides the progression from reviewers; add a new commit.
- **Never force push unless I ask.** Try `git push` first; use `--force-with-lease` only when I request it.

## Merging PRs

**Never arm auto-merge or merge a PR into its base without checking with me first.** Before asking, sweep the PR for unaddressed review comments, human and bot (greptile, veria), and address or answer them. Then tell me what's outstanding, or that nothing is, and wait for my go. A prior "ready to merge" covers only the PRs it named, not re-arms after new commits or comments. Updating a branch from its base needs no approval: merge master in whenever it unblocks CI or clears a conflict, and say so.

Every `posthog/posthog` PR merges through the Trunk merge queue, not `gh pr merge`. After my go, comment `/trunk merge` or add the `trunk-merge-queue-submit` label; removing the label dequeues.

**Re-read a PR's comments immediately before posting one**, since a colleague may have posted the same thing while you worked. If the comment you were about to write already exists (a duplicate `/trunk merge`, "fixed in abc123", or bot reply), say so and post nothing.

## Pull requests

- **Never post PR comments without being asked.**
- **Create PRs only via `/pr-ready`**, never bare `gh pr create`. It owns draft status, reviewer assignment, the template, the self-review, and the pre-PR checklists. Assign reviewers only after marking the PR ready, never on a draft.
- Use `gh` for everything else, including `gh pr edit <number> --add-reviewer <username>`.
- Titles use Conventional Commits with a **lowercase** type: `feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert: Description`.
- When addressing a specific review comment, add that person as a reviewer.
- PostHog monorepo PR descriptions come from the repo's `writing-pr-descriptions` skill, with no extra style pass or word cap. Elsewhere, fill the PR template plainly. Keep the description in sync with the code on every push.
