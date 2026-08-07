# ASD-STE100 Writing Rules: Summary and Sources

This file paraphrases the public description of ASD-STE100 (Simplified Technical
English). It summarizes rule *categories*. It does not reproduce the standard's
text or its approved-word dictionary.

## What ASD-STE100 Is

ASD-STE100 is a controlled natural language, first released in 1986 as AECMA
Document PSC-85-16598 by what is now ASD, the AeroSpace and Defense Industries
Association of Europe. European airlines asked for it because most of their
maintenance staff were non-native English speakers, and a misread instruction on
an aircraft can kill people. The Simplified Technical English Maintenance Group
(STEMG) maintains it. It has been free to download since Issue 6 (2013). The
upstream skill cites Issue 9 (January 2025) as current; treat that edition
number as unverified and check the official site before relying on it.

## Structure

- **53 writing rules across 9 sections** covering word choice, grammar, sentence
  structure, and style.
- **A dictionary** of roughly 900 approved words. Each word is restricted to one
  meaning and one part of speech. Roughly 1,200 more words are listed as words
  to avoid, each with a suggested replacement.
- **A terminology allowance.** An organization may define its own dictionary of
  approved technical nouns and verbs beyond the base list, for domain vocabulary
  the base dictionary cannot cover.

## Rule Categories

### Word choice

- Use an approved word only in its approved meaning and part of speech.
- Map each word to exactly one meaning. Do not rely on context to disambiguate a
  word that carries several dictionary senses.
- Prefer the plainer, shorter, more common word over a formal or rare synonym.

### Verb forms

- Permitted: infinitive, imperative, simple present, simple past, simple future,
  and past participle used only as an adjective.
- Not permitted: present perfect, past perfect, and other compound or auxiliary
  constructions. Write "we received", not "we have received".
- "-ing" forms are permitted only as a technical noun or as part of one, never
  as a verb form.

### Voice

- Active voice is required for procedures and instructions.
- Passive voice is allowed in descriptive text only, and only when the actor is
  genuinely unknown or irrelevant to the reader.

### Sentence structure

- One instruction per sentence.
- 20 words maximum per sentence for procedures and instructions. 25 maximum for
  descriptive text.
- Do not omit a verb, subject, or article to shorten a sentence. The standard
  warns that this creates ambiguity rather than clarity.
- Cap noun clusters at 3 words.

### Paragraph and document structure

- One topic per paragraph.
- 6 sentences maximum per paragraph.
- Use a numbered or bulleted list for a sequence, a set of conditions, or a
  complex enumeration. Do not bury it in prose.

### Safety instructions

- A safety-critical instruction opens with the command or the condition. It is
  never buried mid-sentence.

## Why This Transfers to Agent-Facing Text

STE was built for a reader who cannot ask a follow-up question: a technician
working from a manual with no author to call. A model parsing a tool
description, a system prompt, or another agent's output is in that same
position. There is no back-channel to resolve "does this passive-voice sentence
mean the caller does X, or the callee does X?" The model commits to one reading
and acts on it.

The transfer is a reasoned analogy, not a measured result. No published
evaluation shows STE-styled prompts improve model behavior. Treat this skill as
a clarity discipline that is cheap to apply and hard to make things worse with,
not as a proven accuracy lever.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100: About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe: Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English (Wikipedia)](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe: ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary: Simplified Technical English (STE)](https://skybrary.aero/articles/simplified-technical-english-ste)
- [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill), the
  MIT-licensed upstream this skill is adapted from
