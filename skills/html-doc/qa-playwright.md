# QA screenshot capture reference

Intended final filename: `qa-playwright.md`.

Use this when an HTML QA report needs real screenshot files for `.shots` cards.
The common path stays in `SKILL.md`; this file keeps the longer capture workflow
out of the main skill.

## Capture approach

- Use Playwright to write PNG files next to `body.html`, usually under `shots/`.
- Resolve Playwright from the current project (`npx playwright`, local
  `node_modules`, or an existing install discovered at runtime). Do not hardcode
  machine-specific absolute paths into the skill or scripts.
- For authenticated or context-scoped states, use `addInitScript` before
  navigation to seed required localStorage/session state, then navigate and
  drive the UI to each target state.
- Use `deviceScaleFactor: 2` for crisp text.
- Name files by state or acceptance criterion, such as
  `shots/library-row.png` or `shots/error-empty-state.png`.

## Why not conversation-only screenshots

Browser-driving tools are useful for visual confirmation, but screenshots shown
only inline in the conversation are not reliable source files for the builder.
`build.py` can inline only files reachable from disk through `<img src="...">`.

## Trust checks

- Open or inspect each PNG before using it. Reject blank pages, login redirects,
  wrong tenants, stale data, or clipped states.
- Cover the acceptance criteria: normal, empty, error, loading, and responsive
  states when relevant.
- Use `class="tag fail"` and a `.note.warn` for anything that did not pass.
- Do not mock screenshots in a QA evidence section. If a state was unreachable,
  state that plainly in the caption or nearby note.
