# Delegation

**Bounded implementation should be parallelized with sub-agents running Sonnet.** Split the work into independent chunks, spawn sub-agents in parallel via the Agent tool with `model: "sonnet"`, and have each sub-agent implement its chunk directly after the design decisions are fixed.

- Never shell out to `codex exec` or use the Codex plugin — Sonnet sub-agents replace both.
- Give each sub-agent full context up front: exact file paths, conventions to copy, facts already verified, and the verification commands to run (tests, typecheck, import validation).
- Sub-agents must not commit — leave changes in the working tree for review.
- **Design decisions**: schema ownership, authentication boundaries, billing behavior, and external protocols stay with the strongest available reasoning model. Do not let an implementation agent infer them from existing code.
- **Reviews**: use a fresh strongest-available read-only agent for design integrity and a separate adversarial agent for implementation defects. Give the design reviewer the original request or specification rather than the implementation narrative.
- Parallel chunks in one repo: share a single worktree only when chunks own disjoint files; otherwise give each agent its own worktree.
