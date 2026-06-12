Babysit a single PR — fix CI issues, address review comments. Bias strongly toward fixing. Escalation is a last resort reserved for genuine design/product decisions only the user can make — never for "this might be tricky" or "security-sensitive" or "I'm not 100% sure". Err on the side of making the change and flagging what you did so the user can review a diff instead of answering a question.

Arguments: $ARGUMENTS should be a PR URL (e.g. `https://github.com/OWNER/REPO/pull/12345`) or `repo#number` (e.g. `OWNER/REPO#12345`).

## Workspace

Do the work in a dedicated git worktree for the PR branch — never check the branch out in the main repo (see `CLAUDE.md` → Git Workflow → Workspaces). This keeps the main checkout clean and is what lets `/babysit-prs` babysit several PRs in parallel without collisions.

```bash
cd "$HOME/dev/<main-repo>"
git fetch origin <headRefName>
git worktree add ../<repo>-pr-<number> <headRefName>
cd ../<repo>-pr-<number>
```

Remove it when the PR is done: `git worktree remove ../<repo>-pr-<number>` then `git worktree prune`.

## Prior-session context (best-effort, before acting)

Past Claude sessions often hold the *why* behind this PR — decisions, abandoned approaches, reviewer subtext — that the PR description doesn't. Pull that in as a distilled brief; do NOT resume old sessions (their context is mostly stale tool output — context rot).

1. Find the best-matching prior sessions for this PR:
   ```bash
   python3 ~/.claude/skills/pr-status-check/scripts/pr-status-check.py --match-only "<owner/repo#number>"
   ```
2. Pick at most the top 1-2 candidates worth reading: `branch-exact` always; otherwise only `branch-name`+`url` candidates whose title plausibly relates to the PR. Skip candidates that are clearly generic status sweeps.
3. Extract the conversation (tool noise already stripped, tail-biased):
   ```bash
   python3 ~/.claude/skills/pr-status-check/scripts/extract-transcript.py <transcript-path-or-sid> --max-chars 40000
   ```
4. Distill into a short context brief (≤400 tokens): decisions made and why, constraints, approaches tried and abandoned, anything promised to reviewers, work left in flight. Use the brief when judging review comments and writing fixes/replies.
5. **If a prior session owns this PR, resume it instead of working fresh.** When the extract shows the matched session is mid-flight on this exact PR (armed /loop, an in-progress babysit, or a recent `branch-exact` session that was actively executing on it), do NOT double-work it from a fresh context. Resume that conversation headless — one turn with its full context:
   ```bash
   cd <session dir> && claude -p --resume <session-id> --dangerously-skip-permissions \
     "Continue babysitting <PR url>. New since your last turn: <new comments / CI state / what triggered this>. Pick up from your prior context and report what you did."
   ```
   Relay its output as your own findings. This is the one case where resuming beats fresh+brief: the session is mid-execution and owns state (loops, worktrees, promises to reviewers). If the headless resume errors, fall back to fresh + brief.
   Note: a spawned subagent cannot inherit another session's context — headless `claude -p --resume` via Bash is the only way to continue a prior conversation programmatically.

Entirely best-effort — if the matcher finds nothing or anything errors, proceed without it.

## Notification setup

Notifications use a Slack webhook from your environment. Set this once in your shell rc:

```bash
export SLACK_BABYSITTER_WEBHOOK="https://hooks.slack.com/services/..."
```

If unset, skip the Slack step but still send the macOS notification on escalations.

Send Slack notifications with:

```bash
if [ -n "$SLACK_BABYSITTER_WEBHOOK" ]; then
  curl -s -X POST -H 'Content-type: application/json' \
    --data '{"text":"<message>"}' \
    "$SLACK_BABYSITTER_WEBHOOK"
fi
```

Trigger macOS notification for escalations:

```bash
osascript -e 'display notification "<brief summary>" with title "PR Babysitter" sound name "default"'
```

Detect your GitHub login once at the top of the run and reuse it everywhere a literal username is needed:

```bash
GH_USER=$(gh api user --jq .login)
```

## Steps

1. Parse the PR from `$ARGUMENTS`. Accept either:
   - A full URL: `https://github.com/OWNER/REPO/pull/12345`
   - A `repo#number`: `OWNER/REPO#12345`

   Extract the repo (`owner/name`) and PR number.

2. Check CI and review comments:

   ### CI status

   - Run `gh pr checks <number> --repo <repo> --json name,state,bucket,link`
   - Classify failures:
     - **Infra flake** (docker timeout, runner issues, network errors, Shadow story selection, Build Docker image): **Immediately** rerun with `gh run rerun <run_id> --repo <repo> --failed`. Do NOT wait or just note it — rerun it right away on the first pass.
     - **Real failure** (test failures, lint errors, type errors): In the PR's worktree (see Workspace above), read the failing code and fix it. Commit and push the fix.
   - If CI is still `in_progress`, skip — don't act on it yet. But if there are already-failed jobs alongside `in_progress` ones, rerun the failed jobs immediately.

   ### Merge conflicts

   - Run `gh pr view <number> --repo <repo> --json mergeable,mergeStateStatus`
   - If `mergeStateStatus` is `DIRTY` or `mergeable` is `CONFLICTING`:
     - Use the PR's worktree (see Workspace above)
     - Fetch and rebase onto the base branch (usually `master`): `git fetch origin master && git rebase origin/master`
     - Resolve conflicts, keeping both sides' intent (read surrounding code to understand what changed on master)
     - Run tests if possible to verify the resolution
     - Commit and push (`git push --force-with-lease`)
     - Include in notification: "Resolved merge conflict with master (rebased)"

   ### Review comments

   - Fetch reviews: `gh api repos/<owner>/<repo>/pulls/<number>/reviews`
   - Fetch review comments: `gh api repos/<owner>/<repo>/pulls/<number>/comments`
   - Look at ALL comments (both human and bot reviewers like greptile-apps, graphite-app) that `@$GH_USER` hasn't replied to yet

3. For each unresolved comment, use the **multi-agent deliberation process** described below.

## Multi-agent deliberation process

For each unresolved review comment, use this process to decide what to do:

### Phase 1 — Analysis (parallel agents)

Spawn 3 agents in parallel, each analyzing the same comment independently. Each agent should:

- Read the comment and surrounding code context
- Identify what the reviewer is asking for
- Propose a concrete plan of action
- Rate confidence (high / medium / low)

Framings:

- **Agent A (pragmatist)**: "What's the simplest change that addresses this comment?"
- **Agent B (reviewer perspective)**: "Put yourself in the reviewer's shoes. What are they really concerned about? What would satisfy them? Are there deeper issues they're hinting at that your fix should also address?"
- **Agent C (quality critic)**: "Assume we ARE going to fix this. What's the strongest version of the fix? What would make a naive fix insufficient, and what additional assertions / guards / edge cases should be included so the fix actually does what the reviewer wants?"

Note: Agent C's job is to *strengthen* the fix, not to veto it. It must propose a fix, not an escalation.

### Phase 2 — Synthesize and fix

Default behavior: **fix it.** Build the plan by taking the union of the 3 proposals:

- Start with Agent A's simplest change as the base
- Layer in Agent B's deeper concerns if they identify a better framing
- Incorporate Agent C's additional assertions, guards, or edge cases so the fix is strong, not naive

Examples of how this plays out:

- 2 agents say "add a test", 1 says "the test needs to also assert X or it's misleading" → write the test WITH assertion X. Do not escalate.
- 2 agents say "extract helper", 1 says "but watch out for call site Y" → extract the helper AND handle call site Y.
- Agents propose different implementations → pick the one that addresses the deepest concern, implement it.

### When to actually escalate

Escalation bar is HIGH. Only escalate when:

- The comment asks a **product/design question** where the answer changes what the feature does (not how it's implemented). Example: "should this be self-serve or require approval?" — that's a product call.
- The fix would require **reverting or significantly changing a deliberate decision** the user made in this PR (not just "the reviewer prefers a different pattern").
- You genuinely **cannot understand what the reviewer is asking** after reading the comment and surrounding context, and guessing wrong would waste significant work.

Do NOT escalate for:

- "This is security-sensitive" — write a careful fix with strong assertions and flag your reasoning in the Slack summary. The user can review the diff.
- "A naive fix could be insufficient" — then write a non-naive fix. That's the whole point of having 3 agents.
- "I'm not 100% sure which approach is better" — pick one, commit it, note the alternative in the Slack summary.
- "The reviewer might have meant X or Y" — pick the more thorough interpretation and do that.

### Trivial fixes

Skip deliberation entirely — just fix them directly:

- Formatting, import ordering, typos, obvious renames
- Adding a missing test for a new code path (default: just write it)
- Extracting a helper the reviewer asked for
- Adding type hints, docstrings, error handling the reviewer requested

## Notification format

After processing the PR, send a Slack notification with what happened.

**Every comment reference MUST include a direct GitHub URL (`html_url`)** so the user can click through. Fetch `html_url` from the comments API when gathering comments. Never just link to the PR — link to the specific comment.

For actions taken:

```
PR Babysitter

owner/repo#12345 — feat: add thing
- Reran 3 flaky CI jobs
- Fixed lint error (import ordering) — <link to commit on GitHub>
- Addressed @reviewer comment about helper function
  <direct link to the specific comment, e.g. https://github.com/OWNER/REPO/pull/12345#discussion_r1234567>
  Suggested reply: "Extracted into _resolve_resource_response helper."
```

When you DO fix something non-trivial or security-sensitive, tell the user what you did and what's worth double-checking, so they can review a concrete diff instead of answering a question:

```
PR Babysitter

owner/repo#12345 — feat: add thing
- Added test for non-Stripe partner consent skip (commit abc123)
  Included assertion that PENDING_AUTH_CACHE has no entry after call — naive test without this would give false security assurance since it's a consent-bypass flag
  Worth a look: <commit link>
```

For escalations (rare — only for design/product decisions, also trigger macOS notification):

```
PR Babysitter — needs your input

owner/repo#12345 — feat: add thing
- @reviewer asked: "Should self-serve users be allowed to do this, or require approval?"
  <direct link to the specific comment>
  This is a product decision — affects what the feature does, not how it's implemented
```

If nothing needs attention (CI green, no unresolved comments), stay silent — don't send a notification.

## Loop until done

After each pass, check if the PR is fully healthy:

- CI: all checks passing (not `in_progress`, not failing)
- Comments: no unresolved review comments from humans or bots that `@$GH_USER` hasn't replied to
- Merge conflicts: `mergeStateStatus` is not `DIRTY`

If any of these are not met, use `/loop 5m` to keep checking. Stop looping when all three are green, or when you've escalated something that needs the user's input (don't keep looping on something you can't fix).

If CI is `in_progress`, loop to wait for it to finish — don't treat it as done.

### When running as a subagent (no /loop available)

If you are a spawned subagent rather than the main session: ending your turn to "wait for a notification/monitor/sleep event" TERMINATES you — the event never arrives. Never end your turn to wait. Poll in a FOREGROUND bash loop instead, in a single Bash call with a generous timeout, and repeat the call if it times out:

```bash
until gh pr checks <number> --repo <repo> --json bucket --jq 'all(.[]; .bucket != "pending")' | grep -q true; do sleep 60; done
```

Only end your turn when the PR is fully healthy or you have a genuine escalation, and make your final message the complete report.

## Important

- Always work in the PR branch's worktree, never the main checkout (this also enables parallel `/babysit-prs`)
- Follow `CLAUDE.md` commit and code style guidelines (no unnecessary comments, conventional commits, etc.)
- For **bot reviewer comments**: Post replies directly to GitHub using `gh api repos/<owner>/<repo>/pulls/<number>/comments/<comment_id>/replies`. Keep replies short — just say what was done or why the suggestion was skipped. No need to include these in the Slack notification unless the action is non-obvious.
- For **human reviewer comments**:
  - **Straightforward / simple** (you made a clear fix like "added X", "fixed import", "switched to Y"): Post a short reply directly to GitHub. One sentence max — just state what was done.
  - **Nuanced / ambiguous** (design questions, tradeoffs, questions about behavior, anything where the reply requires judgement or explanation): NEVER post directly. Draft a suggested reply and include it in the Slack notification for the user to review and post manually.
- When drafting suggested replies, keep them short and human — see `CLAUDE.md` "PR Comment Suggestions" section if present.
- When a reply references a commit (e.g. "fixed in abc123", "done in the latest commit"), link to that commit on GitHub. Format: `[abc123](https://github.com/<owner>/<repo>/pull/<number>/commits/<full_sha>)` — full SHA in the URL, short SHA in the link text. Applies to both directly-posted replies and suggested replies in the Slack notification.
- After drafting each suggested reply, spawn a separate agent to review it for AI-sounding language. The reviewer agent should:
  - Flag phrases that sound like AI ("Great catch!", "I've updated the code to...", "This ensures that...", "As suggested, I've...", "I appreciate the feedback")
  - **Never use em dashes** in replies. Use hyphens (-) or restructure the sentence
  - Flag unnecessary hedging, over-explaining, or restating the reviewer's comment back at them
  - Check that it sounds like a real dev dashing off a quick reply, not a polished AI response
  - Rewrite if needed — aim for casual, terse, matter-of-fact tone
  - Examples of good replies: "Done.", "Switched to subscription metadata.", "Returns 409 now if there are unpaid invoices.", "Keeping them separate — test names document the scenarios."
  - Examples of bad replies: "Great suggestion! I've refactored the code to extract a helper function, which improves maintainability.", "You're absolutely right — I've updated the implementation to use direct key access for better fail-fast behavior."
- Never force push, except `--force-with-lease` after resolving merge conflicts via rebase
- Make separate commits for each fix (don't bundle unrelated fixes)
- Run lint / type checks before committing fixes (per `CLAUDE.md` pre-commit checks)
- When in doubt, **fix it carefully and flag it** — a noisy escalation is expensive (it trains the user to ignore notifications and defeats the point of the babysitter); a thoughtful fix the user can review in 30s is cheap. The review comment is the reviewer asking for a change — default to making that change.
- Trivial fixes (formatting, imports, typos, obvious renames) skip deliberation — just do them
- For security-sensitive fixes: write the strongest version of the fix, include the reasoning in the Slack summary so the user knows what to look at in the diff. Do NOT bounce it back as an escalation.
