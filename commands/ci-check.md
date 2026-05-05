---
description: Analyze failed CI checks on a PR, determine if failures are flaky/infra, need a master merge, or require code fixes, and take the appropriate action
allowed-tools: Bash, Read, Grep, Glob, Task, WebFetch
---

# CI Check Analyzer

Analyze failed CI checks on a PR and determine the right action: rerun flaky jobs, merge master, or fix code.

## 1. Identify the PR

```bash
PR_NUMBER=$(gh pr view --json number -q .number 2>/dev/null)
if [ -z "$PR_NUMBER" ]; then
  echo "No PR found for current branch"
  exit 1
fi
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "PR #$PR_NUMBER in $REPO"
```

If there's no PR for the current branch, ask the user for a PR number.

## 2. Get check status

```bash
gh pr checks $PR_NUMBER
```

If all checks pass, report and stop.

## 3. Analyze failed checks

For each failed check, determine the failure category. Spin up parallel agents to investigate each failed job.

For each failed job URL, fetch the logs:

```bash
# URL format: https://github.com/OWNER/REPO/actions/runs/RUN_ID/job/JOB_ID
gh run view RUN_ID --log-failed 2>&1 | tail -200
```

If `--log-failed` is too verbose or doesn't work, try:

```bash
gh api repos/OWNER/REPO/actions/jobs/JOB_ID/logs 2>&1 | tail -200
```

### Classify each failure

**Category A — Flaky / infrastructure** (action: rerun)

- Timeouts unrelated to changed code
- Docker/container startup failures
- Network connectivity issues (DNS, HTTP timeouts to external services)
- ClickHouse / ZooKeeper connection errors
- Redis connection refused
- "Resource temporarily unavailable"
- Kafka broker not available
- Rate limiting from external services
- OOM kills on CI runner
- Sporadic segfaults in unrelated code
- Test failed but passed on a previous identical commit

**Category B — Stale branch / merge conflicts** (action: merge master)

- Import errors for symbols that exist on master but not on this branch
- Test failures referencing code recently changed on master
- Migration conflicts or missing migration dependencies
- Type errors from interfaces that changed on master
- Lockfile conflicts

**Category C — Real failures from our changes** (action: fix code)

- Test assertions failing on code we changed
- Lint / type errors in files we modified
- New test failures referencing our changed functions
- Import errors from our new code
- Schema validation failures from our changes

## 4. Cross-reference with changed files

```bash
gh pr diff $PR_NUMBER --name-only
```

Compare failed test files/modules against the changed files. If the failure is in code completely unrelated to our changes, it's more likely flaky or a master issue.

## 5. Check if failures are known flaky

```bash
gh run list --branch master --limit 5 --json status,conclusion,name -q '.[] | select(.conclusion == "failure") | .name'
```

If the same jobs are failing on master, they're not caused by our PR.

## 6. Report and act

Present a summary table:

| Job | Category | Reason | Action |
|-----|----------|--------|--------|

Then act:

### All Category A (flaky)

```bash
gh run rerun RUN_ID --failed
```

Report: "Re-triggered N flaky jobs. These failures are unrelated to your changes."

### Any Category B (stale branch)

```bash
git fetch origin master
git merge origin/master
```

If conflicts, report them. Otherwise push and let CI re-run.
Report: "Merged latest master to pick up recent changes. CI will re-run."

### Any Category C (real)

Do NOT rerun or merge. Instead:

1. Show the specific error messages
2. Show which of our changed files are involved
3. Suggest what needs to be fixed

Report: "These failures are caused by our changes and need fixes:"

### Mixed

Handle Category C first (those need fixes), then note the others.

- Fix code issues first
- After fixing, if Category B issues exist, merge master
- Category A jobs can be rerun after fixes are pushed
