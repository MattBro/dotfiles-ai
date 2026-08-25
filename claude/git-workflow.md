# Git Workflow

## Workspaces: default to git worktrees

**Default to a git worktree for any task that creates or modifies code, unless told otherwise.** Don't work in the main checkout (keep it clean for parallel tasks), and never make a fresh full clone of a large repo: worktrees share one `.git`, whereas a second clone of a monorepo wastes tens of GiB.

```bash
cd "$HOME/dev/<main-repo>"
git worktree add ../<repo>-<short-task> -b <branch>   # new branch
git worktree add ../<repo>-<short-task> <existing>    # existing branch / PR
```

One worktree per branch/PR/task. That's what lets parallel work (`/babysit-prs`) run without several jobs fighting over a single checkout. Tear it down when the branch is merged or closed: `git worktree remove <path>` (never `rm -rf`), then `git worktree prune`. The branch ref survives, so nothing committed is lost.

For bulk cleanup of accumulated worktrees, use `hogli worktrees:clean` instead
of a loop of `git worktree remove`. It selects by age, skips worktrees holding
uncommitted or unpushed work, handles orphaned admin entries, and takes
`--mode deps` to strip `node_modules` and build artifacts while keeping the code:

```bash
hogli worktrees:clean --before 2w --mode deps --dry-run
hogli worktrees:clean --before 2w --mode full --dry-run
```

Always `--dry-run` first. `--repo PATH` points it at a repo that doesn't ship hogli.

**Work in place instead when**: I say so; it's a trivial read-only or single-file change on the current branch; or it's e2e/full-stack testing, which belongs in a sandbox.

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
- **Always create PRs via the `/pr-ready` slash command**, never bare `gh pr create`. It owns draft status, reviewer assignment, the PR template, the pre-flight self-review, and the pre-PR checklists (lint, types, tests, plus the auth and billing extras).
- Everything else uses `gh`: `gh pr view|list|checks|diff|checkout|comment|review <number>`, and `gh pr edit <number> --add-reviewer <username>`.
- Titles use Conventional Commits with a **lowercase** type: `feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert: Description`. `refactor:` not `Refactor:`.
- If addressing a specific review comment, add that person as a reviewer.

## PR description style

Concise, concrete, and human — no generated-looking implementation diaries.

- A few sentences on what changed and why. Focus on behavior, meaningful design choices, and non-obvious caveats.
- **Never enumerate every file changed, implementation step, or command run.** Cut repetition and anything obvious from the diff.
- Fill the repo's PR template sections with substance. If a section genuinely doesn't apply, one line saying so beats boilerplate.
- **Testing section: describe how the behavior was validated, not the commands used.** A brief manual scenario someone else could reproduce, or a one-line statement of new/updated test coverage ("added coverage for anonymous users matching mixed property conditions"). No lists of lint, typecheck, or build commands. Include an exact command only when it matters for reproducing something unusual. Never claim a test ran unless it actually ran.
- Final pass before publishing: sound like a competent engineer, not an agent. Distinguish what was implemented, what was tested, and what remains uncertain. Mention real risks or follow-up work briefly; don't invent them to fill a section.

Applies to the initial description and every later update (the description stays in sync with the code as it evolves).

**Every PostHog PR description gets a final pass through the `unambiguous-agent-text` skill.** Invoke the skill; do not approximate it from memory. This is required on the first description and on every later edit, and a body that skipped it is unfinished.

The repo skill `writing-pr-descriptions` does not satisfy this. It checks word count, passive voice, and noun-string length, and it excludes the ASD-STE100 vocabulary rules on purpose, so word choice goes unchecked. Word choice is what reviewers object to. Run both: the repo skill decides what goes in, this pass decides how it reads.

Three things to remove that no count catches: metaphor standing in for a technical claim, abstraction where a concrete value exists, and noun phrases the reader must parse twice. The STE flatness governs sentence mechanics only; the content rules above (no file enumeration, no command lists, substance in template sections) still govern what goes in.
