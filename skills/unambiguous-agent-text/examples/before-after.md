# Before / After Examples

## Part 1: The Base Rules

Paraphrased illustrations of ASD-STE100 rules, drawn from the public secondary
sources in `references/writing-rules.md`. They are not quotes from the standard.

| Rule | Before | After | Why |
|---|---|---|---|
| One word, one meaning | Section 2: "Verify the connection." Section 5: "Check the connection." Section 9: "Confirm the connection." | All three read "Check the connection." | Three near-synonyms for one action force the reader to guess whether they mean different things. Pick one verb and reuse it. Note that the rewrite keeps all three sentences; normalizing vocabulary never means deleting content. |
| One part of speech per word | "Oil the valve." | "Apply oil to the valve." | If "oil" is fixed as a noun, using it as a verb breaks the one-word-one-role guarantee. |
| Precise verb meaning | "Follow the safety instructions." | "Obey the safety instructions." | "Follow" can mean "come after" or "obey". STE picks the unambiguous one. |
| Simple tense only | "We have received the technical reports from HQ." | "We received the technical reports from HQ." | Present perfect adds a second parse (received, and still in effect now?) that simple past avoids. |
| No ellipsis | "Files not backed up will be lost." | "The system deletes any file that it did not back up." | The original hides both the actor and which files. |

## Part 2: Agent-Facing Text

These are the cases this skill actually exists for.

### Example A: MCP tool description

**Before:**

> This tool will attempt to synchronize state across the various backends that
> have been configured, and if a conflict is detected it may resolve it
> automatically depending on the strategy that has been set, or otherwise it
> will surface the conflict for manual review.

**Violations:**

- Two instructions in one sentence (sync, then resolve or surface).
- Present perfect and modal stacking: "have been configured", "may resolve",
  "has been set". Compounding hedges compound ambiguity.
- 55 words, over the 25-word descriptive cap.

**After:**

> The tool synchronizes state across the configured backends. If it finds a
> conflict, it reads the current strategy. If the strategy allows automatic
> resolution, the tool resolves the conflict. If not, the tool reports the
> conflict for manual review.

### Example B: Tool parameter description

**Before:**

> Optional filter which, when provided, restricts results to the given project,
> though note that if the caller's token is project-scoped this may already be
> implied.

**Violations:**

- Hedge stacking: "though note that", "may already be implied".
- The reader cannot tell whether passing the parameter is harmful, redundant, or
  required.
- Ellipsis: the actor doing the restricting is dropped.

**After:**

> Restricts results to one project. Give a project ID. If the token is already
> scoped to one project, the server ignores this parameter.

### Example C: Skill `description:` frontmatter

Frontmatter is the highest-value target for this skill. It is the only text the
model sees when it decides whether to load the skill at all.

**Before:**

> Helps with various aspects of database work including migrations and schema
> changes, and can also be used for query performance investigations when
> needed.

**Violations:**

- "various aspects", "when needed", "can also be used": no firm trigger.
- Three unrelated jobs in one sentence.
- No statement of when the skill does not apply, so it fires on everything
  containing the word "database".

**After:**

> Writes and reviews Django migrations for the PostHog repo. Use when the task
> creates, edits, or reverts a migration file. Do not use for query performance
> work or for raw schema inspection.

### Example D: Error message a model will act on

**Before:**

> An error may have occurred while processing your request due to a possible
> mismatch in the expected data format, which could be caused by an outdated
> client version.

**Violations:**

- Passive voice with no actor: "an error may have occurred".
- Double hedge: "may have occurred", "could be caused".
- One sentence carrying two separate claims (the failure, and its cause).

**After:**

> The request failed. The data format did not match what the server expected. An
> outdated client is the most common cause. Check the client version.

### Example E: Sub-agent task prompt

**Before:**

> Once the upstream job has completed and assuming no errors were raised, the
> downstream agent should proceed to consume the output artifact, though it is
> worth noting that partial artifacts are sometimes produced under timeout
> conditions.

**Violations:**

- Present perfect ("has completed") and stacked subordinate clauses.
- One sentence, three separate facts: the wait condition, the action, and an
  edge case.
- 42 words, over the 20-word instruction cap.

**After:**

> Wait for the upstream job to finish with no errors. Then read the output
> artifact. Warning: a timeout can produce a partial artifact. Check that the
> artifact is complete before you use it.

## Example F: Text this skill leaves alone

**Input:**

> Never fix a failing size-budget check by increasing the budget. The budgets
> exist to stop size degrading in tiny increments, and bumping the limit
> whenever it trips defeats the check.

**Verdict:** already compliant. Active voice, simple tense, one instruction,
both sentences under the cap. Report it as clean rather than churning it.

## How to Read These

Part 1 gives the rules. Part 2 shows the transfer: the same discipline that
protects an airline mechanic from a misread torque spec protects a model from a
misread tool description. The reader in both cases cannot ask a follow-up
question.
