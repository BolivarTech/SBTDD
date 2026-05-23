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
| `sbtdd/spec-behavior-base.md` absent, empty, or still contains `<!-- replace -->` markers | — | **Stop and ask the user to fill it in** before proceeding — do NOT proceed to brainstorming on unfilled boilerplate |
| `sbtdd/spec-behavior-base.md` present; `sbtdd/spec-behavior.md` absent | Specification | Invoke `superpowers:brainstorming` using `spec-behavior-base.md` as input |
| `sbtdd/spec-behavior.md` present; `planning/claude-plan-tdd-org.md` absent | Planning | Invoke `superpowers:writing-plans` to generate `claude-plan-tdd-org.md` |
| `planning/claude-plan-tdd-org.md` present; `planning/claude-plan-tdd.md` absent or not yet approved | Plan gate (Checkpoint 2) | Run MAGI review against spec + plan; iterate until `claude-plan-tdd.md` is approved (see `references/review-gates.md` for the MAGI verdict table) |
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

**Canonical mapping — phase implied by the last phase-closing commit:**

| Last phase-closing commit prefix | `current_phase` SHOULD be |
|----------------------------------|---------------------------|
| `test:`                          | `green`                   |
| `feat:` or `fix:`                | `refactor`                |
| `refactor:`                      | `red` (next task) or `done` (plan complete) |
| `chore:`                         | `red` (next task) or `done` (plan complete) |

`current_phase` is set to the phase to work on **next** after a phase closes.
The consistency check therefore compares `current_phase` to the phase
**implied by** the last phase-closing commit, not to the prefix of that same
phase.

**Classification rules (evaluate in order):**

1. **N/A** — `current_phase == "done"`: the plan is complete; any post-done
   commits (`test:` / `fix:` / `refactor:` from a pre-merge review mini-cycle)
   are expected and correct. This is NOT drift; do not abort.

2. **Consistent** — `current_phase` equals the phase implied by the last
   phase-closing commit per the table above. Normal state; continue.

3. **Recoverable lag** — `current_phase` equals the phase that was *closed* by
   the last commit (i.e. the commit landed but the state update was
   interrupted before `current_phase` was advanced). This is NOT drift; resume
   by completing the state update and advancing `current_phase`, then
   escalate to the user for confirmation.

4. **DRIFT** — none of the above. `current_phase` does not match either the
   implied next phase or the closed phase. **Abort and escalate to the user
   immediately.** Do not attempt silent reconciliation; silent sync hides
   protocol bugs.

Worked examples:
- `current_phase = "done"` + last commit `fix:` → **N/A** (pre-merge
  review mini-cycle after plan completion; not drift).
- `current_phase = "red"` + last commit `test:` → **recoverable lag** (the
  `test:` commit closed Red, but `current_phase` was not yet advanced to
  `green`; resume by updating state).
- `current_phase = "green"` + last commit `feat:` → **recoverable lag** (the
  `feat:` commit closed Green, but `current_phase` was not yet advanced to
  `refactor`).
- `current_phase = "green"` + last commit `test:` → **consistent**.
- `current_phase = "refactor"` + last commit `feat:` → **consistent**.
- `current_phase = "green"` + last commit `refactor:` → **DRIFT** (green
  implies the last closing commit was `test:`, but we see `refactor:`).
- `current_phase = "refactor"` + last commit `test:` → **DRIFT** (refactor
  implies the last closing commit was `feat:`/`fix:`, but we see `test:`).

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
