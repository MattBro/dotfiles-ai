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

## Common review feedback to watch for

Recurring patterns in PR feedback I've received:

1. **Code duplication** — when copy-pasting, extract a helper function.
2. **Type safety** — add types proactively. Use enums for string constants.
3. **Import organization** — imports at the top of the file, not inline.
4. **API design** — consider what fields should be read-only. Use proper ViewSet inheritance.
5. **Irreversible actions** — add confirmation UX. Consider whether self-serve is appropriate.
