---
name: html-doc
description: >-
  Generate a polished, self-contained HTML document: explainer, plan, spec,
  status update, data/BI report, or QA report with embedded D2 diagrams,
  bar/line charts, optional vega-lite charts, KPI cards, UI mockups, code,
  tables, and inline screenshots. Use when the user asks for an HTML doc/page,
  shareable visual write-up, dashboard/data report, or screenshot-backed QA
  artifact instead of a wall of Markdown.
---

# HTML docs

Produce one portable `.html` file. `build.py` renders D2 files and chart JSON to
inline SVG, base64-inlines local images, and stitches a styled shell with one
inline script for the screenshot lightbox. No external assets or CDN.

Use HTML when the result needs to be scanned, inspected, or shared: plans, specs,
implementation explainers, status updates, BI reports, QA reports, and design
system notes.

## Build

Write `body.html`, optional `diagrams/*.d2`, optional `charts/*.json`, then run:

```bash
python3 <SKILL_DIR>/build.py \
  --title "My report" \
  --body body.html \
  --diagrams diagrams \
  --charts charts \
  --out my-report.html
```

`--diagrams` and `--charts` are optional. Local `<img src="...">` files are
inlined automatically, including single- or double-quoted `src` attributes.

## Choose the lightest visual

- Table: default for lists, attributes, linear sequences, and small comparisons.
- `.flow`: compact step strip for a short `a -> b -> c` sequence.
- D2: only for non-linear topology: branches, merges, loops, state machines,
  lanes, or architecture relationships.
- Chart: comparing or trending numbers. Two or three numbers are usually KPI
  cards or a table.

If deleting arrows loses no meaning, it was not a diagram. For dated/statused
steps, prefer a table with `td.step`, `tr.mark`, and `tr.done`.

## Sizing rule

Figures render at natural SVG size and are never upscaled. `build.py` gives
charts explicit width/height (`CW`) and pins D2 root SVGs to their viewBox pixel
size; `.fig svg { max-width:100%; height:auto; }` only shrinks them to fit.
Do not reintroduce `width:100%` on figure SVGs.

For D2:

- Use `direction: down` by default.
- Keep labels short and single-line; put detail in prose.
- Keep diagrams to roughly 8 nodes, or split them.
- Avoid nested containers that shrink child text.
- Do not put `$` in labels; D2 treats it as substitution syntax.
- Fix any `WARN: ... renders Npx wide` by narrowing/splitting the diagram.

Example `diagrams/flow.d2`:

```d2
direction: down
a: User uploads doc
b: Agent extracts fields { style.fill: "#d1fae5" }
c: Stored in plan_details
a -> b: upload
b -> c: commit
```

## Charts and KPI cards

Built-in charts are dependency-free inline SVG:

```json
{ "type": "bar", "prefix": "$", "target": 180,
  "series": [ {"label":"Jan","value":120}, {"label":"Feb","value":150},
              {"label":"Mar","value":175}, {"label":"Apr","value":190} ] }
```

```json
{ "type": "line", "suffix": "%", "x": ["W1","W2","W3","W4"],
  "series": [ {"label":"Success","values":[88,91,94,96]},
              {"label":"Retry","values":[12,9,6,4]} ] }
```

Reference charts in the body as `@@revenue@@`. Bar charts accept `target` and
auto-switch to horizontal layout when labels are long. Line charts accept shared
`x` labels and one or more series; multiple series draw a legend.

Number formatting: without `suffix`, large values abbreviate (`850000` ->
`850K`). With explicit `suffix`, values stay grouped so units do not double
(`prefix:"$", suffix:"K", value:1000` -> `$1,000K`, never `$1KK`).

Optional vega-lite engine: `area`, `scatter`, `grouped`, and `stacked`, or
`"engine":"vega"` on bar/line, use `vl-convert` when installed and still output
inline SVG. Install with `pip install vl-convert-python`. If absent, rich types
exit with a clean install hint; `engine:"vega"` bar/line specs fall back to the
built-in renderer with a note.

KPI cards are plain HTML:

```html
<div class="kpigrid">
  <div class="kpi"><div class="l">Runs - 30d</div><div class="n">1,284</div>
    <div class="d up">▲ 45% vs prior</div></div>
  <div class="kpi"><div class="l">Success rate</div><div class="n">96.5%</div>
    <div class="d flat">▬ flat</div></div>
</div>
```

Use `.d.up`, `.d.down`, and `.d.flat`; include a glyph, not color alone. Reuse
series colors consistently and annotate numbers with time frame/benchmark.

## QA screenshots

Use `.shots` / `.shot` for screenshot evidence. `build.py` inlines the PNGs and
the shell wires a lightbox: click a shot to open a full-screen gallery with
keyboard/on-screen previous/next, caption panel, and fullscreen toggle.

```html
<div class="shots">
  <div class="shot">
    <img src="shots/library-row.png" alt="Library row showing usage">
    <div class="cap"><b>Library - <span class="tag pass">PASS</span></b>
      As an author, I want seeded usage to appear in the Library row.</div>
  </div>
  <div class="shot">
    <img src="shots/insights-30d.png" alt="Insights page, 30 day default">
    <div class="cap"><b>Insights - <span class="tag mark">CHECK</span></b>
      As an author, I want default insights to show cards, chart, usage, and runs.</div>
  </div>
</div>
```

Capture real PNG files with Playwright when possible; do not fake QA evidence.
For the longer capture workflow and sandbox notes, see sibling reference
`qa-playwright.md` (intended final filename: `qa-playwright.md`).

## Body classes

- `<header>`, `h1`, `.sub`, `.pill`, `.pill.blue` for the title block. Pills are
  optional metadata chips; omit them when they carry no signal.
- `h2`, `h3`, `footer` for document structure.
- `.fig` with `.figcap` for D2 diagrams or `@@chart@@`.
- `.kpigrid` > `.kpi` with `.l`, `.n`, `.d up|down|flat` for KPI cards.
- `table`, `th`, `td`; `.num` for right-aligned numeric cells, `td.step` for a
  centered step number, `tr.mark` amber, `tr.done` green.
- `.note` and `.note.warn` for callouts.
- `.step` with `ol.steps` for a numbered walkthrough.
- `.flow` > `.fstep` with optional `.when`, `.fstep.mark`, `.fstep.done`.
- `.mock` with `.bar`, `.bar i`, and `.bar span` for a fake window-frame mockup.
- `.shots` > `.shot` with `img` and `.cap`; `.tag pass|fail|mark` for status.
- `details > summary`, `code`, and `<pre><code>...</code></pre>` are styled.

## Theming (dark default + light toggle)

The shell renders **dark by default** and ships a fixed top-right toggle
(`☀ Light` / `☾ Dark`). The choice persists in `localStorage`; first visit
honours the OS `prefers-color-scheme`. Both themes are driven entirely by CSS
variables on `:root` (dark) and `:root[data-theme="light"]` (light), so
everything swaps from one attribute flip. Available tokens: `--ink`, `--muted`,
`--line`, `--bg`, `--card`, `--card-head`, `--accent`, `--green`, `--amber`,
`--rust`, `--blue`, `--code-bg`, `--code-ink`, `--shadow`.

**Build per-doc overrides from those variables, never hardcoded hex** — a
literal light color (`background:#fff`) will look broken in dark mode. Tinted
surfaces use `color-mix(in srgb, var(--green) 16%, transparent)` so they read on
either theme. Built-in chart SVGs tag their axis/grid/value text with `.g-line`,
`.g-txt`, `.v-txt` so they follow the theme; series colors stay fixed.

Baked-at-build limitations: **d2 diagrams** render with their own (light) theme
and do not follow the toggle; **vega-lite** charts use a transparent background
and mid-tone axes so they stay legible on both, but also don't switch live. The
built-in `bar`/`line` charts are fully theme-aware.

Override per-doc with a `<style>` block at the top of `body.html` (body rules win
on order). Copy-pasteable starting point:

```html
<style>
  /* Shared surface — cards and tables lift off the page identically */
  :root  { --frame: 0 0 0 1px var(--line), 0 1px 3px var(--shadow); }
  .kpi   { border: none; border-radius: 8px; box-shadow: var(--frame); }
  table  { border-radius: 8px; overflow: hidden; box-shadow: var(--frame); }

  /* Muted column-label header (data-table convention) */
  thead th { background:var(--card-head); color:var(--muted); font-size:12px; font-weight:600;
             text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid var(--line); }
  th, td   { padding:9px 14px; }

  /* Lozenges — one pill style shared by status tags and t-shirt sizes */
  .tag, .sz        { display:inline-block; padding:1px 8px; border-radius:10px;
                     font-size:11px; font-weight:700; white-space:nowrap; }
  .tag.pass, .sz.s { background:color-mix(in srgb, var(--green) 16%, transparent); color:var(--green); }
  .tag.mark, .sz.m { background:color-mix(in srgb, var(--amber) 16%, transparent); color:var(--amber); }
</style>
```

Frame a table with a **box-shadow ring**, never `border`. The shell uses
`border-collapse`, so a `table { border }` is overridden at the edge by the cell
borders and silently disappears (looks borderless/white). The ring sits outside
the collapse and respects `border-radius`. Use one `--frame` token on both `.kpi`
and `table` so cards and tables pop by the same amount.

## Verify

Serve and inspect the output before handoff:

```bash
( cd "$(dirname my-report.html)" && python3 -m http.server 8899 >/dev/null 2>&1 & )
# open http://localhost:8899/my-report.html
```

Check that diagrams/charts are legible, numbers and deltas are formatted, images
are inlined rather than broken, and lightbox galleries open. Reopening the same
filename can focus a stale tab instead of reloading — hard-reload (Cmd-R) or add
a `?v=N` cachebuster. Kill the server afterward: `pkill -f "http.server 8899"`.

## Prereqs

- `d2` CLI (`brew install d2`) for diagrams.
- `python3` for `build.py`; built-in charts and image inlining use stdlib only.
- `vl-convert-python` only for optional vega-lite chart types.
- Playwright only when capturing QA screenshots as real files.
