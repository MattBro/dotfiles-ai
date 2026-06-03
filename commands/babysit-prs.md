Actively monitor and maintain my open PRs by calling `/babysit-pr` on each one.

## Steps

1. Get all open PRs I authored across the repos in `$REVIEW_REPOS`.

   ```bash
   # Space-separated list of owner/name pairs. Set this in your shell rc, e.g.:
   #   export REVIEW_REPOS="PostHog/posthog PostHog/posthog-js"
   REVIEW_REPOS="${REVIEW_REPOS:-PostHog/posthog PostHog/posthog-js}"

   for repo in $REVIEW_REPOS; do
     gh pr list --author @me --state open --repo "$repo" --json number,title,url,headRefName
   done
   ```

2. For each open PR found, call `/babysit-pr <url>` using the Skill tool, passing the PR URL.
   Run these in parallel when possible (use agents). Each parallel `/babysit-pr` must operate in its own git worktree (see `CLAUDE.md` → Git Workflow → Workspaces) so the jobs don't collide on a single checkout.

3. If no open PRs are found across any repo, stay silent.
