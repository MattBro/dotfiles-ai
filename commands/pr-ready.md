---
description: Create draft PR and run comprehensive self-review with historical feedback, online research, and codebase pattern analysis
allowed-tools: Bash, Read, Grep, Glob, Task, WebSearch, WebFetch
---

# Pre-PR Readiness Check

Create a draft PR and run a comprehensive self-review before requesting reviews.

> **In the PostHog monorepo, the repo's own skills supersede parts of this
> command.** Use `writing-pr-descriptions` for the PR body and
> `running-ci-preflight` for step 6. They only load when the session started
> inside the checkout; otherwise read them from
> `~/dev/posthog/.agents/skills/<name>/SKILL.md`.
>
> **One exception: `writing-pr-descriptions` does not supersede the
> `unambiguous-agent-text` pass in step 5.** Run that pass over the body the repo
> skill produces. See step 5 for what it removes.

## 1. Get context

Run this from your feature-branch worktree — code work defaults to a worktree, not the main checkout (see `CLAUDE.md` → Git Workflow → Workspaces).

```bash
REPO=$(basename $(git rev-parse --show-toplevel))
BRANCH=$(git branch --show-current)
echo "Repo: $REPO, Branch: $BRANCH"

git diff --name-only main...HEAD
```

In the PostHog monorepo, resolve the owning team for the changed paths so the
review request goes to whoever owns the code:

```bash
git diff --name-only master...HEAD | hogli owners:resolve --json
```

Use the resolved team for `--reviewer`. Fall back to `PostHog/team-growth` only
when the paths come back unowned.

## 2. Create draft PR with a placeholder body

**Create the draft with a placeholder body, never the finished description.** One line of intent, or the repo's empty `.github/pull_request_template.md` if one exists. Step 5 writes the real body, and step 5 owns the style rules and the required `unambiguous-agent-text` pass.

Writing the finished body here is how this command fails in practice. The PR looks done, so step 5 never runs, and the description ships without the style pass. If you write the body here anyway, you still owe step 5: run it against the published body and edit the PR before you report.

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

### Agent 3 — Design integrity and codebase patterns

Use the strongest available reasoning model for this review. Start from the original request, linked issue, and external specification before reading the implementation narrative. State the intended behavior and invariants in plain terms, then check whether the diff implements that design.

For changes to persisted data, authentication, billing, or external integrations, record:

- each protocol or domain value and its single canonical field;
- every writer and reader, including the consumer and trust boundary;
- why each new field is needed instead of changing an existing field;
- whether the same identity or configuration now exists in two places;
- whether another capability or quota would extend a column family that should move to a dedicated model or structured configuration;
- for temporary duplication, the backfill, writer cutover, reader cutover, deployment order, and pull request that deletes the old representation.

Then search the codebase for helpers, framework-native structure, naming conventions, and comparable implementations. Existing code is evidence about compatibility, not proof that the design is correct. If a repeated pattern conflicts with the original request, external specification, framework structure, or ownership of the value, report the pattern itself as the problem.

Also check whether the change pushes a views file past roughly 800 lines, a function past roughly 80 lines, or a module into serving another protocol or consumer. Those are restructure prompts, not follow-up cleanup notes.

### Agent 4 — Adversarial review

Spawn a read-only Sonnet sub-agent (Agent tool, `model: "sonnet"`, Explore type) whose job is to find problems, not validate. Prompt it with:

> Act as an adversarial reviewer on the current branch's diff vs main. Your job is to find problems, not validate. Read the diff (`git diff main...HEAD`), then read the full context of every modified function. Focus on:
> - Bugs, race conditions, off-by-one errors
> - Security issues (injection, auth bypass, secret leakage, unsafe deserialization)
> - Incorrect error handling, swallowed exceptions, missing edge cases
> - Data integrity risks (migrations, money/float precision, nullability)
> - API contract breaks, backwards-incompatible changes
> - Performance cliffs (N+1 queries, unbounded loops, large in-memory ops)
> - Tests that assert the wrong thing, or that pass without actually exercising the change
>
> For each issue: file:line, what's wrong, why it matters, suggested fix. Be concrete. Skip nitpicks and style. If the diff looks clean, say so rather than inventing problems.
>
> For every test the diff adds, prove it earns its place: revert the code change it covers, run that test, confirm it fails, then restore. Report any test that still passed, since that one asserts nothing about the behaviour it claims to cover.

Feed its findings into the compile step.

## 4. Compile review findings

After all agents complete, compile findings into categories:

### Must fix (blocking)

- Security issues
- Bugs that would crash
- A design that contradicts the original request or external specification
- Duplicate canonical identities without a backfill, writer and reader cutovers, safe deployment order, and linked deletion PR
- New persisted fields with no independent meaning or no named readers and writers
- Another capability or quota column in a growing family whose storage structure has not been corrected
- Use of a scaffold whose protocol, consumer, or trust boundary does not match the change
- Feature work that crosses or increases an over-limit file or function, or adds another protocol or consumer without restructuring first

### Should fix (important)

- Code that duplicates existing helpers
- Naming inconsistencies
- Missing error handling

### Consider (nice to have)

- Refactoring opportunities
- Documentation improvements
- Test coverage gaps

A "Must fix" finding must be fixed in this PR. An accepted non-blocking finding is not resolved by moving it to a lower category: fix it or link an issue or PR with a named owner before the PR can leave draft. If this PR would make more code depend on the problem, it is blocking.

## 4.5. Cold design audit

If the diff touches persisted data, authentication, billing, or an external integration, run one final review with a fresh strongest-available reasoning agent that did not participate in implementation or the earlier review.

**Pass 1, independent design:** give it only the original request, linked issue, applicable external specification, final diff, and full changed files. Do not provide Agent 3's ownership map, the implementation conversation, or the compiled findings. Ask it to derive the canonical holders, trust boundaries, and module boundaries itself, then report any design defects.

**Pass 2, comparison:** after Pass 1 returns, give the same agent the ownership map from Agent 3 plus the compiled findings and resolutions. Ask it to identify disagreements, findings that were incorrectly closed, and deferred problems the diff now depends on.

Both passes must check for duplicate representations, fields without independent meaning, growing capability or quota column families, and scaffolds built for another consumer. Existing code does not settle those questions. Fold every verified finding back into step 4 before updating the PR description.

## 5. Update PR description

Based on the review, update the draft PR with:

- Proper title (Conventional Commits format, lowercase type)
- Any notes for reviewers about tradeoffs
- Every section of `.github/pull_request_template.md` filled out:
  - **Problem** — who it's for, what they need, why this matters
  - **Changes** — what changed, with screenshots for frontend work
  - **How did you test this code** — how the behavior was validated, not the commands run: a manual scenario someone else could reproduce, plus a one-line statement of new/updated test coverage. Never claim a test ran unless it did.
  - **Changelog** — yes/no whether this is changelog-worthy

Follow the "PR description style" rules in `claude/git-workflow.md`. The two that agents miss most:

- **150 words or fewer of prose.** No file-by-file enumeration, no command lists, no implementation diary.
- **One claim, one proof.** State what is true and the single strongest piece of evidence for it. Do not transcribe the verification trail that convinced you; the reviewer has the diff. Further evidence goes in a review comment, or nowhere.

Count the words before you write the body to the PR. If the prose is over 150, cut evidence first, then caveats a reviewer can get from the diff.

### Required final pass: `unambiguous-agent-text`

Run the `unambiguous-agent-text` skill over the finished body before you write it
to the PR. This pass is required, not optional, and it is the last thing you do to
the text.

In the PostHog monorepo `writing-pr-descriptions` does not replace this pass. Its
checks are mechanical: word count, passive voice, noun-string length. Its own
background section states that the ASD-STE100 controlled vocabulary is licensed
and deliberately excluded, so word choice stays unchecked. Word choice is what
reviewers complain about.

Remove these three things, none of which any mechanical check catches:

- **Metaphor in place of a technical claim.** "silently cross a boundary",
  "blast radius", "surface area", "load-bearing". Write what happens instead.
- **Abstraction where a concrete value exists.** "tuned thresholds" is a number
  in a file. Name the number or name the file.
- **Compressed noun phrases the reader must parse twice.** Split them with a
  preposition or a verb.

A sentence can pass every count in that skill and still be unreadable. Reviewers
have asked for this style directly, so treat a body that skipped this pass as
unfinished.

## 6. Run CI checks locally

**Run these BEFORE marking the PR ready** to catch CI failures early.

### PostHog monorepo: preflight first

```bash
hogli ci:preflight --fix
hogli ci:preflight --strict
```

This is the highest-yield check and it replaces most of what follows. It covers
the deterministic CI failures reachable from the diff: formatting, lint, broken
lockfiles, OpenAPI drift, migration leaf conflicts, stale branch. Fix whatever
`--fix` could not auto-remediate, then re-run until `--strict` exits clean.

If `hogli` is not found, see `claude/hogli.md`. Do not skip this step because the
pre-push hook exists; that hook no-ops when `hogli` is off PATH.

Then the checks preflight does not cover:

```bash
hogli test --changed                                  # tests for changed files
mypy . | mypy-baseline filter                         # NEW violations only
pnpm --filter=@posthog/frontend typescript:check      # frontend types
```

If mypy shows new violations, fix them before proceeding.

### Other repos

```bash
ruff check . --fix && ruff format .
pnpm --filter=<pkg> lint
pnpm --filter=<pkg> typescript:check
pytest path/to/test_file.py -v
```

## 7. Final checklist

- [ ] All "Must fix" items addressed
- [ ] "Should fix" items addressed or linked to an issue or PR with a named owner
- [ ] Original request, linked issue, and applicable external specification re-read after the final diff
- [ ] Every new persisted field has one canonical value, named writers and readers, and a reason an existing field cannot hold it
- [ ] Any temporary duplicate representation defines its backfill, writer and reader cutovers, safe deployment order, and linked deletion PR
- [ ] Feature work does not cross or increase an over-limit file or function, or add another protocol or consumer without restructuring first
- [ ] `hogli ci:preflight --strict` exits clean (PostHog monorepo)
- [ ] Reviewer matches `hogli owners:who <changed path>`, not a default team
- [ ] Python lint passes (`ruff check .`)
- [ ] Python types pass (`mypy . | mypy-baseline filter` shows no NEW errors, if applicable)
- [ ] Frontend lint passes (if applicable)
- [ ] Frontend types pass (if applicable)
- [ ] Tests pass locally
- [ ] PR description is complete

### If the diff touches auth or OAuth

- [ ] No internal exception details exposed to clients
- [ ] Redirect URIs validated (no injection)
- [ ] Rate limits appropriate for the endpoint
- [ ] Tokens and secrets not logged

### If the diff touches billing or money

- [ ] Monetary values use a money type or `Decimal`, never float
- [ ] Business logic values verified (pricing, limits)
- [ ] Error paths use `capture_exception`

## 8. Report and stop — never mark ready without an explicit go

**The PR stays a draft until Matt explicitly says to mark it ready.** Never run `gh pr ready` as part of this command, even if every checklist item passes. A green checklist means "ready for Matt's go", not "ready for review".

When the flow completes, notify Matt that it's done:

1. Send a push notification (PushNotification tool) if available — short: repo, PR title, and whether the checklist is green or has open findings.
2. In the session, report: the PR link (title + URL, never a bare number), the compiled findings and what was fixed vs noted, the checklist state, and the explicit line "Draft — say the word to mark it ready."

Only after Matt gives the go: `gh pr ready NUMBER`, then run `/babysit-pr` on it to monitor CI, address review comments, and fix any issues that come up.
