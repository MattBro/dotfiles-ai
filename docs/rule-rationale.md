# Rule rationale

The incidents, case studies, and extra examples behind the rules in `claude/`. Nothing loads this file into an agent's context. The rules carry only what an agent needs to act, which keeps PostHog Code's flattened copy under its 20k-character cap. When a new rule comes out of an incident, the story goes here.

## Engineering

### Comments

Change-history comments are noise: a reviewer reading the diff already sees what changed, and six months later the contrast describes code nobody can see. Replacing a bad comment with an explanation of why the old one was wrong just trades one banned kind for another.

Stale-by-construction comments read as fact and rot silently, because nothing fails when they stop being true.

A "what" comment example that was trimmed from the rule: `// Use first matching product key` before `product = config.get(product_keys[0])`.

### Tests

Reverting the fix takes thirty seconds, and it is the only thing that distinguishes coverage from decoration. A test that exercises the right branch can still assert nothing about the behaviour that matters. A reviewer who reports a real defect has told you exactly which revert to try.

### Launch observability

The recurring failure shape: an integration works at launch, degrades silently, and detection is a downstream human months later. Vercel invoice submission, Stripe app key expiry, and enrichment pipeline stalls all followed it. The accidental human reconciliation that eventually catches these should be a designed check.

Silent failure plus slowly growing stakes is the worst combination: at launch the volume is too small to notice, and by the time it's noticeable the bug is months old.

Green infrastructure hides dead components: probe-less workers crash-loop invisibly, and tracebacks ship at info severity. A hand-seeded image pointer can predate the feature code itself, shipping a fleet that never had the code.

### Dead code

A minimal patch with deletion offered as "an alternative if reviewers prefer" punts the decision to the reviewer, who says "just remove it" and costs a review cycle. Once the code is proven dead, the minimal patch is the worse option: it preserves dead code and adds special cases to it.

### Maintainability

The agentic provisioning API grew to a 3,000-line `views.py` because one module served two protocols (Stripe HMAC plus provisioning OAuth), forcing hand-rolled auth in every function and purely additive growth. Skipping the framework taxes every future endpoint with the boilerplate it exists to remove, and "it works, move on" repeated ten times is how 3,000-line files happen.

### Separate how it works from how it should work

A partner-provisioned API key copied its scopes from the partner's own OAuth token, because a single field in the partner's manifest fed both. Several rounds went into a generator, CI gates, and questions for the partner about editing their manifest, when the fix was to stop the developer's key reading from the partner's grant at all. The original request said "the return key", which named the right credential from the start. Verifying every fact along the chain didn't help, because the premise underneath it went unexamined.

### Effort estimates

Planning built on wrong time estimates (sequencing, parallelism, "is this worth doing") is wrong too. "Phase 0 is a spike to validate auth" says more than "Phase 0 is 2 days".

## Git workflow

- Worktrees share the repo's Git objects, and one worktree per branch, PR, or task lets parallel jobs run without fighting over a checkout.
- Size budgets exist to stop size degrading in tiny increments; bumping the limit whenever it trips defeats the check.
- Separate commits show the evolution of a change, for example `fix: use line item periods for invoices` followed by `refactor: extract _get_billing_period helper`.
- A fresh read before posting a PR comment matters because a colleague may have said the same thing while the agent was working, and a duplicate is noise on a PR other people are reading.

## hogli in personal repos

hogli is a general framework, published to PyPI, that turns a `hogli.yaml` into a discoverable, `--help`-documented command surface. Personal projects (`creekside-fields`, `buzz`, `brooker-wedding`) have none, so agents guess at commands from `package.json`. A ten-line `hogli.yaml` fixes that. The PyPI package is the framework alone; PostHog's own commands live in the monorepo under `tools/hogli-commands/`.
