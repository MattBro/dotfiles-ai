# Engineering

## Comments

**Be extremely sparing with comments.** If you need comments, the code isn't clean enough. Good code is self-documenting through clear naming and structure.

Only comment to explain a non-obvious **why**, to warn about a consequence or side effect, or to cite a legal requirement or attribution. **Never write a comment that explains *what* the code does.**

- **Docstrings are comments.** One that restates the function or test name explains what the code does. Test functions never get a docstring.
- **A non-obvious reason permits a comment; it does not require one.** The reason a fix exists usually belongs in the PR description or commit message. Wanting to record something you just worked out is the tell that it belongs there.
- **Never instruct a sub-agent to add a comment.** That is how a diff ends up 20% prose.
- **Never narrate change history.** No "previously did X", "rather than the old Y", "no longer", "this used to", "per PR #123", and no "AI:" or "agent:" notes. When fixing a bad comment, delete it; don't replace it with why it was wrong.
- **Never write a comment that goes stale on its own**: no measurements ("sustains 15 req/s", "~20 min build"), counts ("the only caller today"), or current-state stamps ("currently", "for now"). A number that matters belongs in a test, a constant, or a dashboard.

Bad:
- `// Create a customer` before `create_customer()`
- `// Paced per wave rather than once per batch, which used to burst past the budget`
- `// The weekly job walks ~203,000 records in about 3.8 hours`

Good:
- `// Dummy email satisfies the upstream API requirement; the real customer email lives elsewhere.`
- `// Must check this BEFORE sending to Stripe to avoid double-charging.`

## Debugging and bug fixes

**Always reproduce locally before fixing.** If you cannot reproduce it, do not implement a fix; nothing could verify it before deployment. Help me reproduce first, confirm you see the same error, then fix, then verify against that reproduction. If I say "I can't reproduce it yet" or "help me reproduce it", **write no fix code.** Exception: the bug is obvious from code inspection AND I explicitly say to fix without reproducing.

## Tests

**A new test earns its place only if it fails without the fix.** Revert the fix, run the test, watch it fail, restore. Do this for every test you add, including tests for review comments. A test written from the same understanding as the fix can pass against broken code.

## Synthetic data for third-party tests

**All test data sent to a third party must be synthetic and created from scratch.** This covers test, experiment, benchmark, and demo inputs sent through external APIs, AI models, or gateways, including sandbox and staging environments.

- Never use production records or customer data: signup-derived company profiles, logs, conversations, or website excerpts selected from customer records.
- Redacted, anonymized, renamed, and publicly available real data are not synthetic. Never generate synthetic fixtures from real data.
- AI consent, vendor approval, and working credentials do not waive this rule. Use credentials only through the service's authentication, never as test content.
- Check prompts, files, metadata, and tool arguments before sending.
- If synthetic data cannot verify a behavior, report that limitation; never fall back to real data.

## Launch observability: "how will I know when this breaks?"

**Answering this is a ship gate, same tier as tests.** Before launching anything that touches money or an external partner:

1. **The failure path emits a signal with an owner.** `capture_exception` into a surface nobody reads is not enough.
2. **An alert exists before launch**, routed to the team's `#alerts-*` channel, not the human team channel or email. For money-facing operations at PostHog billing, prefer the `billing/slo/` framework over hand-built insight alerts.
3. **Money paths get a scheduled monthly reconciliation** of our totals against the counterparty's.
4. **"Launched" means one observed execution, not green infrastructure.** ArgoCD Healthy, pods Running, and CI green all fit a component that never did its job. Watch one real unit of work land in the output data, and alert on *absence* of output: a component that never runs emits zero failures.
5. **Deploy-pipeline wiring is a pre-launch gate.** A hand-seeded image pointer stays frozen until its CD release entry exists.

## Dead code: delete, don't patch

**Once data proves code is dead** (it never worked, can never fire, or has zero users), **removal is the primary fix**, whatever the original author intended. A minimal, behavior-preserving patch is the default only while liveness is uncertain; never offer deletion as "an alternative if reviewers prefer". Prove deadness with prod queries, logs, or error tracking, not intuition. Lead the PR or delegation prompt with removal, state the evidence in the PR body, and offer the conservative patch only as a fallback in case review surfaces a live dependency.

## Maintainability is a build-time concern

- **Adopt the framework's native structure from the first endpoint.** For DRF: serializers, ViewSets, and authenticators, not loose `@api_view` functions with inline request parsing and manual auth.
- **Don't reuse a scaffold built for a different consumer or protocol just because it exists.** A second auth mechanism or API consumer landing in one module is the signal to split it.
- **Treat file growth as a refactor trigger**: a views file past ~800 lines, or a function past ~80, means stop and restructure.
- **After each feature milestone, run a code-smell pass**: duplication, god-functions, mixed concerns.

## Verify before asserting or drafting

**Check empirically verifiable facts from primary sources before you claim them, draft on them, or ask me to confirm them.**

- Prod data, the actual code, and the running system override an issue body, RFC, planning doc, or anyone's summary. Planning docs go stale: pre-launch becomes launched, "runs in prod" turns out to be staging.
- Use the tools you have: MCP prod queries, the local repos, the relevant skill, or running the integration. Don't theorize or hand me SQL to run when you could check it directly.
- Don't ask a recipient to confirm something measurable ("can you confirm whether you use X?"). Measure it, then tell them what you see.
- A comm, claim, PR description, or summary isn't ready until every fact in it traces to something checked. If you can't verify yet, say "let me verify" and do it.

## Separate how it works from how it should work

**When tracing a mechanism to find where a change goes, name each consumer and its holder before designing around what you find.** That A feeds B feeds C describes the current data flow; it does not put the change at A.

- One value sizing two consumers with different holders or trust boundaries means the coupling is the bug, not a constraint.
- A fix that seems to require changing something a third party owns is evidence the data flow is wrong.
- **Re-read the original request verbatim before proposing a design.** Its literal wording usually constrains the design more than accumulated context does.
- Before building a derivation, check whether it already exists on the other side of a language boundary.

## Numeric types for money

**Never use floats for money.** Use a money type (project-specific, e.g. `HogMoney("10.99", "USD")`) or `Decimal("10.99")`, never `10.99`.

## Error handling

For services that report to an error-tracking platform, prefer the platform's `capture_exception(exc, {context})` over `logger.exception` on error paths, and use it on every path that returns a 4xx or 5xx.

## Effort estimates

**Never estimate work in time units** ("1 week", "3-5 days", "~2 hours") in specs, plans, work breakdowns, PR descriptions, design docs, or project updates. Your time estimates anchor to human baselines that AI-assisted work breaks. Use relative size (small / medium / large, "smaller than X"), complexity signals ("mostly glue code", "blocked on an API design decision"), independently shippable phases ordered by dependency, and risks or unknowns ("Phase 0 is a spike to validate auth"). If asked directly for a time estimate, say: "I don't estimate time well; here's the relative size and the dependencies."
