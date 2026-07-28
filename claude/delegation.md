# Sonnet Delegation

**Implementation should always be parallelized with sub-agents running Sonnet.** Split the work into independent chunks, spawn sub-agents in parallel via the Agent tool with `model: "sonnet"`, and have each sub-agent implement its chunk directly.

- Never shell out to `codex exec` or use the Codex plugin — Sonnet sub-agents replace both.
- Give each sub-agent full context up front: exact file paths, conventions to copy, facts already verified, and the verification commands to run (tests, typecheck, import validation).
- Sub-agents must not commit — leave changes in the working tree for review.
- **Reviews**: a read-only sub-agent with an adversarial task prompt.
- Parallel chunks in one repo: share a single worktree only when chunks own disjoint files; otherwise give each agent its own worktree.
