# sbtdd — Finalization Reference

This reference covers the git-status verification, the final checklist, pending-change
resolution, and the handoff to `superpowers:finishing-a-development-branch`.
For commit prefix conventions, see `CLAUDE.local.md` §5. For verification
commands, see `CLAUDE.local.md` §0.1.

---

## 1. Clean Git-Status Verification

Before invoking `superpowers:finishing-a-development-branch`, the working tree
must be clean with respect to the plan's scope.

```bash
git status     # No modified, staged, or untracked files within plan scope
```

### Approval Criteria

- **No modified or staged files** related to any plan task. Every in-scope
  change must already be in an atomic commit.
- **No untracked files** that should be part of the plan. New files required
  by the plan (modules, tests, configs) must be committed. New files outside
  the plan (artifacts, logs, exploration) must be in `.gitignore` or removed.
- **Permitted untracked files** are only those the project already documents
  as intentionally ignorable (in `CLAUDE.md` under the artifact-ignored or
  `.gitignore` conventions section). If `CLAUDE.md` does not document an
  untracked artifact, it is **not** accepted — add it to `.gitignore` or remove
  it before finalizing.

If `git status` shows pending changes within plan scope, the plan is **not**
complete — see Section 3 (Pending-Change Resolution) below.

---

## 2. Final Checklist

All items must be verified by the agent before invoking
`superpowers:finishing-a-development-branch`.

- [ ] All plan tasks marked `[x]` in `planning/claude-plan-tdd.md`
- [ ] `.claude/session-state.json` reports `current_task_id: null`, `current_task_title: null`, and `current_phase: "done"`
- [ ] All verification commands in `CLAUDE.local.md` §0.1 pass without warnings
- [ ] `git status` clean with respect to plan scope (Section 1 criteria above)
- [ ] `sbtdd/spec-behavior.md` and `planning/claude-plan-tdd.md` reflect the final state
- [ ] `superpowers:requesting-code-review` executed and all findings resolved (Loop 1 clean to go)
- [ ] **MAGI gate approved** — `magi:magi` verdict ≥ `GO WITH CAVEATS`; if the verdict was `GO WITH CAVEATS`, all structural *Conditions for Approval* applied before merge (see `references/review-gates.md` §5)
- [ ] Commits follow the prefix conventions in `CLAUDE.local.md` §5 (atomic, correct prefix per context: TDD phase close, task close, review fix mini-cycles)
- [ ] `CLAUDE.md` updated if any durable architectural decisions were made during implementation

Only when every checklist item is checked invoke `superpowers:finishing-a-development-branch`.
The skill guides the decision between direct merge, pull request, or branch cleanup.

---

## 3. Pending-Change Resolution

If `git status` reports changes related to plan scope, resolve before closing:

1. Identify which plan task the pending change belongs to.
2. Return to that task's TDD cycle: verify the phase, run
   `superpowers:verification-before-completion`, commit atomically with the
   correct prefix.
3. If the change does not correspond to any plan task, it is **scope creep**:
   revert it or move it to a separate plan. Do not commit it under the current
   plan.

No pending changes may be bundled into a catch-all commit to clear the status.
Each commit must be atomic and belong to a specific TDD phase or task close.
