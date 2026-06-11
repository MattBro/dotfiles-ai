---
description: Review a PR and generate a list of specific, actionable comments with file paths, line numbers, problems, and suggestions
allowed-tools: Bash, Read, Grep, Glob, Agent, WebSearch, WebFetch
---

# PR Review Tool

Review a PR and produce a list of comments ready to post. Each comment includes: file, line number, problem, and suggestion (with tradeoffs when relevant).

## Input

The user provides a PR number, URL, or branch name. If nothing is provided, use the current branch's PR.

## 1. Get PR context

```bash
PR_NUMBER=$(gh pr view --json number -q .number 2>/dev/null)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Reviewing PR #$PR_NUMBER in $REPO"
```

Fetch the PR details:

```bash
# PR metadata — capture headRefName and headRefOid for file reads below
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName,headRefOid,files

# Full diff
gh pr diff $PR_NUMBER

# Comments already posted (avoid duplicating existing feedback)
gh api repos/$REPO/pulls/$PR_NUMBER/comments --jq '.[] | {path: .path, line: .line, body: .body, user: .user.login}'
gh api repos/$REPO/pulls/$PR_NUMBER/reviews --jq '.[] | {state: .state, body: .body, user: .user.login}'
```

## 2. Understand the change

Before reviewing line-by-line, understand the big picture:

- What problem is this PR solving?
- What approach did the author take?
- What files changed and why?

Read every changed file in full (not just the diff) to understand the surrounding context. Also read any test files added or modified.

### How to read PR files — DO NOT CLONE

**Never `git clone` the repo to a temp dir.** Cloning a large monorepo burns several GB and minutes for a read-only review. Pick the cheapest option that works:

1. **Repo is already checked out locally** (e.g. `~/dev/<repo-name>` exists): `cd` there, run `git fetch origin <headRefName>`, then read files at the PR's HEAD with `git show FETCH_HEAD:path/to/file`. Do not modify the working tree — no `git checkout`, no `git checkout -- path`. If you must materialize files, use `git worktree add` against `FETCH_HEAD`, never a fresh clone.
2. **Repo is not local**: read individual files via the GitHub contents API at the PR's HEAD SHA. Always quote URLs that contain `?` so zsh doesn't glob:
   ```bash
   gh api "repos/$REPO/contents/path/to/file.py?ref=$HEAD_SHA" --jq '.content' | base64 -d
   ```
3. **Avoid background bash for setup** (`run_in_background`, `gh pr checkout` in the background). Setup commands should be foreground and fast — if they hang, diagnose immediately.

If you accidentally created a clone or worktree, `rm -rf` it (or `git worktree remove`) before finishing the review.

## 3. Review the code (parallel agents)

Spin up 6 agents in parallel, each reviewing the diff from a different angle. Each agent should read the full changed files (not just the diff hunks) and cross-reference with existing code in the repo.

### Agent 1 — Correctness and safety

Focus exclusively on bugs, logic errors, and safety:

- **Logic errors** — off-by-ones, wrong comparisons, inverted conditions, missing early returns
- **Null / undefined handling** — anything that can be null/undefined but isn't checked
- **Race conditions** — async code that assumes ordering, missing awaits
- **Security** — SQL injection, XSS, command injection, auth bypass, secrets in code
- **Data integrity** — possible corruption, missing transactions, partial updates
- **Breaking changes** — API contract changes, removed fields, changed behavior
- **Error handling** — swallowed errors, missing catch blocks, unhelpful messages
- **Edge cases** — empty arrays, zero values, negative numbers, very large inputs

**Critical: before flagging a pattern as an issue, search the codebase for similar patterns.** If the same pattern is used elsewhere, it's probably intentional. Check 2-3 similar files before flagging.

For each issue, output:

```
FILE: <path>
LINE: <number or range>
SEVERITY: critical | important
PROBLEM: <what's wrong, one sentence>
SUGGESTION: <how to fix it, with code snippet if helpful>
CODEBASE_CHECK: <did you verify this pattern against similar code? what did you find?>
```

### Agent 2 — Tests and coverage

Focus on whether the changes are properly tested:

- **Missing tests** — new code paths without coverage
- **Weak assertions** — tests that pass but don't actually verify the right thing
- **Missing edge cases** — happy path tested, error paths aren't
- **Test quality** — brittle, flaky-prone, or implementation-detail tests
- **Integration gaps** — unit tests exist but integration between components isn't tested
- **Regression risk** — changed behavior that existing tests don't cover

Search the codebase for how similar features are tested. Use those as the bar for what's expected.

For each issue:

```
FILE: <path to where test should be, or existing test file>
LINE: <line of code that needs testing>
SEVERITY: important | suggestion
PROBLEM: <what's missing>
SUGGESTION: <specific test case to add, with a rough code sketch>
```

### Agent 3 — Patterns, conventions, design

Focus on whether the code fits the codebase:

- **Existing helpers** — is the author reimplementing something that exists? Search for it.
- **Naming** — does naming match conventions in surrounding code?
- **Architecture** — does this follow the project's established patterns? Check `AGENTS.md`, `CLAUDE.md`, `conventions.md`.
- **Duplication** — is code being copy-pasted that should be extracted?
- **API design** — fields properly typed? Read-only where needed? Serializers annotated?
- **State management** — frontend: Kea vs hooks? Backend: proper queryset filtering?
- **Type safety** — missing type hints, overly broad types, unsafe casts
- **Performance** — N+1 queries, unnecessary re-renders, missing indexes for new queries

**Check existing patterns first.** Read 2-3 similar files before flagging convention issues.

```
FILE: <path>
LINE: <number or range>
SEVERITY: important | suggestion
PROBLEM: <what doesn't fit>
SUGGESTION: <what to do instead, referencing the existing pattern and where it lives>
```

### Agent 4 — Adversarial review (Codex), best-effort, run in background

Run an adversarial review using the `codex` CLI. The goal is a second opinion from a different model that actively tries to poke holes in the change.

**Treat this step as best-effort.** Codex typically takes 3-8 minutes — don't block the other agents on it. Kick it off in parallel with the other agents using `run_in_background`, with a hard timeout cap of 600000 (10 minutes), and continue compiling the review when the others return. If Codex hasn't produced output by then, ship the review without it and mention in the summary that Codex was skipped. Do **not** spin / poll / sleep waiting for it.

```bash
# run_in_background: true, timeout: 600000
codex exec --sandbox read-only --skip-git-repo-check "$(cat <<EOF
Act as an adversarial reviewer on PR #$PR_NUMBER in $REPO. Your job is to find problems, not validate.

First, read the diff:
  gh pr diff $PR_NUMBER

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
)" || echo "[codex skipped]"
```

If Codex is missing (`command not found`), permission-denied, or the call gets interrupted, do not retry — note "codex skipped" and proceed.

When Codex output arrives (or doesn't), fold whatever you have into the compile step.

### Agent 5 — Overly-defensive code

Flag defensive code that masks bugs instead of failing fast:

- Added `?.`, `|| fallback`, `.get(x, default)`, try/swallow, or null guards on a value the contract says is non-null
- Catch blocks that log-and-continue where the caller can't proceed correctly anyway
- Defaults that paper over a missing required value

Masking turns a clean fail-fast into a cryptic downstream error. For each candidate, ask: if this errors, does the surrounding context make the Sentry/stack trace easy to understand — or would failing fast at the boundary give a clearer report? **Only flag where the contract implies non-null** — check the type signatures and callers before claiming the guard is unnecessary.

```
FILE: <path>
LINE: <number or range>
SEVERITY: important | suggestion
PROBLEM: <which guard masks what, and why the contract says it can't be null>
SUGGESTION: <fail fast instead — what to remove or assert, and where the real boundary check belongs>
```

### Agent 6 — YAGNI / simplification

Review for YAGNI (DHH + Fowler). A presumptive feature is code supporting something nothing uses yet — weigh the cost of building and carrying it:

- Config options, parameters, or branches with exactly one caller/value
- Abstractions (base classes, registries, plugin points) with a single implementation
- "Expand later" scaffolding — code added speculatively probably isn't needed; the move is willingness to delete
- Dead code paths the diff makes unreachable

Skip refactoring suggestions, tests, and zero-complexity additions. Report what to delete or simplify:

```
FILE: <path>
LINE: <number or range>
SEVERITY: suggestion
PROBLEM: <what's speculative/unused and what it costs to carry>
SUGGESTION: <what to delete or inline, and what the simpler version looks like>
```

## 4. Compile and deduplicate

After all agents return, compile findings into a single list. Remove duplicates (different agents may flag the same issue).

Sort by priority:

1. **Critical** — bugs, security issues, data corruption risks
2. **Important** — missing tests, convention violations, wrong patterns
3. **Suggestions** — nice-to-haves, refactoring ideas, minor improvements

For each comment, verify:

- The file path is correct (matches the PR diff)
- The line number is accurate (check against the actual file content)
- The problem is real (not a false positive from misunderstanding context)
- The suggestion is actionable (not vague "consider improving")

**Remove any issue where the codebase check found the same pattern used elsewhere**, unless you can articulate why it's specifically wrong in this context.

## 4.5. Verification gate (anti-hallucination)

**Subagents will confidently invent code that doesn't exist** — claims like "the file uses a negative-list `kind !== 'anthropic'`" when the file actually uses a helper, or "this branch returns a random sibling field" when tracing the loop shows it returns the correct value. The compile step's soft "verify the problem is real" check is not enough. Every finding must pass this gate before it ships:

For each comment, do all of the following yourself in the main thread (do not delegate):

1. **Quote the actual code.** Open the cited file at the PR's HEAD (`git show FETCH_HEAD:path` or `gh api .../contents/...?ref=$HEAD_SHA`) and copy the lines the comment is about into your scratch reasoning. If the quote doesn't contain the construct the comment claims is there, drop the comment. No exceptions.
2. **For control-flow claims, trace one concrete input.** "This returns wrong message for array `detail`" → walk through the code with `{detail: ['msg']}` and verify the bad branch is actually reached. If tracing shows the code handles it, drop the comment.
3. **For "missing X" claims, prove the absence.** Don't trust the subagent. `grep -r 'X'` the relevant directory and confirm. If a test file or helper exists that the subagent missed, drop the comment.
4. **For "duplicated with Y" claims, diff Y.** Open both sites and confirm they're actually duplicate. Subagents will call near-identical-looking code "duplicated verbatim" when it differs in the field that matters.

When in doubt, drop. Posting a wrong comment costs the author trust, the reviewer credibility, and the next reviewer's signal-to-noise. A review of 3 verified comments beats a review of 8 with 2 hallucinations.

After this gate, what remains is the actual review. Pass it through the audit step before de-AI.

## 4.6. Audit-the-feedback agent

Spawn one fresh agent (general-purpose) whose only job is to try to break the surviving findings. The orchestrator's verification gate catches obvious hallucinations; this step catches the subtler ones — wrong line numbers, fix that won't compile, claim that's true in isolation but contradicted by surrounding code, severity mismatch.

The agent must NOT have seen the findings produced — it should arrive cold and form its own opinion.

Prompt the audit agent with:

- The PR number and HEAD SHA
- The full surviving finding list (one block per finding: file path, line, claim, suggested fix, severity)
- Instructions to (a) re-read each cited file at HEAD, (b) check whether the claim still holds, (c) verify the suggested fix actually solves the claim and doesn't break callers, (d) flag any finding it cannot independently confirm
- Output format: per finding, one of `CONFIRMED`, `WRONG: <reason>`, or `UNCERTAIN: <what would resolve it>`

Treat `WRONG` as a drop. Treat `UNCERTAIN` as a downgrade — drop if it can't be resolved with one more inline read; otherwise keep with reduced confidence.

This agent is cheap relative to the cost of posting a wrong finding. Always run it; do not skip even when only one finding survived the gate.

## 5. De-AI the comments

This is critical. Each comment must sound like it was written by a human developer, not an AI.

For each comment, scrub for:

### Banned phrases (rewrite if found)

- "Great catch" / "Good point" / any compliment openers
- "I noticed that…" / "I'd suggest…" / "I think we should…"
- "This ensures that…" / "This approach…" / "This implementation…"
- "It's worth noting…" / "It might be worth…"
- "For better/improved…" / "For enhanced…"
- "Consider leveraging…" / "We could leverage…"
- "Robust" / "comprehensive" / "streamline" / "leverage" / "facilitate"
- "Potential issue" / "potential concern" — just say what the issue is
- "Best practice" / "industry standard"
- "Moving forward" / "going forward"
- "In terms of" / "with respect to"
- "It would be beneficial to…"
- Any sentence starting with "Additionally," / "Furthermore," / "Moreover,"
- "LGTM" followed by suggestions (pick one — either it looks good or it doesn't)

### Banned punctuation/formatting

- Em dashes (use hyphens or restructure the sentence)
- Excessive exclamation marks
- Bullet points within a single comment (just write a sentence or two)

### Style rules

- Lead with the problem, not preamble
- One to three sentences max per comment
- State facts, don't hedge ("this will crash" not "this could potentially cause issues")
- If you're suggesting something, just suggest it directly
- Use the same tone as: "This returns null when `user` is missing — needs a guard. See `similar_file.py:42` for the pattern."

### Internal review pass

Read each comment aloud mentally. If it sounds like a ChatGPT response, rewrite it. If a coworker would roll their eyes reading it, rewrite it. Goal: terse, direct, helpful.

## 6. Output format

Present the final review as a numbered list. Group by file when multiple comments hit the same file.

**Always include the full PR URL in the header so it's clickable.** Never reference the PR by number alone without the link right next to it.

```
## Review: [PR #NUMBER — "title"](https://github.com/OWNER/REPO/pull/NUMBER)

### Critical

1. **`path/to/file.py:42`** — `user` can be None here but isn't checked. Add a guard before accessing `.email`. (Same pattern in `other_file.py:88` uses `if not user: return`.)

2. **`path/to/file.py:107-112`** — This query runs inside a loop — will be an N+1. Pull the queryset outside and filter in memory, or use `prefetch_related`.

### Important

3. **`path/to/file.py:55`** — Missing test for the error path when the API returns 429. The happy path is covered in `test_file.py:30` but rate limiting isn't.

4. **`path/to/component.tsx:23`** — Business logic in the component — this repo puts that in Kea logics. See `similarLogic.ts` for the pattern.

### Suggestions

5. **`path/to/file.py:90`** — `calculate_discount` already exists in `utils/pricing.py:15`. Use that instead of reimplementing.
```

End with a single line containing the clickable PR link again so it's easy to jump to:

```
PR: https://github.com/OWNER/REPO/pull/NUMBER
```

Then ask if I want to:

- Post any of them as PR review comments (using `gh api`)
- Adjust severity or wording on any
- Drop any that seem off

**Never post comments to the PR without explicit approval.** Always present them first.

## 7. Posting comments (after approval)

When I say "post the comments" (with or without approving), post each one as a **separate inline review comment on the exact line it targets**. Do NOT post a single combined comment in the PR body — reviewers can't click through to the line, and it doesn't thread with future replies.

Use a single review API call that bundles all inline comments. **Do NOT use `--raw-field 'comments=[...]'`** — `gh` stringifies it and the API rejects it as "not an array". Always pass the full payload via `--input <json-file>` instead:

```bash
HEAD_SHA=$(gh api repos/$REPO/pulls/$PR_NUMBER --jq .head.sha)

# Write the review payload to a JSON file (use the Write tool — clean, no quoting hell).
# event: "APPROVE" | "REQUEST_CHANGES" | "COMMENT"
# /tmp/pr-review.json:
#   {
#     "commit_id": "<HEAD_SHA>",
#     "event": "APPROVE",
#     "body": "<overall review body, optional>",
#     "comments": [
#       {"path": "path/to/file.py", "line": 42, "side": "RIGHT", "body": "comment text"},
#       {"path": "path/to/file.py", "line": 107, "side": "RIGHT", "body": "comment text"}
#     ]
#   }

gh api repos/$REPO/pulls/$PR_NUMBER/reviews --method POST --input /tmp/pr-review.json
```

Rules:

- One comment per line — never concatenate multiple issues into one comment body.
- Use `line` (the line in the file) with `side: "RIGHT"` for normal right-side-of-diff comments. For multi-line ranges use `start_line` + `line`.
- The `line` must be part of the PR diff — if it's not, GitHub rejects it. When targeting code that isn't in the diff, pick the nearest diff line and reference the actual target in the body.
- If posting a single comment without a review wrapper, use `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments` instead — but prefer the review endpoint so all comments land together.
- When approving with comments, use `event: "APPROVE"`. When blocking, `"REQUEST_CHANGES"`. For neutral, `"COMMENT"`.
- Clean up `/tmp/pr-review.json` after a successful post.
