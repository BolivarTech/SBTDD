# sbtdd — Routing Reference

This reference describes how the orchestrator determines which phase of the
SBTDD workflow to enter at session start, how authority is resolved across
the three state-carrying artifacts, and how drift between them is detected
and recovered.

---

## 1. State-Detection Decision Table

The orchestrator inspects artifacts in the project tree to choose the correct
entry point. Evaluate rows top-to-bottom; take the first matching row.

| Condition | Phase entered | Action |
|-----------|---------------|--------|
| `sbtdd/spec-behavior-base.md` absent or empty | — | **Stop and request** the file from the user before proceeding |
| `sbtdd/spec-behavior-base.md` present; `sbtdd/spec-behavior.md` absent | Specification | Invoke `superpowers:brainstorming` using `spec-behavior-base.md` as input |
| `sbtdd/spec-behavior.md` present; `planning/claude-plan-tdd-org.md` absent | Planning | Invoke `superpowers:writing-plans` to generate `claude-plan-tdd-org.md` |
| `planning/claude-plan-tdd-org.md` present; `planning/claude-plan-tdd.md` absent or not yet approved | Plan gate (Checkpoint 2) | Run MAGI review against spec + plan; iterate until `claude-plan-tdd.md` is approved |
| Approved `planning/claude-plan-tdd.md` exists; `session-state.json` present with `current_phase` ≠ `"done"` | Execution — resume | Read `session-state.json`; resume from `current_task_id` / `current_phase` |
| Approved `planning/claude-plan-tdd.md` exists; `session-state.json` absent | Execution — start | Create `session-state.json` from plan (first `[ ]` task, phase `"red"`) |
| All plan tasks `[x]` and `session-state.json` reports `current_phase: "done"` | Pre-merge review | Run Loop 1 (`superpowers:requesting-code-review`) then Loop 2 (`magi:magi`) |
| Pre-merge review clean (Loop 1 clean-to-go + Loop 2 ≥ GO WITH CAVEATS) | Finalization | Execute finalization checklist — see `references/finalization.md` |

### Canonical artifact names

| Artifact | Canonical path |
|----------|----------------|
| Spec base | `sbtdd/spec-behavior-base.md` |
| Refined spec | `sbtdd/spec-behavior.md` |
| Original plan | `planning/claude-plan-tdd-org.md` |
| Approved plan | `planning/claude-plan-tdd.md` |
| Runtime state | `.claude/session-state.json` |

---

## 2. Authority Order

Three artifacts carry state about the same TDD progression. When they contain
redundant or conflicting information, the following canon order applies:

```
1. Git is canon of the past   — commits are immutable; the timeline is truth
2. State file is canon of the present — the sole source of "now" during execution
3. Plan is canon of the future + documentary record — what remains + what completed
```

This maps directly to `CLAUDE.local.md` §2.1. Do not duplicate the rule
tables from that section here; refer to it for the authoritative definition.

---

## 3. Drift Detection and Recovery

**Hard rule:** if `session-state.json` reports `current_phase: "green"` but
the last git commit carries a `refactor:` prefix, **drift has occurred** —
**abort and escalate to the user immediately**. Do not attempt silent
reconciliation; silent sync hides protocol bugs.

### Recovery procedure (manual, not automatic)

1. Regenerate `session-state.json` from two sources of truth:
   - Plan (`planning/claude-plan-tdd.md`): find the last `[x]` task.
   - Git: inspect the last commit prefix and SHA.
2. Construct the minimal consistent state from those two sources.
3. **Present the reconstructed state to the user and ask for explicit
   confirmation before resuming any TDD phase.**

Recovery is intentionally manual so that state divergence surfaces as a
conversation rather than a silent assumption.

---

## 4. Autonomous vs. Manual Scope

`session-state.json` is used **only** when an approved `planning/claude-plan-tdd.md`
exists and the session is running in one of the two autonomous modes
(`superpowers:executing-plans` or `superpowers:subagent-driven-development` via
`superpowers:dispatching-parallel-agents`).

Under **manual fallback** (no approved plan, ad-hoc tasks, hotfixes), the
state file is not read or written. The user controls phase transitions
explicitly in each prompt. If a state file from a previous completed plan
exists when switching to manual mode, it may be retained as a historical
record or deleted; it is neither read nor updated during the manual session.

For the full state-file schema (fields, types, update protocol), see
`CLAUDE.local.md` §2.2. This reference describes routing logic only; do not
duplicate the schema here.
