#!/usr/bin/env python3
"""Inline D2 diagrams and data charts into a styled, self-contained HTML doc.

Usage:
  build.py --title "My Doc" --body body.html --out doc.html \
           [--diagrams ./diagrams] [--charts ./charts]

Renders every *.d2 in --diagrams to SVG via the `d2` CLI and replaces each
`%%<name>%%` token in the body with that inline SVG. Renders every *.json in
--charts (bar/line specs) to an inline SVG and replaces each `@@<name>@@`
token. Any local `<img src="...">` (screenshots, etc.) is base64-inlined as a
data URI, so QA reports stay one portable file. Output is one portable file, no
external assets, no CDN — just one small inline script that powers the screenshot
lightbox (full-screen click-through gallery with captions).

Figures render at natural SVG size and only shrink to fit. Diagrams wider than
900px warn because they will shrink in the document; prefer `direction: down`.
"""
import argparse
import base64
import html as _html
import json
import math
import pathlib
import re
import subprocess
import sys

CSS = r"""
  /* Dark is the default theme; light is opt-in via :root[data-theme="light"].
     Both are driven entirely by these variables, so the runtime toggle only
     has to flip one attribute on <html>. Tinted surfaces (pills, notes, table
     rows) use color-mix so they read against the card in either theme. */
  :root { --ink:#e6edf3; --muted:#9aa7b4; --line:#2d3742; --bg:#0f1419;
    --card:#1a212b; --card-head:#232c38; --blue:#5b9bf0;
    --accent:#4fb3c9; --green:#3fb88f; --amber:#e0a82e; --rust:#e0703a;
    --code-bg:#0b1120; --code-ink:#e2e8f0; --shadow:rgba(0,0,0,.30); }
  :root[data-theme="light"] { --ink:#1f2933; --muted:#5b6770; --line:#e3e8ee; --bg:#f7f9fb;
    --card:#fff; --card-head:#eef2f6; --blue:#2563eb;
    --accent:#2E8DA1; --green:#2F9C7F; --amber:#C5890A; --rust:#C5500A;
    --code-bg:#0f172a; --code-ink:#e2e8f0; --shadow:rgba(0,0,0,.04); }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .theme-toggle { position:fixed; top:14px; right:14px; z-index:50; cursor:pointer;
    background:var(--card); color:var(--ink); border:1px solid var(--line); border-radius:999px;
    padding:7px 13px; font:600 13px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    box-shadow:0 1px 3px var(--shadow); display:flex; align-items:center; gap:6px; }
  .theme-toggle:hover { border-color:var(--accent); }
  @media print { .theme-toggle { display:none; } }
  .wrap { max-width:960px; margin:0 auto; padding:40px 24px 80px; }
  header { border-bottom:3px solid var(--accent); padding-bottom:18px; margin-bottom:8px; }
  h1 { font-size:28px; margin:0 0 6px; letter-spacing:-.01em; }
  h2 { font-size:21px; margin:42px 0 12px; padding-top:10px; border-top:1px solid var(--line); }
  h3 { font-size:16px; margin:26px 0 8px; color:var(--accent); }
  .sub { color:var(--muted); font-size:15px; }
  .pill { display:inline-block; font-size:12px; font-weight:600; padding:2px 9px; border-radius:999px;
    background:color-mix(in srgb, var(--green) 16%, transparent); color:var(--green); margin-right:6px; }
  .pill.blue { background:color-mix(in srgb, var(--blue) 16%, transparent); color:var(--blue); }
  a { color:var(--accent); }
  code { background:color-mix(in srgb, var(--ink) 9%, transparent); padding:1px 6px; border-radius:5px; font-size:13.5px;
    font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace; }
  pre { background:var(--code-bg); color:var(--code-ink); padding:16px 18px; border-radius:10px;
    overflow-x:auto; font-size:13px; line-height:1.55; }
  pre code { background:none; color:inherit; padding:0; }
  .fig { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px;
    margin:18px 0; text-align:center; box-shadow:0 1px 2px var(--shadow); }
  /* Never upscale figures: render at natural size, only shrink to fit. */
  .fig svg { width:auto; max-width:100%; height:auto; }
  /* Chart internals are tagged with classes so axis/grid/label colors follow
     the theme; series colors (bars, lines) stay fixed and read on both. */
  .fig svg .g-line { stroke:var(--line); }
  .fig svg .g-txt { fill:var(--muted); }
  .fig svg .v-txt { fill:var(--ink); }
  .figcap { font-size:13px; color:var(--muted); margin-top:10px; text-align:left; }
  table { border-collapse:collapse; width:100%; font-size:14px; margin:14px 0; }
  th,td { border:1px solid var(--line); padding:8px 11px; text-align:left; vertical-align:top; }
  th { background:var(--card-head); font-weight:600; }
  td.num,th.num { text-align:right; font-variant-numeric:tabular-nums; }
  tr.mark > td { background:color-mix(in srgb, var(--amber) 13%, transparent); }
  tr.done > td { background:color-mix(in srgb, var(--green) 13%, transparent); }
  td.step { text-align:center; font-weight:700; color:var(--muted); font-variant-numeric:tabular-nums; width:34px; }
  .note { border-left:4px solid var(--accent); background:var(--card); padding:12px 16px;
    border-radius:0 8px 8px 0; margin:16px 0; font-size:14.5px; }
  .note.warn { border-color:var(--amber); background:color-mix(in srgb, var(--amber) 9%, var(--card)); }
  .step { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:4px 18px 14px; margin:14px 0; }
  ol.steps > li { margin:8px 0; }
  details { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:6px 16px; margin:12px 0; }
  details > summary { cursor:pointer; font-weight:600; padding:6px 0; }
  details[open] > summary { border-bottom:1px solid var(--line); margin-bottom:10px; }
  .mock { border:1px solid var(--line); border-radius:10px; background:var(--card); padding:14px;
    box-shadow:0 1px 2px var(--shadow); font-size:14px; margin:16px 0; }
  .mock .bar { display:flex; align-items:center; gap:6px; margin:-14px -14px 12px;
    padding:9px 12px; background:var(--card-head); border-bottom:1px solid var(--line); border-radius:10px 10px 0 0; }
  .mock .bar i { width:10px; height:10px; border-radius:50%; background:var(--muted); display:inline-block; }
  .mock .bar span { margin-left:6px; font-size:12px; color:var(--muted); }
  .kpigrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:14px; margin:18px 0; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:15px 17px;
    box-shadow:0 1px 2px var(--shadow); }
  .kpi .l { font-size:12px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
  .kpi .n { font-size:29px; font-weight:700; letter-spacing:-.02em; margin:7px 0 2px; font-variant-numeric:tabular-nums; }
  .kpi .d { font-size:13px; font-weight:600; }
  .kpi .d.up { color:var(--green); }
  .kpi .d.down { color:var(--rust); }
  .kpi .d.flat { color:var(--muted); }
  .legend { display:flex; flex-wrap:wrap; gap:14px; justify-content:center; margin-top:10px; font-size:12px; color:var(--muted); }
  .legend i { display:inline-block; width:11px; height:11px; border-radius:3px; margin-right:5px; vertical-align:-1px; }
  .shots { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:18px; margin:18px 0; }
  .shot { border:1px solid var(--line); border-radius:12px; background:var(--card); overflow:hidden;
    box-shadow:0 1px 2px var(--shadow); }
  .shot img { width:100%; display:block; border-bottom:1px solid var(--line);
    background:var(--card-head); cursor:zoom-in; }
  .shot .cap { padding:12px 14px; font-size:13.5px; color:var(--ink); line-height:1.5; }
  .shot .cap b { display:block; font-size:11px; color:var(--muted); text-transform:uppercase;
    letter-spacing:.04em; margin-bottom:4px; }
  .tag { display:inline-block; font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px;
    letter-spacing:.03em; }
  .tag.pass { background:color-mix(in srgb, var(--green) 16%, transparent); color:var(--green); }
  .tag.fail { background:color-mix(in srgb, var(--rust) 16%, transparent); color:var(--rust); }
  .tag.mark { background:color-mix(in srgb, var(--amber) 16%, transparent); color:var(--amber); }
  /* Step strip: a short linear sequence a -> b -> c without burning a screen of
     height on a vertical flowchart. Arrows are drawn between steps; it wraps. */
  .flow { display:flex; flex-wrap:wrap; gap:11px 26px; margin:18px 0; }
  .flow .fstep { position:relative; background:var(--card); border:1px solid var(--line);
    border-radius:9px; padding:9px 13px; font-size:13.5px; }
  .flow .fstep:not(:first-child)::before { content:"\2192"; position:absolute; left:-20px;
    top:50%; transform:translateY(-50%); color:var(--muted); font-size:14px; }
  .flow .fstep .when { display:block; font-size:11px; color:var(--muted); margin-top:2px; }
  .flow .fstep.mark { background:color-mix(in srgb, var(--amber) 11%, var(--card)); border-color:var(--amber); }
  .flow .fstep.done { background:color-mix(in srgb, var(--green) 11%, var(--card)); border-color:var(--green); }
  footer { margin-top:50px; padding-top:16px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; }
  /* Screenshot lightbox: click a .shot to open a full-screen left/right gallery
     with the caption text kept visible beside the image. JS wires it up. */
  .lb { position:fixed; inset:0; z-index:9999; background:rgba(15,23,42,.94); display:none; }
  .lb.open { display:flex; flex-direction:column; }
  .lb-bar { display:flex; align-items:center; gap:12px; padding:10px 16px; color:#e2e8f0;
    flex:0 0 auto; font-size:13px; }
  .lb-bar .ct { font-variant-numeric:tabular-nums; font-weight:700; }
  .lb-bar .sp { flex:1; }
  .lb-bar button { background:rgba(255,255,255,.12); color:#e2e8f0; border:0; border-radius:7px;
    padding:7px 12px; cursor:pointer; font-size:13px; font-weight:600; }
  .lb-bar button:hover { background:rgba(255,255,255,.24); }
  .lb-body { flex:1; display:flex; min-height:0; }
  .lb-stage { flex:1; position:relative; display:flex; align-items:center; justify-content:center;
    min-width:0; padding:10px 10px 18px; }
  .lb-stage img { max-width:100%; max-height:100%; object-fit:contain; border-radius:8px;
    box-shadow:0 12px 44px rgba(0,0,0,.5); }
  .lb-cap { flex:0 0 330px; background:#0f172a; color:#cbd5e1; padding:24px 22px 32px;
    overflow:auto; font-size:14px; line-height:1.6; border-left:1px solid rgba(255,255,255,.08); }
  .lb-cap b { display:block; font-size:11px; color:#94a3b8; text-transform:uppercase;
    letter-spacing:.05em; margin-bottom:8px; }
  .lb-arrow { position:absolute; top:50%; transform:translateY(-50%); width:46px; height:46px;
    border-radius:50%; border:0; background:rgba(255,255,255,.15); color:#fff; font-size:26px;
    line-height:1; cursor:pointer; display:flex; align-items:center; justify-content:center; }
  .lb-arrow:hover { background:rgba(255,255,255,.3); }
  .lb-arrow.prev { left:16px; } .lb-arrow.next { right:16px; }
  .lb-arrow[disabled] { opacity:.22; cursor:default; }
  @media (max-width:720px){ .lb-body { flex-direction:column; }
    .lb-cap { flex:0 0 auto; max-height:40vh; border-left:0; border-top:1px solid rgba(255,255,255,.08); } }
"""

# Two small inline scripts: a theme toggle (dark default, light opt-in, choice
# persisted), then the .shots lightbox (inert if no gallery exists).
JS = r"""
(function(){
  var KEY = 'htmldoc-theme', root = document.documentElement, cur;
  var saved = null; try { saved = localStorage.getItem(KEY); } catch(e){}
  function apply(t){ cur = t === 'light' ? 'light' : 'dark';
    if(cur === 'light') root.setAttribute('data-theme','light'); else root.removeAttribute('data-theme'); }
  apply(saved || (window.matchMedia
    && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'));
  var btn = document.createElement('button');
  btn.className = 'theme-toggle'; btn.type = 'button';
  btn.setAttribute('aria-label', 'Toggle light or dark theme');
  function label(){ btn.textContent = cur === 'light' ? '☾ Dark' : '☀ Light'; }
  label();
  btn.addEventListener('click', function(){
    apply(cur === 'light' ? 'dark' : 'light'); label();
    try { localStorage.setItem(KEY, cur); } catch(e){}
  });
  document.body.appendChild(btn);
})();
(function(){
  var galleries = [].slice.call(document.querySelectorAll('.shots'));
  if(!galleries.length) return;
  var lb = document.createElement('div');
  lb.className = 'lb';
  lb.innerHTML =
    '<div class="lb-bar"><span class="ct"></span><span class="sp"></span>'+
      '<button data-act="fs">⛶ Fullscreen</button>'+
      '<button data-act="close">✕ Close</button></div>'+
    '<div class="lb-body"><div class="lb-stage">'+
      '<button class="lb-arrow prev" data-act="prev" aria-label="Previous">‹</button>'+
      '<img alt="">'+
      '<button class="lb-arrow next" data-act="next" aria-label="Next">›</button>'+
    '</div><div class="lb-cap"></div></div>';
  document.body.appendChild(lb);
  var img = lb.querySelector('.lb-stage img'),
      cap = lb.querySelector('.lb-cap'),
      ct  = lb.querySelector('.ct'),
      prev = lb.querySelector('[data-act=prev]'),
      next = lb.querySelector('[data-act=next]');
  var group = [], idx = 0;
  function render(){
    var s = group[idx], im = s.querySelector('img'), cp = s.querySelector('.cap');
    img.src = im.currentSrc || im.src; img.alt = im.alt || '';
    cap.innerHTML = cp ? cp.innerHTML : '';
    ct.textContent = (idx+1) + ' / ' + group.length;
    prev.disabled = idx === 0;
    next.disabled = idx === group.length - 1;
  }
  function open(g, i){ group = g; idx = i; render(); lb.classList.add('open');
    document.body.style.overflow = 'hidden'; }
  function close(){ lb.classList.remove('open'); document.body.style.overflow = '';
    if(document.fullscreenElement) document.exitFullscreen(); }
  function go(d){ var n = idx + d; if(n < 0 || n >= group.length) return; idx = n; render(); }
  galleries.forEach(function(gallery){
    var items = [].slice.call(gallery.querySelectorAll('.shot'));
    items.forEach(function(s, i){
      var im = s.querySelector('img'); if(!im) return;
      im.addEventListener('click', function(){ open(items, i); });
    });
  });
  lb.addEventListener('click', function(e){
    var act = e.target.getAttribute && e.target.getAttribute('data-act');
    if(act === 'close') return close();
    if(act === 'prev') return go(-1);
    if(act === 'next') return go(1);
    if(act === 'fs') return document.fullscreenElement ? document.exitFullscreen()
                          : (lb.requestFullscreen && lb.requestFullscreen());
    if(e.target === lb || e.target.classList.contains('lb-body')
       || e.target.classList.contains('lb-stage')) close();
  });
  document.addEventListener('keydown', function(e){
    if(!lb.classList.contains('open')) return;
    if(e.key === 'Escape') close();
    else if(e.key === 'ArrowLeft') go(-1);
    else if(e.key === 'ArrowRight') go(1);
  });
})();
"""

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%%</title>
<style>%%CSS%%</style>
</head>
<body>
<div class="wrap">
%%BODY%%
</div>
<script>%%JS%%</script>
</body>
</html>
"""

# Color-blind-safe categorical palette (Okabe-Ito subset, harmonized with the
# doc accent). Reuse meaning across charts — same series = same color.
CHART_COLORS = ["#2E8DA1", "#E69F00", "#2F9C7F", "#CC79A7", "#56342B", "#5b6770"]
GRID = "#e3e8ee"
AXIS_INK = "#5b6770"
LABEL_INK = "#1f2933"
FONT = "-apple-system,Segoe UI,Roboto,sans-serif"


def _fmt(v, prefix="", suffix=""):
    """Format a value with optional prefix/suffix.

    Explicit suffixes use grouped values to avoid double units: `suffix="K"`,
    1000 -> "$1,000K", never "$1KK". Without suffix, big numbers abbreviate.
    """
    if suffix:
        s = f"{v:,.2f}".rstrip("0").rstrip(".") if v % 1 else f"{int(v):,}"
        return f"{prefix}{s}{suffix}"
    a = abs(v)
    if a >= 1e9:
        s = f"{v / 1e9:.2f}".rstrip("0").rstrip(".") + "B"
    elif a >= 1e6:
        s = f"{v / 1e6:.2f}".rstrip("0").rstrip(".") + "M"
    elif a >= 1e3:
        s = f"{v / 1e3:.2f}".rstrip("0").rstrip(".") + "K"
    else:
        s = f"{v:.2f}".rstrip("0").rstrip(".")
    return f"{prefix}{s}{suffix}"


def _nice(v):
    """Round an axis maximum up to a clean gridline value."""
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    base = 10 ** exp
    f = v / base
    for n in (1, 1.5, 2, 2.5, 3, 4, 5, 10):
        if f <= n + 1e-9:
            return n * base
    return 10 * base


# Charts render at a fixed canonical width; `.fig svg` never upscales them.
# 1 user-unit ~= 1px, so font-size:11 stays near 11px instead of being magnified.
CW = 672          # total canonical chart width
_CHAR_W = 6.1     # ~px per char at font-size 11 (for label-fit estimates)


def _est_w(s, fs=11):
    return len(str(s)) * _CHAR_W * fs / 11.0


def _svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">')


def _grid_values(vmin, vmax):
    return [vmin + (vmax - vmin) * i / 4 for i in range(5)]


def _add_y_grid(p, w, padl, padr, y, values, pre, suf):
    for val in values:
        gy = y(val)
        p.append(f'<line class="g-line" x1="{padl}" y1="{gy:.1f}" x2="{w - padr}" y2="{gy:.1f}" stroke="{GRID}"/>')
        p.append(f'<text class="g-txt" x="{padl - 8}" y="{gy + 4:.1f}" font-size="11" fill="{AXIS_INK}" '
                 f'text-anchor="end">{_fmt(val, pre, suf)}</text>')


def _add_x_grid(p, padl, padt, ploth, x, values, pre, suf):
    for val in values:
        gx = x(val)
        p.append(f'<line class="g-line" x1="{gx:.1f}" y1="{padt}" x2="{gx:.1f}" y2="{padt + ploth}" stroke="{GRID}"/>')
        p.append(f'<text class="g-txt" x="{gx:.1f}" y="{padt + ploth + 16}" font-size="11" fill="{AXIS_INK}" '
                 f'text-anchor="middle">{_fmt(val, pre, suf)}</text>')


def _bar_svg(spec):
    """Vertical bars for short labels; auto-switches to horizontal for long
    category names (the layout that was overflowing before)."""
    data = spec["series"]
    pre, suf = spec.get("prefix", ""), spec.get("suffix", "")
    target = spec.get("target")
    vmax = _nice(max([d["value"] for d in data] + [target or 0] + [0]) or 1)
    labels = [str(d["label"]) for d in data]
    n = max(1, len(data))
    slot = CW * 0.86 / n  # available px per category in a vertical layout

    # Long labels don't fit under a bar -> horizontal layout gives them a gutter.
    if any(_est_w(l) > slot for l in labels):
        return _hbar_svg(data, labels, vmax, pre, suf, target)

    PADL, PADR, PADT, PADB = 54, 18, 30, 46
    plotw, ploth = CW - PADL - PADR, 230
    W, H = CW, PADT + ploth + PADB
    slot = plotw / n
    bw = min(120, slot * 0.6)

    def y(val):
        return PADT + ploth - (val / vmax) * ploth

    p = [_svg_open(W, H)]
    _add_y_grid(p, W, PADL, PADR, y, _grid_values(0, vmax), pre, suf)
    if target is not None:
        ty = y(target)
        p.append(f'<line x1="{PADL}" y1="{ty:.1f}" x2="{W - PADR}" y2="{ty:.1f}" '
                 f'stroke="{CHART_COLORS[1]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        # Target label sits at the LEFT end so it can't collide with a bar's
        # value label at the right where a near-target bar peaks.
        p.append(f'<text x="{PADL + 4}" y="{ty - 5:.1f}" font-size="10.5" fill="{CHART_COLORS[1]}" '
                 f'text-anchor="start" font-weight="600">target {_fmt(target, pre, suf)}</text>')
    for i, d in enumerate(data):
        bx = PADL + i * slot + (slot - bw) / 2
        by = y(d["value"])
        bh = (PADT + ploth) - by
        p.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                 f'rx="3" fill="{CHART_COLORS[0]}"/>')
        # If the bar peaks within ~16px of the target line, draw the value
        # inside the bar (white) so the two labels never stack.
        near = target is not None and abs(by - y(target)) < 16
        if near and bh > 24:
            p.append(f'<text x="{bx + bw / 2:.1f}" y="{by + 15:.1f}" font-size="11" fill="#fff" '
                     f'text-anchor="middle" font-weight="700">{_fmt(d["value"], pre, suf)}</text>')
        else:
            p.append(f'<text class="v-txt" x="{bx + bw / 2:.1f}" y="{by - 6:.1f}" font-size="11" fill="{LABEL_INK}" '
                     f'text-anchor="middle" font-weight="700">{_fmt(d["value"], pre, suf)}</text>')
        p.append(f'<text class="g-txt" x="{bx + bw / 2:.1f}" y="{PADT + ploth + 16}" font-size="11" fill="{AXIS_INK}" '
                 f'text-anchor="middle">{_html.escape(labels[i])}</text>')
    p.append("</svg>")
    return "".join(p)


def _hbar_svg(data, labels, vmax, pre, suf, target):
    """Horizontal bars: category labels get a left gutter, values sit at the bar
    end, target is a vertical line — three label zones that can't overlap."""
    n = len(data)
    gutter = min(210, max(90, int(max(_est_w(l, 12) for l in labels)) + 12))
    PADR, PADT, PADB = 66, 26, 30
    PADL = gutter
    bararea = CW - PADL - PADR
    rowh = 48
    ploth = rowh * n
    W, H = CW, PADT + ploth + PADB

    def x(val):
        return PADL + (val / vmax) * bararea

    p = [_svg_open(W, H)]
    _add_x_grid(p, PADL, PADT, ploth, x, _grid_values(0, vmax), pre, suf)
    if target is not None:
        tx = x(target)
        p.append(f'<line x1="{tx:.1f}" y1="{PADT - 4}" x2="{tx:.1f}" y2="{PADT + ploth}" '
                 f'stroke="{CHART_COLORS[1]}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        p.append(f'<text x="{tx:.1f}" y="{PADT - 8:.1f}" font-size="10.5" fill="{CHART_COLORS[1]}" '
                 f'text-anchor="middle" font-weight="600">target {_fmt(target, pre, suf)}</text>')
    for i, d in enumerate(data):
        cy = PADT + i * rowh + rowh / 2
        bh = rowh * 0.56
        bw = x(d["value"]) - PADL
        p.append(f'<rect x="{PADL}" y="{cy - bh / 2:.1f}" width="{max(0, bw):.1f}" height="{bh:.1f}" '
                 f'rx="3" fill="{CHART_COLORS[0]}"/>')
        p.append(f'<text class="v-txt" x="{PADL - 10}" y="{cy + 4:.1f}" font-size="11.5" fill="{LABEL_INK}" '
                 f'text-anchor="end">{_html.escape(labels[i])}</text>')
        p.append(f'<text class="v-txt" x="{x(d["value"]) + 6:.1f}" y="{cy + 4:.1f}" font-size="11" '
                 f'fill="{LABEL_INK}" text-anchor="start" font-weight="700">'
                 f'{_fmt(d["value"], pre, suf)}</text>')
    p.append("</svg>")
    return "".join(p)


def _line_svg(spec):
    xs = spec["x"]
    series = spec["series"]
    pre, suf = spec.get("prefix", ""), spec.get("suffix", "")
    n = max(1, len(xs))
    rot = any(_est_w(l) > (CW * 0.82 / n) for l in xs)  # rotate crowded labels
    PADL, PADR, PADT = 54, 18, 28
    PADB = 64 if rot else 46
    plotw, ploth = CW - PADL - PADR, 230
    W, H = CW, PADT + ploth + PADB
    allv = [v for s in series for v in s["values"]]
    vmax = _nice(max(allv + [0]) or 1)
    vmin = min(0, min(allv + [0]))
    span = (vmax - vmin) or 1

    def x(i):
        return PADL + plotw * i / max(1, n - 1)

    def y(val):
        return PADT + ploth - ((val - vmin) / span) * ploth

    p = [_svg_open(W, H)]
    _add_y_grid(p, W, PADL, PADR, y, _grid_values(vmin, vmax), pre, suf)
    for i, lab in enumerate(xs):
        lx, ly = x(i), PADT + ploth + 16
        if rot:
            p.append(f'<text class="g-txt" x="{lx:.1f}" y="{ly:.1f}" font-size="11" fill="{AXIS_INK}" '
                     f'text-anchor="end" transform="rotate(-30 {lx:.1f} {ly:.1f})">'
                     f'{_html.escape(str(lab))}</text>')
        else:
            p.append(f'<text class="g-txt" x="{lx:.1f}" y="{ly:.1f}" font-size="11" fill="{AXIS_INK}" '
                     f'text-anchor="middle">{_html.escape(str(lab))}</text>')
    for si, s in enumerate(series):
        c = CHART_COLORS[si % len(CHART_COLORS)]
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s["values"]))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.5" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, v in enumerate(s["values"]):
            p.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{c}"/>')
    p.append("</svg>")
    svg = "".join(p)
    if len(series) > 1:
        chips = "".join(
            f'<span><i style="background:{CHART_COLORS[i % len(CHART_COLORS)]}"></i>'
            f'{_html.escape(str(s.get("label", "")))}</span>'
            for i, s in enumerate(series)
        )
        svg += f'<div class="legend">{chips}</div>'
    return svg


# ---- Optional vega-lite engine (richer chart types) -------------------------
# bar/line render with the built-in SVG above (no deps). area / scatter /
# grouped / stacked bars, or `"engine":"vega"`, route through vega-lite via
# vl-convert when installed — output is still inline, self-contained SVG.
_VEGA_TYPES = {"area", "scatter", "grouped", "stacked"}


def _vega_label_expr(pre, suf):
    pre_js, suf_js = json.dumps(str(pre)), json.dumps(str(suf))
    value = 'format(datum.value, ",")' if suf else "datum.label"
    return f"{pre_js} + {value} + {suf_js}"


def _to_vegalite(spec):
    t = spec.get("type", "bar")
    pre, suf = spec.get("prefix", ""), spec.get("suffix", "")
    # Vega SVGs are baked at build time and can't follow the runtime theme
    # toggle, so they use a transparent background (the themed card shows
    # through) and mid-tone axis colors that stay legible on light or dark.
    v_grid, v_axis = "rgba(140,150,165,.35)", "#8a94a0"
    val_axis = {"labelExpr": _vega_label_expr(pre, suf), "grid": True,
                "gridColor": v_grid, "domain": False, "labelColor": v_axis, "title": None}
    cat_axis = {"labelColor": v_axis, "domainColor": v_grid, "grid": False, "title": None}
    cfg = {"font": FONT, "view": {"stroke": None}, "background": "transparent",
           "axis": {"labelFontSize": 11, "titleFontSize": 11, "tickColor": v_grid},
           "legend": {"labelColor": v_axis, "titleColor": v_axis, "labelFontSize": 11},
           "range": {"category": CHART_COLORS}}
    base = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "width": CW - 90, "height": 230, "background": "transparent", "config": cfg}

    if t in ("bar", "grouped", "stacked"):
        if "x" in spec:  # multi-series: x labels + named series
            rows = [{"c": c, "v": v, "s": s.get("label", "")}
                    for s in spec["series"] for c, v in zip(spec["x"], s["values"])]
        else:
            rows = [{"c": d["label"], "v": d["value"], "s": d["label"]} for d in spec["series"]]
        long = any(_est_w(r["c"]) > 60 for r in rows)
        cat = {"field": "c", "type": "nominal", "sort": None, "axis": cat_axis}
        val = {"field": "v", "type": "quantitative", "axis": val_axis}
        enc = {("y" if long else "x"): cat, ("x" if long else "y"): val}
        if t in ("grouped", "stacked") or "x" in spec:
            enc["color"] = {"field": "s", "type": "nominal", "title": None}
            if t == "grouped":
                enc["xOffset" if not long else "yOffset"] = {"field": "s"}
            else:
                val["stack"] = True if t == "stacked" else None
        base.update({"data": {"values": rows}, "mark": {"type": "bar", "cornerRadius": 2}, "encoding": enc})
        return base

    if t in ("line", "area"):
        rows = [{"c": c, "v": v, "s": s.get("label", "")}
                for s in spec["series"] for c, v in zip(spec["x"], s["values"])]
        enc = {"x": {"field": "c", "type": "ordinal", "sort": None, "axis": cat_axis},
               "y": {"field": "v", "type": "quantitative", "axis": val_axis},
               "color": {"field": "s", "type": "nominal", "title": None}}
        mark = {"type": t, "point": True, "interpolate": "monotone"}
        if t == "area":
            mark["opacity"] = 0.55
        base.update({"data": {"values": rows}, "mark": mark, "encoding": enc})
        return base

    if t == "scatter":
        rows = [{"px": pt["x"], "py": pt["y"], "s": s.get("label", "")}
                for s in spec["series"] for pt in s["points"]]
        base.update({"data": {"values": rows},
                     "mark": {"type": "point", "filled": True, "size": 70},
                     "encoding": {"x": {"field": "px", "type": "quantitative", "axis": val_axis},
                                  "y": {"field": "py", "type": "quantitative", "axis": val_axis},
                                  "color": {"field": "s", "type": "nominal", "title": None}}})
        return base
    return None


def _vega_svg(spec):
    """Returns inline SVG via vl-convert, or None if vl-convert isn't installed."""
    try:
        import vl_convert as vlc
    except Exception:
        return None
    vl = _to_vegalite(spec)
    if vl is None:
        return None
    svg = vlc.vegalite_to_svg(json.dumps(vl))
    i = svg.find("<svg")
    svg = svg[i:] if i != -1 else svg
    return svg


def render_diagrams(d: pathlib.Path) -> dict:
    svgs = {}
    for f in sorted(d.glob("*.d2")):
        out = f.with_suffix(".svg")
        try:
            subprocess.run(
                ["d2", "--theme", "4", "--pad", "20", str(f), str(out)], check=True
            )
        except FileNotFoundError:
            sys.exit("d2 CLI not found. Install it: brew install d2")
        except subprocess.CalledProcessError as e:
            sys.exit(f"{f.name}: d2 render failed (exit {e.returncode}). Fix the .d2 file and rerun.")
        s = out.read_text()
        i = s.find("<svg")
        svg = s[i:] if i != -1 else s
        # Pin viewBox-only D2 roots to natural pixels; CSS can still shrink them.
        head = svg[:svg.find(">") + 1]
        vb = re.search(r'viewBox="[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"', head)
        if vb and "width=" not in head:
            nat_w, nat_h = float(vb.group(1)), float(vb.group(2))
            svg = svg.replace("<svg", f'<svg width="{nat_w:.0f}" height="{nat_h:.0f}"', 1)
            if nat_w > 900:
                print(
                    f"WARN: {f.name} renders {nat_w:.0f}px wide — text will shrink. "
                    f"Use `direction: down` and shorter labels.",
                    file=sys.stderr,
                )
        svgs[f.stem] = svg
    return svgs


_MIME = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif",
         "svg": "svg+xml", "webp": "webp"}


def inline_images(body: str, base: pathlib.Path) -> str:
    """Base64-inline local images; leave http(s):// and data: sources untouched."""
    def repl(m):
        full, src = m.group(0), m.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return full
        path = pathlib.Path(src)
        if not path.is_absolute():
            path = base / src
        if not path.exists():
            print(f"NOTE: <img> src not found: {src}", file=sys.stderr)
            return full
        mime = _MIME.get(path.suffix.lstrip(".").lower(), "png")
        b64 = base64.b64encode(path.read_bytes()).decode()
        start, end = m.start(2) - m.start(0), m.end(2) - m.start(0)
        return f"{full[:start]}data:image/{mime};base64,{b64}{full[end:]}"

    return re.sub(r"""<img\b[^>]*\bsrc\s*=\s*(['"])(.*?)\1[^>]*>""", repl, body)


def render_charts(d: pathlib.Path) -> dict:
    out = {}
    for f in sorted(d.glob("*.json")):
        spec = json.loads(f.read_text())
        kind = spec.get("type", "bar")
        want_vega = spec.get("engine") == "vega" or kind in _VEGA_TYPES
        if want_vega:
            svg = _vega_svg(spec)
            if svg is None:
                if kind in _VEGA_TYPES:
                    sys.exit(f"{f.name}: type {kind!r} needs the vega-lite engine. "
                             f"Install it (`pip install vl-convert-python`) or use 'bar'/'line'.")
                print(f"NOTE: {f.name}: vl-convert not installed; using built-in renderer",
                      file=sys.stderr)
                svg = _bar_svg(spec) if kind == "bar" else _line_svg(spec)
            out[f.stem] = svg
        elif kind == "bar":
            out[f.stem] = _bar_svg(spec)
        elif kind == "line":
            out[f.stem] = _line_svg(spec)
        else:
            sys.exit(f"{f.name}: unknown chart type {kind!r} "
                     f"(built-in: 'bar'/'line'; vega: {sorted(_VEGA_TYPES)})")
        # A label too long for even the horizontal gutter is the one case the
        # layout can't fully rescue — flag it so the author shortens it.
        for lab in [str(s.get("label", "")) for s in spec.get("series", [])] + \
                   [str(x) for x in spec.get("x", [])]:
            if len(lab) > 34:
                print(f"WARN: {f.name}: label {lab!r} is very long — shorten it "
                      f"or move detail to the caption.", file=sys.stderr)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True, help="HTML body fragment")
    ap.add_argument("--diagrams", help="dir of *.d2 files (optional)")
    ap.add_argument("--charts", help="dir of *.json chart specs (optional)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    body = pathlib.Path(a.body).read_text()
    if a.diagrams:
        for name, svg in render_diagrams(pathlib.Path(a.diagrams)).items():
            token = f"%%{name}%%"
            if token not in body:
                print(f"NOTE: {token} not referenced in body", file=sys.stderr)
            body = body.replace(token, svg)
    if a.charts:
        for name, svg in render_charts(pathlib.Path(a.charts)).items():
            token = f"@@{name}@@"
            if token not in body:
                print(f"NOTE: {token} not referenced in body", file=sys.stderr)
            body = body.replace(token, svg)

    body = inline_images(body, pathlib.Path(a.body).resolve().parent)

    html = (
        SHELL.replace("%%CSS%%", CSS)
        .replace("%%JS%%", JS)
        .replace("%%TITLE%%", a.title)
        .replace("%%BODY%%", body)
    )
    pathlib.Path(a.out).write_text(html)
    print(f"wrote {a.out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
