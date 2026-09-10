# Delegation

Parallelize implementation with sub-agents when the work has at least two genuinely independent chunks. Spawn them in parallel via the Agent tool and have each implement its chunk directly.

- Give each sub-agent full context up front: exact file paths, conventions to copy, facts already verified, and the verification commands to run (tests, typecheck, import validation).
- Let sub-agents inherit the active model unless the task itself calls for a specific one.
- Sub-agents must not commit. Leave changes in the working tree for review.
- **Reviews**: a read-only sub-agent with an adversarial task prompt.
- Parallel chunks in one repo: share a single worktree only when chunks own disjoint files; otherwise give each agent its own worktree.
- Keep sequential or tightly coupled work in the primary agent instead of forcing artificial delegation.
