# Git Workflow

## Workspaces — default to git worktrees

**Default to a git worktree for any task that creates or modifies code, unless told otherwise.** Don't do the work directly in the main checkout (keep it clean for parallel tasks), and never make a fresh full clone of a large repo — worktrees share one `.git`, whereas a second clone of a monorepo wastes tens of GiB.

```bash
cd "$HOME/dev/<main-repo>"
git worktree add ../<repo>-<short-task> -b <branch>   # new branch
git worktree add ../<repo>-<short-task> <existing>     # existing branch / PR
```

- One worktree per branch/PR/task. This is also what lets parallel work (e.g. `/babysit-prs`) run without several jobs fighting over a single checkout.
- Tear it down when the branch is merged/closed: `git worktree remove <path>` (never `rm -rf`), then `git worktree prune`. Removing a worktree keeps the branch ref, so nothing committed is lost.
- **Exceptions — work in place instead:** the user says so; a trivial read-only or single-file change on the current branch; or e2e/full-stack testing, which belongs in a sandbox (see PostHog Stack → Sandboxes).

## Pre-commit checks

- **Always run linting before committing** in repos with lint configs:
  - JS/TS monorepos: `pnpm run lint` (auto-fix with `pnpm run lint --fix`)
  - Python: `ruff check . --fix && ruff format .`
- Fix errors before committing — prevents CI failures.

## Flox environment

If git pre-commit hooks fail with `command not found` errors (e.g. `pnpm: command not found`), use flox to run git commands:

```bash
flox activate -- bash -c "git commit -m 'message'"
```

This makes development dependencies (pnpm, etc.) available to the hook.

## Branch naming

PostHog conventions (check current PRs for the latest patterns):

- `username/description` — most common (e.g. `matt/fix-login-bug`)
- `feat/description` — features
- `fix/description` — fixes
- `refactor/description` — refactors
- `chore/description` — maintenance

## Merging PRs and auto-merge

- **Never arm auto-merge (or merge) without checking with me first.** Before asking, sweep the PR for unaddressed review comments — human AND bot (greptile, veria) — and address or answer them. Then tell me what's outstanding (or that nothing is) and wait for my go.
- A prior "ready to merge" covers the PRs it was said about, not later re-arms after new commits or new comments land.

## Git push

- **Never force push unless explicitly asked.**
- Always try `git push` first.
- Only use `git push --force-with-lease` when the user requests it.

## Commits

- **Never amend commits.** Make separate commits instead.
  - Amending requires force pushing.
  - Separate commits show the evolution of changes.
  - Reviewers can see the progression.

Example: instead of amending to add a refactor, create a new commit:

- `fix: use line item periods for invoices`
- `refactor: extract _get_billing_period helper`

## Pull requests

- **Never post PR comments without being asked.**
- **Always create PRs via the `/pr-ready` slash command** — never run `gh pr create` directly. `/pr-ready` handles draft status, reviewer assignment, PR template, and pre-flight self-review.
- For non-creation PR operations, use `gh` CLI:
  - View: `gh pr view <number>` or `gh pr view <url>`
  - List: `gh pr list`
  - Checks: `gh pr checks <number>`
  - Diff: `gh pr diff <number>`
  - Checkout: `gh pr checkout <number>`
  - Add reviewer: `gh pr edit <number> --add-reviewer <username>`
  - Comment: `gh pr comment <number> --body "comment text"`
  - Review: `gh pr review <number> --approve` / `--request-changes` / `--comment`

### PR title — Conventional Commits (lowercase type)

- `feat: Description` — new feature
- `fix: Description` — bug fix
- `refactor: Description` — neither feature nor fix
- `perf: Description` — performance improvement
- `test: Description` — tests
- `docs: Description` — docs only
- `style: Description` — formatting / whitespace
- `build: Description` — build system / external deps
- `ci: Description` — CI config
- `chore: Description` — other non-src/test changes
- `revert: Description` — reverts a previous commit

**Type must be lowercase.** `refactor:` not `Refactor:`.

### PR template

Always fill out `.github/pull_request_template.md`:

- **Problem** — who it's for, what they need, why this matters
- **Changes** — what changed (screenshots for frontend changes)
- **How did you test this code** — automated tests AND manual testing steps
- **Changelog** — yes/no whether this is changelog-worthy

### Reviewers

If addressing a specific review comment, add that person as a reviewer.

## Pre-PR checklist

Always run these before opening a PR:

### Python

```bash
pytest path/to/test_file.py -v         # tests for changed files
mypy path/to/changed_file.py            # type check
python -c "from module.path import thing"  # import validation
```

### Frontend (large monorepos)

```bash
pnpm run lint
pnpm run typescript:check
```

### JS SDKs

```bash
pnpm run lint
pnpm test
```

### Auth / OAuth code — extra checklist

- [ ] No internal exception details exposed to clients
- [ ] Redirect URIs validated (no injection)
- [ ] Rate limits appropriate for endpoint
- [ ] Tokens / secrets not logged

### Billing / monetary code — extra checklist

- [ ] Monetary values use a money type or `Decimal` (never float)
- [ ] Business logic values verified (pricing, limits, etc.)
- [ ] Error paths use `capture_exception`
