---
name: unambiguous-agent-text
description: >-
  Rewrites agent-facing English so a downstream model cannot misparse it: one
  meaning per word, active voice, simple tense, one instruction per sentence.
  Based on ASD-STE100 Simplified Technical English.

  Use when writing or reviewing text whose reader is a machine with no
  back-channel: MCP/tool descriptions, skill `description:` frontmatter, system
  prompts, sub-agent task prompts, error messages a model will parse, and
  inter-agent instructions.

  ALSO use for PostHog PR descriptions: reviewers asked for this style
  (posthog#79254). DO NOT use for Slack (use slack-smart-brevity), for other
  prose written to humans, or for code (use /simplify). Never triggers on the
  bare phrase "simplify this".
---

# Unambiguous Agent-Facing Text

ASD-STE100 (Simplified Technical English) is a controlled language the aerospace
industry built so a maintenance technician on a tarmac cannot misread an
instruction. The technician has no author to call. Ambiguity is unrecoverable,
so the standard removes the two things that create it: words with more than one
meaning, and sentences with more than one possible structure.

A model parsing a tool description is in the same position. It cannot ask "did
you mean X or Y?" It picks one reading and acts. This skill applies the STE
discipline to that reader.

## When to Use

Reach for this when the reader is a machine and a misparse has a cost:

- MCP tool descriptions and parameter descriptions
- Skill `description:` frontmatter (this is the text that decides whether a
  skill fires at all, so ambiguity there is expensive)
- System prompts and sub-agent task prompts
- Error messages that an agent, not a human, will act on
- Inter-agent instructions and handoff notes
- Text headed for a translation pipeline or a non-native English reader

## When Not to Use

| Situation | Use instead |
|---|---|
| Slack messages, threads, announcements | `slack-smart-brevity` |
| Code refactoring, dead code, duplication | `/simplify` |
| Docs and human-facing prose, generally | nothing; write normally |
| PR descriptions in PostHog repos | USE this skill; Fernando asked for STE-style PR bodies (posthog#79254) and reviews most growth PRs |
| Marketing, persuasive, or narrative copy | nothing; STE is deliberately flat |

STE is flat and literal on purpose. Applying it to text where voice or nuance
carries the point makes the text worse, not clearer.

## Core Rewrite Rules

| Rule | Do | Don't |
|---|---|---|
| One word, one meaning | Pick one verb per action and reuse it everywhere. Always "check", never rotate "check" / "verify" / "confirm" for the same action | Rotate synonyms for one idea across a document |
| One part of speech per word | "Apply oil to the valve" (oil = noun) | "Oil the valve" (oil = verb), if the word is fixed as a noun elsewhere |
| Active voice | "The agent deletes the file." | "The file is deleted." Passive is allowed only in descriptive text where the actor is genuinely unknown |
| Simple tenses only | "We received the report." | "We have received the report." No present perfect, past perfect, or auxiliary stacking |
| One instruction per sentence | "Open the file. Read line 3." | "Open the file and read line 3, then check if it matches." |
| Sentence length | 20 words or fewer for instructions, 25 or fewer for descriptions | Long compound or subordinate-clause sentences |
| Noun clusters | 3 words maximum ("fuel pump valve") | 4+ word noun stacks ("high pressure fuel pump inlet valve assembly") |
| No ellipsis | Keep subject, verb, and article explicit even if it runs longer | Drop words to save space. "Files not backed up will be lost" hides which files |
| One topic per paragraph | 6 sentences or fewer | Multi-topic paragraphs |
| Lists for sequences | Numbered or bulleted list for 3+ steps or conditions | A sequence buried in one prose sentence |
| Hedge stacking | State the condition once, plainly | "may have occurred", "could possibly be caused by", "it is worth noting that" |
| Domain terms | Keep necessary technical nouns and verbs, define each once | Undefined jargon |

## Process

1. Read the input once for meaning. Do not rewrite before you know what the text
   must still say afterward.
2. Walk it sentence by sentence. Flag every violation: word ambiguity, tense,
   voice, length, ellipsis, noun stacking, hedge stacking.
3. Rewrite each flagged sentence. Preserve every fact, condition, number, and
   scope qualifier exactly.
4. If a rewrite would drop required precision, keep the longer phrasing and flag
   the trade-off. Do not silently simplify away a safety condition or an
   exception.
5. Output the before/after table.
6. If the input already complies, say so. Do not force changes onto clean text.

## Output Format

```markdown
| Rule violated | Original | Rewritten |
|---|---|---|
| Present perfect tense | "We have received your request." | "We received your request." |
| Noun cluster (4+ words) | "the agent task queue priority handler" | "the handler that sets task-queue priority" |
```

Follow the table with one line on anything you deliberately left alone, and why.
Usually the reason is that simplifying it would lose required precision.

## House Rules

Output from this skill lands in Matt's repos, so it inherits his writing rules:

- **No em dashes.** Rewrite the sentence. Do not substitute a spaced hyphen.
- No invented compound jargon and no metaphors standing in for a technical claim.
- No trailing period after a file path.

These sit on top of the STE rules, not instead of them.

## Boundaries

**Will:**

- Rewrite ambiguous or dense agent-facing English into short, single-meaning,
  active-voice sentences.
- Name the exact rule a sentence violates before rewriting it.
- Preserve every fact, condition, and scope qualifier in the original.
- Suggest a one-line glossary entry for a domain term that has to stay.

**Will not:**

- Reproduce ASD's official ~900-word approved dictionary from memory. This skill
  applies the underlying principle (pick the plainest, most common word and use
  it the same way every time) rather than checking against a fixed word list.
- Touch Slack drafts, general human-facing prose, or code. Exception: PostHog PR descriptions, which reviewers asked to have in this style.
- Drop a safety condition, exception, or scope qualifier to shorten a sentence.
  It flags the trade-off instead.
- Claim aerospace-grade STE compliance. For real maintenance documentation,
  download the standard from https://www.asd-ste100.org/ and check word by word
  against the real dictionary.

## Additional Resources

- `references/writing-rules.md` for the 9 rule sections, the dictionary
  structure, and citations to the official standard.
- `examples/before-after.md` for worked examples, including MCP tool
  descriptions and skill frontmatter.

## Attribution

Adapted from [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)
(MIT, Copyright (c) 2026 Dustin Yuchen Teng). Scope narrowed to machine-read
text, trigger changed to avoid colliding with `/simplify`, house style rules
added, and the examples corrected.
