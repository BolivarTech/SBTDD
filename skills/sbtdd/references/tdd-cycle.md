# sbtdd — TDD Cycle Reference

This reference describes the per-phase rules, the non-negotiable atomic close
procedure, bookkeeping at Refactor close, TDD-Guard behavior under multi-agent
execution, and failure handling. For commit prefix conventions, see
`CLAUDE.local.md` §5. For verification commands, see `CLAUDE.local.md` §0.1.
For the state-file schema and update protocol, see `CLAUDE.local.md` §2.2.

---

## 1. Per-Phase Rules

| Phase | Allowed | Blocked |
|-------|---------|---------|
| **Red** | Write tests that fail. Minimal stubs to compile (no real logic). | Production code. Tests that pass without an implementation. |
| **Green** | Minimum implementation to make existing tests pass. | Modifying tests. Adding functionality not required by any test. |
| **Refactor** | Improve structure, names, remove duplication, add doc-comments. | Adding functionality. Modifying tests. Changing observable behavior. |

If TDD-Guard (hook enforcement) and `superpowers:test-driven-development`
(skill guidance) disagree, TDD-Guard takes precedence — it is physical
enforcement, not a suggestion.

---

## 2. Bookkeeping Note at Refactor Close

At the close of the Refactor phase, two bookkeeping actions are required:

1. Mark the checkbox `[x]` in `planning/claude-plan-tdd.md` for the completed
   task.
2. Update `.claude/session-state.json` per the protocol in `CLAUDE.local.md` §2.3.

These actions are **not** "adding functionality" and do not violate Refactor's
blocked list. They are administrative task-close bookkeeping per §2.3 of
`CLAUDE.local.md` and do not count as a TDD phase change.

---

## 3. Atomic 3-Step Close (Non-Negotiable)

Every phase — Red, Green, Refactor — must be closed with the following three
steps in strict order. A phase is not considered approved until all three
complete successfully.

### Step 1 — Verification

Invoke `superpowers:verification-before-completion`. The skill requires running
every command listed in `CLAUDE.local.md` §0.1 for the project's stack and
presenting their output as evidence. "It should pass" is not evidence — the
actual command output is.

### Step 2 — Atomic Commit

Only after Step 1 passes cleanly, create an atomic commit using the prefix
corresponding to the phase (see `CLAUDE.local.md` §5). The commit must contain
**only** the diff of that phase. Do not mix Red with Green, Green with Refactor,
or different tasks in a single commit.

### Step 3 — Update `session-state.json`

After the commit, update `session-state.json` to reflect the transition:
advance `current_phase`, record `phase_started_at_commit` (the SHA of the
commit just created), and update `last_verification_at` and
`last_verification_result`. Full protocol in `CLAUDE.local.md` §2.3.

#### Refactor-close fork

When the closed phase is Refactor, the task is complete. Two sub-cases apply:

- **Next `[ ]` task exists in plan** — commit the checkbox update with
  `chore: mark task {id} complete`; advance `current_task_id` /
  `current_task_title` to that task and reset `current_phase` to `"red"`.
- **No next `[ ]` task (last task)** — commit the checkbox update with
  `chore: mark task {id} complete`; set `current_task_id: null`,
  `current_task_title: null`, `current_phase: "done"` in `session-state.json`.
  This enables the finalization flow (see `references/finalization.md`).

---

## 4. TDD-Guard Under Multi-Agent Execution

TDD-Guard is active for all sub-agents spawned from the main session because
the hooks in `.claude/settings.json` are session-global. However, TDD-Guard
maintains **shared state at process level** (its own internal file under
`.claude/tdd-guard/`, separate from `session-state.json`), which creates a
strong constraint under parallelism.

### Scenario Table

| Scenario | TDD-Guard | Behavior |
|----------|-----------|----------|
| Sub-agents **serial** (one task at a time) | ON | Correct — each task completes its own Red→Green→Refactor cycle |
| Sub-agents **parallel** in the **same worktree** | ON | **Conflict** — one sub-agent's phase can block legitimate writes from another |
| Sub-agents **parallel** in **separate worktrees** | ON | Correct — each worktree has its own TDD-Guard state file |
| Sub-agents parallel, same worktree | OFF | Correct — correctness enforcement deferred to `superpowers:verification-before-completion` at phase close; Red-Green-Refactor discipline rests solely on `superpowers:test-driven-development` |

### 3 Practical Rules

1. **Default: serial execution with TDD-Guard ON.** `superpowers:executing-plans`
   and `superpowers:subagent-driven-development` process tasks in plan order
   when no explicit dependencies are marked.

2. **Real parallelism** requires one of:
   - `superpowers:using-git-worktrees` → one worktree per sub-agent, TDD-Guard ON.
   - The user explicitly toggles `tdd-guard off` before dispatching parallel
     execution and `tdd-guard on` when done. During the OFF window,
     `superpowers:verification-before-completion` is mandatory at every phase
     close, and `superpowers:test-driven-development` is the sole discipline
     enforcer. Sub-agents cannot toggle TDD-Guard themselves.

3. **Never** run parallel tasks in the same worktree with TDD-Guard ON — this
   produces false blocks and inconsistent state.

---

## 5. Spec Precedence on Ambiguity

When `sbtdd/spec-behavior.md` and `planning/claude-plan-tdd.md` contradict each
other, **`spec-behavior.md` wins** — it is the authoritative behavioral contract.
Consult `sbtdd/spec-behavior.md` before assuming any behavior; do not implement
behavior that is absent from the spec.

---

## 6. On Unexpected Test Failure

If a test fails unexpectedly during any phase, invoke
`superpowers:systematic-debugging` before proposing a fix. Diagnose the root
cause; do not patch the symptom. Only after the diagnosis is clear should a
fix be applied, verified, and committed.
