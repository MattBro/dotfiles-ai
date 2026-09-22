# Codex Delegation

Parallelize implementation with Codex subagents when the work has at least two genuinely independent chunks. Have each subagent implement its chunk directly.

- Give each subagent the exact files it owns, the relevant conventions, facts already verified, and the commands it must run.
- Let subagents inherit the active model unless the task itself requires a specific model.
- Subagents must not commit. Leave changes in the working tree for review.
- Use a read-only subagent for adversarial review.
- In one repository, share a worktree only when chunks own disjoint files. Otherwise, give each subagent its own worktree.
- Keep sequential or tightly coupled work in the primary agent instead of forcing artificial delegation.
