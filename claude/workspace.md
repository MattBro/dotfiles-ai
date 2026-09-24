# Workspace

## Working notes

Working files live in `~/dev/.claude/docs/`, organized by project. Project dirs (`stripe/`, `vercel/`) each hold `specs/`, `scripts/`, `drafts/`, `investigations/`; everything else goes in the top-level `specs/`, `scripts/`, `drafts/`, `investigations/`, `plans/`. Use descriptive filenames (`test_provisioning_pat.py`, not `test.py`). Drafts are ephemeral; clean them up after sending. The directory is private by default; its `README.md` has the safety policy.

## PostHog repos

- My PostHog monorepo rules (hogli, sandboxes, devboxes, migrations, Kea) are in `~/.claude/claude/posthog/`. Read them before working in a PostHog/posthog checkout unless they are already in your context.
- Repo skills load only in a session started inside the checkout, so start PostHog sessions there. From `~/dev`, read `~/dev/posthog/.agents/skills/<name>/SKILL.md` directly. Its `running-ci-preflight`, `merging-prs`, `writing-pr-descriptions`, `debugging-ci-failures`, `fixing-flaky-tests`, and `establishing-code-ownership` skills supersede my commands. Ones with no local equivalent: `stacking-prs`, `autoresolving-pr-conflicts`, `security-audit`, `qa-frontend`, `run-posthog`, `django-migrations`, `clickhouse-migrations`, `writing-tests`, `writing-kea-logics`.
- For prod SQL, run `hogli metabase:login`, `metabase:databases`, and `metabase:query --save` from `~/dev/posthog` (details in `claude/posthog/hogli.md`) instead of driving the Metabase UI in a browser.
- posthog.com lives at `~/dev/posthog.com`; its setup and gotchas are in that repo's `CLAUDE.local.md`.
