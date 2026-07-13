---
name: explainer-video
description: >-
  Build a scene-based visual explainer: an interactive HTML motion deck
  (default) or a narrated mp4 (kokoro TTS + ffmpeg). Fixed-map style: boxes
  never move, scenes toggle arrows/highlights via CSS classes. Use when the
  user asks for a video, explainer, walkthrough, animated status report, or
  dynamic/interactive presentation of a system, plan, or project status.
---

# Explainer videos and motion decks

Two output modes sharing one authoring model. Default to the **motion deck**
(interactive HTML) unless the user explicitly needs an .mp4 file to drop into
Slack or a doc.

Authoring model for both: ONE master layout of absolutely-positioned boxes
that NEVER move between scenes. Each scene is a named state (a CSS class on
`<body>`) that toggles arrow colors, opacity, glow, and captions. Viewers keep
their mental map; only the delta lights up.

## Style rules (both modes)

- Boxes never move or resize across scenes. Arrows/edges appear, dim, or
  recolor; nothing else changes position.
- Consistent color semantics with a persistent on-screen legend. Reuse
  established meanings across decks in the same project (enrichment decks:
  green = data toward Clay, orange = from Clay, blue = ours/in-house,
  purple = facade/bridge, gray dashed = off/dead).
- Glow (box-shadow pulse) marks the ONE thing that changed this scene.
- Captions: max 12 words. No em dashes (use colons). Plain sentences.
- One idea per scene. If a scene needs two glows, split it.
- 1920x1080 canvas geometry (16:9); motion decks wrap it in a responsive
  scaler (`transform: scale()` from a fixed 1920x1080 stage).

## Mode 1: interactive motion deck (default)

A single self-contained .html file. No CDN, no external assets (Artifact CSP
blocks them). Publish with the Artifact tool; load the `artifact-design`
skill first, and `dataviz` if any scene contains a chart.

Structure:

```html
<div id="stage">            <!-- fixed 1920x1080, scaled to fit viewport -->
  <div class="box" id="clay" style="left:...;top:...">Clay</div>
  <svg id="edges">…</svg>   <!-- all arrows for all scenes, toggled by class -->
  <div class="legend">…</div>
</div>
<div id="hud">              <!-- outside the stage -->
  <div id="caption"></div>  <!-- current scene caption -->
  <div id="dots"></div>     <!-- progress dots, clickable -->
  <button id="play"></button>
</div>
```

Scene machine (the whole engine, keep it this small):

```js
const scenes = [
  { id: 's1', caption: 'Today: every signup flows to Clay.', dwell: 6000 },
  { id: 's2', caption: 'Step 1: our pipeline writes the same keys.', dwell: 7000 },
  // ...
];
let i = 0, timer = null;
function show(n) {
  i = (n + scenes.length) % scenes.length;
  document.body.className = scenes[i].id;
  caption.textContent = scenes[i].caption;
  dots.querySelectorAll('span').forEach((d, j) => d.classList.toggle('on', j === i));
}
function playpause() {
  if (timer) { clearInterval(timer); timer = null; }
  else timer = setInterval(() => show(i + 1), scenes[i].dwell);
}
addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') show(i + 1);
  if (e.key === 'ArrowLeft') show(i - 1);
  if (e.key === 'p') playpause();
});
show(0);
```

Scene styling: everything is driven by `body.s2 .edge-x { … }` rules. Give
every edge/box transition `transition: opacity .6s, stroke .6s, box-shadow .6s`
so scene changes animate instead of snapping. Draw ALL edges in one SVG and
default them to `opacity:.12`; scenes raise the relevant ones. Animated flow
on active edges: `stroke-dasharray` + a `dash` keyframe loop. Glow:
`@keyframes pulse` on box-shadow, applied per scene
(`body.s3 #newbox { animation: pulse 1.6s infinite }`).

Optional per-scene side panel (status decks): a fixed-position card whose
content swaps per scene (`body.s4 .panel-s4 { display:block }`) for bullets,
KPI numbers, or a mini chart. Keep the map on the left, panel on the right;
neither moves.

Data/status decks: scenes are chapters (where we are, what shipped, what's
next, risks). Same engine; the "map" can be a timeline or pipeline diagram.
Numbers in panels come from verified sources only; cite nothing you didn't
check.

Theme: support light and dark (`@media (prefers-color-scheme: dark)` plus
`:root[data-theme=…]` overrides) since Artifacts render in the viewer theme.

Quality gate before shipping: step through EVERY scene (Playwright/Chrome
screenshot per scene, or at minimum read the scene CSS against the checklist):
boxes identical across scenes, exactly one glow per scene, caption under 12
words, legend readable in both themes, autoplay loops cleanly.

## Mode 2: narrated mp4 (kokoro + ffmpeg, fully local)

Use when the deliverable must be a video file. Recipe proven Jul 2026 (three
enrichment explainers); templates and a worked example live in
`~/dev/.claude/docs/enrichment/video-pipeline/` (master-fixed-map-v2.html,
tts_batch.py, xfade-filter-example.txt).

1. Narration: `narration.md`, one heading per scene describing the visual
   state; the prose under it is the TTS script for that scene.
2. Slides: one `master.html` (1920x1080). Render each scene by setting the
   scene class, then:
   `~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-mac-arm64/headless_shell
    --headless --disable-gpu --screenshot=sceneN.png --window-size=1920,1080
    file://.../sceneN.html`
3. TTS: kokoro-onnx, local. venv: `uv venv --python 3.12 && uv pip install
   kokoro-onnx soundfile`. Voice `af_heart`. Model files (~340MB, re-download
   if missing):
   `https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx`
   `https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin`
4. Assembly: per segment
   `ffmpeg -loop 1 -i scene.png -i seg.wav -c:v libx264 -tune stillimage
    -pix_fmt yuv420p -af apad=pad_dur=0.5 -shortest seg.mp4`,
   then 0.5s `xfade` chain with `acrossfade` for audio.
5. Quality gates: read every scene PNG (legibility, positions identical),
   `ffprobe` total duration, spot-check a frame at each segment midpoint,
   audio RMS at two boundaries, no em dashes in narration.

## Picking scenes

Write the scene list BEFORE any HTML: one line per scene = caption + what
lights up. If a caption needs "and", split the scene. Status reports usually
land at 6-10 scenes; system explainers at 4-8. Show the scene list to the
user only if the request was ambiguous; otherwise build.
