# Engineering

## Comments

- **Be extremely sparing with comments.** If you need comments, the code isn't clean enough. Good code is self-documenting through clear naming and structure.
- Only add comments to:
  - explain **why** something is done (when the reason is non-obvious)
  - warn about consequences or side effects
  - cite legal requirements or attributions
- **Never add comments that explain *what* the code does** — that should be obvious from the code itself. Don't restate what the docstring or function name already says.

Bad comments:
- `// Create a customer` before `create_customer()`
- `// Set email to None` before `email = None`
- `// Use first matching product key` before `product = config.get(product_keys[0])`

Good comments:
- `// We use a dummy email here to satisfy the upstream API requirement; real customer email lives elsewhere.`
- `// HACK: Workaround for Django bug #12345 — remove when fixed in 5.0.`
- `// Must check this BEFORE sending to Stripe to avoid double-charging.`

## Debugging and bug fixes

**Always reproduce locally before fixing.** If you cannot reproduce it, do not implement a fix.

Implementing fixes without reproduction means there's no way to verify the fix works until deployment, which is an unacceptably long iteration loop.

Steps:

1. User reports a bug or error.
2. Help reproduce it locally first.
3. Verify you can see the same error/behavior.
4. Only then implement the fix.
5. Verify the fix resolves the reproduced issue.

If the user says "I can't reproduce it yet" or "help me reproduce it", **do not write any fix code.**

Exception: the bug is obvious from code inspection AND the user explicitly says to fix without reproduction.

## Verify before asserting or drafting

**Check empirically-verifiable facts from primary sources before you claim them, draft on them, or ask me to confirm them.** Same spirit as reproduce-before-fixing, applied to claims and comms instead of code.

- **Primary source beats secondary.** Prod data, the actual code, and the running system override an issue body, RFC, planning doc, or anyone's summary. Don't repeat a planning doc as established fact — those go stale (pre-launch becomes launched, "runs in prod" turns out to be staging).
- **Reach for the tools you already have first.** MCP prod queries, the local repos, the relevant skill, or just running the real integration. Don't theorize or hand me SQL to run when you could check it directly.
- **Don't outsource verification to the recipient.** A partner comm that asks "can you confirm whether you use X?" about something measurable is a tell that the homework wasn't done. Measure it, then tell them what you see.
- **A comm or claim isn't ready until every fact in it traces to something checked.** Don't generate the downstream artifact (comms, PR description, summary) on an unverified premise.
- If you can't verify yet, say "let me verify" and go do it — don't ship a confident-but-unchecked artifact.

## Numeric types for money

**Never use floats for monetary calculations.** Use a money type (project-specific, e.g. `HogMoney`) or `Decimal`.

Floats have precision issues that cause rounding errors:

```python
# WRONG
price = 10.99
quantity = 3
total = price * quantity  # may have rounding error

# CORRECT — money type
price = HogMoney("10.99", "USD")
total = price * 3

# CORRECT — Decimal
from decimal import Decimal
rate = Decimal("0.15")
amount = Decimal("100.00")
result = amount * rate  # exactly 15.00
```

## Error handling

For services that report errors to a tracking platform: prefer the platform's `capture_exception` (or equivalent) over `logger.exception` for error paths.

Tracking platforms surface stack traces and grouping that logs alone don't. Use for all error paths that return 4xx or 5xx responses.

```python
from sentry_sdk import capture_exception

if not invoice:
    capture_exception(Exception("Invoice not found"), {"invoice_id": invoice_id})
    return JsonResponse({"error": "Invoice not found"}, status=404)
```

## Effort estimates

**Never estimate work in time units.** Don't write "1 week", "3-5 days", "~2 hours" on plans, specs, or work breakdowns. Your time estimates are systematically wrong because AI-assisted work runs much faster than the human-calibrated baselines you implicitly anchor to. When estimates are wrong, the planning analysis built on top of them is wrong too (sequencing, parallelism, "is this worth doing").

What to do instead:

- **Relative size only**: small / medium / large, or "smaller than X" / "larger than Y" when a known reference point exists.
- **Complexity signals over duration**: "mostly glue code", "needs new infrastructure", "requires cross-team coordination", "blocked on API design decision" carry far more information than a day count.
- **Independently shippable phases**: break work into phases that each deliver value, ordered by dependency. Don't attach time to them.
- **Risk and unknowns over duration**: "Phase 0 is a spike to validate auth" tells the reader more than "Phase 0 is 2 days".

If a human explicitly asks for a time estimate, say so plainly: "I don't estimate time well; here's the relative size and the dependencies." Don't guess hours.

Applies everywhere: specs, work plans, PR descriptions, design docs, project updates.

## Common review feedback to watch for

Recurring patterns in PR feedback I've received:

1. **Code duplication** — when copy-pasting, extract a helper function.
2. **Type safety** — add types proactively. Use enums for string constants.
3. **Import organization** — imports at the top of the file, not inline.
4. **API design** — consider what fields should be read-only. Use proper ViewSet inheritance.
5. **Irreversible actions** — add confirmation UX. Consider whether self-serve is appropriate.
