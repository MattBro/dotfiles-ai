# Engineering

## Comments

**Be extremely sparing with comments.** If you need comments, the code isn't clean enough. Good code is self-documenting through clear naming and structure.

Only comment to explain **why** something is done when the reason is non-obvious, to warn about a consequence or side effect, or to cite a legal requirement or attribution. **Never write a comment that explains *what* the code does.**

**A non-obvious reason makes a comment permitted, not required.** This rule narrows what may be written; it is not a prompt to annotate every insight. The reason a fix exists usually belongs in the PR description or the commit message, where reviewers read it, rather than in the diff. Wanting to record something you just worked out is the tell that it belongs there instead.

Never instruct a sub-agent to add a comment. The rule already covers when one is allowed, and a per-fix request to explain the reasoning is how a diff ends up 20% prose.

Bad:
- `// Create a customer` before `create_customer()`
- `// Use first matching product key` before `product = config.get(product_keys[0])`

Good:
- `// Dummy email satisfies the upstream API requirement; the real customer email lives elsewhere.`
- `// Must check this BEFORE sending to Stripe to avoid double-charging.`

## Debugging and bug fixes

**Always reproduce locally before fixing.** If you cannot reproduce it, do not implement a fix. No reproduction means no way to verify the fix until deployment, which is an unacceptably long iteration loop.

Help me reproduce first, confirm you see the same error, then fix, then verify the fix against that reproduction. If I say "I can't reproduce it yet" or "help me reproduce it", **write no fix code.**

Exception: the bug is obvious from code inspection AND I explicitly say to fix without reproducing.

## Tests

**A new test earns its place only if it fails without the fix.** Revert the fix, run the test,
watch it fail, restore. Thirty seconds, and it is the only thing that distinguishes coverage
from decoration.

A test written from the same understanding that produced the fix will happily pass against
broken code, because it asserts what you already believed. That is how a test that exercises
the right branch still asserts nothing about the behaviour that matters.

Do this for every test you add in response to a review comment. A reviewer who reports a real
defect has told you exactly which revert to try.

## Launch observability: "how will I know when this breaks?"

**Answering this is a ship gate, same tier as tests.** The recurring failure shape: an integration works at launch, degrades silently, and detection is a downstream human months later (Vercel invoice submission, Stripe app key expiry, enrichment pipeline stalls). Captured-but-unrouted errors are indistinguishable from no errors.

Before launching anything that touches money or an external partner:

1. **The failure path emits a signal with an owner.** `capture_exception` into a surface nobody reads is not enough; it must route somewhere a specific team looks.
2. **An alert exists before launch**, routed to the team's `#alerts-*` channel, not the human team channel and not email. At PostHog billing, prefer the `billing/slo/` framework for money-facing operations over hand-built insight alerts.
3. **Money paths get a scheduled reconciliation loop**: our totals against the counterparty's, monthly. The accidental human reconciliation that eventually catches these should be a designed check.
4. **"Launched" means one observed execution, not green infrastructure.** ArgoCD Healthy, pods Running, and CI green are all compatible with a component that has never once done its job: probe-less workers crash-loop invisibly, tracebacks ship at info severity. End the checklist by watching one real unit of work land in the output data, and alert on *absence* of output, because a component that never runs emits zero failures.
5. **Deploy-pipeline wiring is a pre-launch gate**, never a trailing item. A deployable whose image pointer is hand-seeded stays frozen until its CD release entry exists, and the seed can predate the feature code itself, shipping a fleet that never had the code.

Silent failure plus slowly growing stakes is the worst combination: at launch the volume is too small to notice, and by the time it's noticeable the bug is months old.

## Dead code: delete, don't patch

**Once evidence proves code is dead, removal is the primary fix.** Don't propose a minimal patch with deletion offered as "an alternative if reviewers prefer"; that punts the real decision to the reviewer, who will say "just remove it" and cost a review cycle.

"Minimal, behavior-preserving change" is the safe default only while a feature's liveness is *uncertain*. Once data shows the code never worked, can never fire, or has zero users, the minimal patch is the worse option: it preserves dead code and adds special cases to it.

Prove deadness with data (prod queries, logs, error tracking), not intuition. Lead the PR or agent delegation prompt with removal and state the evidence in the PR body. Offer the conservative patch only as the fallback, for the case where review surfaces a live dependency. Deference to the original author's intent doesn't apply once the data settles it.

## Maintainability is a build-time concern, not a cleanup phase

Structural debt compounds silently while code "works", and agents do a worse job in a badly-structured file. Case study: the agentic provisioning API grew to a 3,000-line `views.py` because one module served two protocols (Stripe HMAC plus provisioning OAuth), forcing hand-rolled auth in every function and purely additive growth.

- **Adopt the framework's native structure from the first endpoint.** For DRF that means serializers, ViewSets, and authenticators, not loose `@api_view` functions with inline request parsing and manual auth. Skipping the framework taxes every future endpoint with the boilerplate it exists to remove.
- **Don't reuse a scaffold built for a different consumer or protocol just because it exists.** A second auth mechanism or a second API consumer landing in one module is the signal to split it, not to add another branch.
- **Treat file growth as a refactor trigger.** A views file past ~800 lines, or a single function past ~80, is a stop-and-restructure prompt.
- **Refactor checkpoints are part of the build.** After each feature milestone, run a code-smell pass (duplication, god-functions, mixed concerns). "It works, move on" repeated ten times is how 3,000-line files happen.

## Verify before asserting or drafting

**Check empirically-verifiable facts from primary sources before you claim them, draft on them, or ask me to confirm them.** Same spirit as reproduce-before-fixing, applied to claims and comms.

- **Primary source beats secondary.** Prod data, the actual code, and the running system override an issue body, RFC, planning doc, or anyone's summary. Planning docs go stale: pre-launch becomes launched, "runs in prod" turns out to be staging.
- **Reach for the tools you already have.** MCP prod queries, the local repos, the relevant skill, or just running the real integration. Don't theorize or hand me SQL to run when you could check it directly.
- **Don't outsource verification to the recipient.** A partner comm asking "can you confirm whether you use X?" about something measurable is a tell that the homework wasn't done. Measure it, then tell them what you see.
- **A comm or claim isn't ready until every fact in it traces to something checked.** Don't generate the downstream artifact (comms, PR description, summary) on an unverified premise.
- If you can't verify yet, say "let me verify" and go do it.

## Separate how it works from how it should work

**When tracing a mechanism to find where a change goes, name each consumer and its holder before designing around what you find.** Discovering that A feeds B feeds C tells you the current data flow, not that the change belongs at A. Verifying every fact along that chain doesn't help if the premise underneath it went unexamined.

The signal that a coupling is the bug rather than a constraint: one value sizes two consumers with different holders or trust boundaries. Case study: a partner-provisioned API key copied its scopes from the partner's own OAuth token, because a single field in the partner's manifest fed both. Several rounds went into a generator, CI gates, and questions for the partner about editing their manifest, when the fix was to stop the developer's key reading from the partner's grant at all.

- If a fix seems to require changing something a third party owns, treat that as evidence the data flow is wrong, not that the change belongs there.
- **Re-read the original request verbatim before proposing a design.** Investigation accumulates context and drifts. The literal wording usually constrains the design more than the accumulated context does; in the case above the request said "the return key", which named the right credential from the start.
- Before building a derivation, check whether it already exists on the other side of a language boundary.

## Numeric types for money

**Never use floats for monetary calculations**, they carry rounding error. Use a money type (project-specific, e.g. `HogMoney("10.99", "USD")`) or `Decimal("10.99")`, never `10.99`.

## Error handling

For services that report to an error-tracking platform, prefer the platform's `capture_exception(exc, {context})` over `logger.exception` on error paths. Tracking platforms surface stack traces and grouping that logs alone don't. Use it on every path that returns 4xx or 5xx.

## Effort estimates

**Never estimate work in time units.** No "1 week", "3-5 days", "~2 hours" on plans, specs, or work breakdowns. Your time estimates are systematically wrong because AI-assisted work runs much faster than the human-calibrated baselines you anchor to, and the planning built on them (sequencing, parallelism, "is this worth doing") is then wrong too.

Instead: relative size (small / medium / large, or "smaller than X"); complexity signals ("mostly glue code", "needs new infrastructure", "blocked on an API design decision"); independently shippable phases ordered by dependency; and risk or unknowns ("Phase 0 is a spike to validate auth" says more than "Phase 0 is 2 days").

If asked directly for a time estimate, say so plainly: "I don't estimate time well; here's the relative size and the dependencies." Applies to specs, work plans, PR descriptions, design docs, project updates.
