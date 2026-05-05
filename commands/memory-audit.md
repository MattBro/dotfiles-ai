---
description: Audit auto-memory and CLAUDE.md for staleness, duplicates, dead links, and overlap. Reports findings and pauses for approval before any deletion.
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Memory Audit

Review the user's memory system and `CLAUDE.md` files for hygiene issues. **Never auto-delete anything** — surface findings, wait for approval.

The memory directory is per-project under `~/.claude/projects/<project-slug>/memory/`. The global `CLAUDE.md` is at `~/.claude/CLAUDE.md`.

```bash
PROJECT_SLUG=$(echo "$PWD" | sed 's|/|-|g')
MEMORY_DIR="$HOME/.claude/projects/${PROJECT_SLUG}/memory"
GLOBAL_CLAUDE_MD="$HOME/.claude/CLAUDE.md"
```

If your project slug uses a different convention, adjust the path.

## 1. Context footprint

Report lines in auto-loaded files:

```bash
wc -l "$GLOBAL_CLAUDE_MD" "$MEMORY_DIR/MEMORY.md"
```

Only `CLAUDE.md` and `MEMORY.md` (the index) are auto-loaded. Individual memory files are loaded on demand. Flag if combined auto-load exceeds ~500 lines — that's usually the point where trimming helps.

## 2. MEMORY.md integrity

```bash
cd "$MEMORY_DIR"

# Files not referenced in MEMORY.md (orphans)
for f in *.md; do
  [ "$f" != "MEMORY.md" ] && ! grep -q "$f" MEMORY.md && echo "ORPHAN: $f"
done

# Links pointing to files that don't exist (dead links)
grep -oE '\(([a-z_]+\.md)\)' MEMORY.md | sed 's/[()]//g' | while read link; do
  [ ! -f "$link" ] && echo "DEAD LINK: $link"
done
```

## 3. Stale memories (point to things that no longer exist)

Memory files frequently reference specific paths, functions, or dirs. Check each:

```bash
grep -rn -E "$HOME/[a-zA-Z0-9_-]+|~/[a-zA-Z0-9_-]+" "$MEMORY_DIR/" --include="*.md" | grep -v MEMORY.md
```

For each path mentioned: verify the dir/file still exists. If not, the memory is stale — surface it.

Also flag memories dated more than ~60 days ago that mention volatile things (branches, in-flight PRs, specific people's ongoing work).

## 4. Duplicate / near-duplicate memories

Two signals:

```bash
# Names that look alike
ls "$MEMORY_DIR/" | sort

# Descriptions that overlap (grep frontmatter descriptions)
grep -h "^description:" "$MEMORY_DIR/"*.md
```

If two files cover the same topic, read both and propose merging. Don't merge automatically.

## 5. CLAUDE.md vs memory overlap

Scan the global `CLAUDE.md` for sections that duplicate a memory file. Common offenders:

- PR workflow sections (often superseded by `/pr-ready` + feedback memories)
- Commit message guidance (can live in memory, not CLAUDE.md)
- Tool-specific tips that apply to only one repo

```bash
grep -n "^#" "$GLOBAL_CLAUDE_MD"  # section headings
```

For each section, ask: is there a memory file that already covers this? If yes, propose trimming `CLAUDE.md` and pointing to the memory, or vice versa.

## 6. Report

Present findings in this shape:

```
## Memory audit

Context size: CLAUDE.md N lines + MEMORY.md M lines = K lines auto-loaded

Integrity: [clean | N orphans + M dead links — list them]

Stale references:
  - <file>: mentions <thing> which no longer exists
  - ...

Duplicates / near-duplicates:
  - <file A> and <file B> both cover <topic>

CLAUDE.md overlap:
  - Section "<heading>" overlaps with <memory file>

Recommended actions:
  1. Delete <file>
  2. Merge <A> into <B>
  3. Trim CLAUDE.md section "<heading>" to point to <memory>
```

Ask the user which actions to take. Only act on the ones they approve.

## Rules

- Never delete a memory file without explicit approval.
- Never trim `CLAUDE.md` without showing the diff first.
- If a memory is merely *old* (>30 days) but still accurate, don't flag it — age alone isn't a problem.
- If two memories look similar but are actually about different topics (e.g. "dev server" vs "test prereqs" vs "sandboxes"), leave them alone and note that you considered them.
- After any deletion, update `MEMORY.md` to remove the link.
