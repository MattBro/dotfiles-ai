---
description: Create draft PR and run comprehensive self-review with historical feedback, online research, and codebase pattern analysis
allowed-tools: Bash, Read, Grep, Glob, Task, WebSearch, WebFetch
---

# Pre-PR Readiness Check

Create a draft PR and run a comprehensive self-review before requesting reviews.

## 1. Get context

Run this from your feature-branch worktree — code work defaults to a worktree, not the main checkout (see `CLAUDE.md` → Git Workflow → Workspaces).

```bash
REPO=$(basename $(git rev-parse --show-toplevel))
BRANCH=$(git branch --show-current)
echo "Repo: $REPO, Branch: $BRANCH"

git diff --name-only main...HEAD
```

## 2. Create draft PR

Create a draft PR so we have a PR number to reference. If a PR template exists (`.github/pull_request_template.md`), use it. Otherwise use a minimal placeholder body.

Get the PR number for the review.

## 3. Run comprehensive review

Spin up parallel agents to review the changes from multiple angles:

### Agent 1 — Historical feedback analysis

Search past PR review comments for feedback on similar code patterns. Look for:

- Comments on files I've changed before
- Feedback patterns that apply to this type of change (e.g. if this is auth code, find past auth feedback)
- Recurring issues to watch for

```bash
gh api repos/ORG/REPO/pulls/NUMBER/comments  # on my recent PRs
```

### Agent 2 — Online best practices

Search docs and best-practice guides for:

- The libraries/frameworks being used in the changes
- Common pitfalls with the patterns I'm implementing
- Whether my approach aligns with recommended practices

For example:

- Django patterns → Django docs
- React/TypeScript → React docs, TypeScript handbook
- API design → REST best practices
- Auth/OAuth → OAuth specs, security guides

### Agent 3 — Codebase pattern analysis

Search the codebase to verify my changes fit existing patterns:

- How do similar features implement this?
- Are there existing helpers I should be using instead of writing new code?
- Does my naming match conventions in nearby code?
- Am I duplicating something that already exists?

Look at:

- Similar files in the same directory
- How other features handle the same concerns
- Existing utility functions and helpers

### Agent 4 — Adversarial review (Codex)

Run an adversarial review using the `codex` CLI. Goal: a second opinion from a different model that actively tries to poke holes in the change — not validate it.

```bash
codex exec --sandbox read-only --skip-git-repo-check "$(cat <<'EOF'
Act as an adversarial reviewer on the current branch's diff vs main. Your job is to find problems, not validate.

First, read the diff:
  git diff main...HEAD

Then critique it. Focus on:
- Bugs, race conditions, off-by-one errors
- Security issues (injection, auth bypass, secret leakage, unsafe deserialization)
- Incorrect error handling, swallowed exceptions, missing edge cases
- Data integrity risks (migrations, money/float precision, nullability)
- API contract breaks, backwards-incompatible changes
- Performance cliffs (N+1 queries, unbounded loops, large in-memory ops)
- Tests that assert the wrong thing, or that pass without actually exercising the change

For each issue: file:line, what's wrong, why it matters, suggested fix. Be concrete. Skip nitpicks and style — only substantive issues. If the diff looks clean, say so rather than inventing problems.
EOF
)"
```

Capture Codex's output and feed its findings into the compile step.

## 4. Compile review findings

After all agents complete, compile findings into categories:

### Must fix (blocking)

- Security issues
- Bugs that would crash
- Violations of existing patterns

### Should fix (important)

- Code that duplicates existing helpers
- Naming inconsistencies
- Missing error handling

### Consider (nice to have)

- Refactoring opportunities
- Documentation improvements
- Test coverage gaps

## 5. Update PR description

Based on the review, update the draft PR with:

- Proper title (Conventional Commits format, lowercase type)
- Fill out all sections from the PR template
- Any notes for reviewers about tradeoffs

## 6. Run CI checks locally

**Run these BEFORE marking the PR ready** to catch CI failures early.

### Python changes

```bash
ruff check . --fix
ruff format .

# If the project uses mypy-baseline (PostHog), check NEW violations only:
mypy . | mypy-baseline filter
```

If mypy shows new violations, fix them before proceeding.

### Frontend changes

```bash
pnpm --filter=@posthog/frontend lint
pnpm --filter=@posthog/frontend typescript:check
```

(Adjust the `--filter` for the project you're in.)

### Tests

```bash
pytest path/to/test_file.py -v
pnpm --filter=@posthog/frontend jest path/to/test
```

## 7. Final checklist

Before marking ready for review:

- [ ] All "Must fix" items addressed
- [ ] "Should fix" items addressed or noted for reviewers
- [ ] Python lint passes (`ruff check .`)
- [ ] Python types pass (`mypy . | mypy-baseline filter` shows no NEW errors, if applicable)
- [ ] Frontend lint passes (if applicable)
- [ ] Frontend types pass (if applicable)
- [ ] Tests pass locally
- [ ] PR description is complete

When ready:

```bash
gh pr ready NUMBER
```

Or if issues remain, keep as draft and fix first.

## 8. Babysit the PR

After marking the PR ready, run `/babysit-pr` on it to monitor CI, address review comments, and fix any issues that come up.
