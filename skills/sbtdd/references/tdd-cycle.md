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
the hooks in `.claude/settings.json` are session-global. It maintains **shared
state at process level** (its own internal file under `.claude/tdd-guard/`,
separate from `session-state.json`). That shared state is the root of the
parallelism constraint below: it cannot be partitioned per sub-agent, not even
across separate worktrees.

### Default and Preferred Mode

**Serial execution with TDD-Guard ON, via
`superpowers:subagent-driven-development`.** This is the default and the
preferred mode for the skill: one task at a time, each running its own
Red→Green→Refactor cycle under real-time guard enforcement. Suggest parallel
agents only when **both** conditions hold:

1. There is a **perceptible time gain** from running the tasks concurrently.
2. The tasks are **mutually independent** — no shared state and no cross-task
   dependencies (dependent tasks must be marked `addBlockedBy` and run serially
   anyway).

When in doubt, stay serial. Parallelism trades the guard's real-time
enforcement for speed and must be set up deliberately (see the rules below).

### Scenario Table

| Scenario | TDD-Guard | Behavior |
|----------|-----------|----------|
| **Serial** (one task at a time) — *default / preferred* | ON | Correct — each task completes its own Red→Green→Refactor cycle under real-time enforcement |
| **Parallel** sub-agents, any layout — same **or** separate worktrees | ON | **Conflict** — the guard's shared process state collides across agents and blocks legitimate writes, *even in separate worktrees* |
| **Parallel** sub-agents, one isolated worktree each | OFF | Correct — git isolation per agent; Red-Green-Refactor discipline rests on `superpowers:test-driven-development`, with `superpowers:verification-before-completion` mandatory at every phase close |

### Practical Rules

1. **Default & preferred: serial execution with TDD-Guard ON.**
   `superpowers:executing-plans` and `superpowers:subagent-driven-development`
   process tasks in plan order when no explicit dependencies are marked.

2. **Go parallel only when it is worth it** — a perceptible time gain *and*
   mutually independent tasks (see "Default and Preferred Mode" above).
   Otherwise stay serial.

3. **Parallel requires this full combination** (the parts are not alternatives):
   - **TDD-Guard OFF.** With the guard ON, parallel sub-agents conflict *even in
     separate worktrees* — one agent's phase state blocks another's legitimate
     writes. The user toggles `tdd-guard off` before dispatching and
     `tdd-guard on` when the parallel run finishes; sub-agents cannot toggle it.
   - **One isolated worktree per sub-agent** via `superpowers:using-git-worktrees`,
     so concurrent work never contaminates a shared working tree.
   - **`superpowers:test-driven-development` enforces the Red-Green-Refactor
     discipline** during the OFF window, with
     `superpowers:verification-before-completion` mandatory at every phase close
     (it replaces the guard's real-time check).
   - **On completion, each sub-agent commits its work and merges its worktree
     branch back into the parent ("mother") branch.**

4. **Never run parallel sub-agents with TDD-Guard ON**, regardless of worktree
   separation — it produces false blocks and inconsistent guard state.

---

## 5. Spec Precedence on Ambiguity

When `sbtdd/spec-behavior.md` and `planning/claude-plan-tdd.md` contradict each
other, **`spec-behavior.md` wins** — it is the authoritative behavioral contract.
Consult `sbtdd/spec-behavior.md` before assuming any behavior; do not implement
behavior that is absent from the spec.

---

## 6. TDD-Guard Toggle for Non-Execution Phases

TDD-Guard's `PreToolUse` matcher (`Write|Edit|MultiEdit|TodoWrite`) enforces
the Red-Green-Refactor cycle by blocking writes that violate it. This
enforcement is only meaningful during the **Execution** phase.

During non-Execution phases — **Spec**, **Planning**, **Plan gate**,
**Pre-merge review**, and **Finalization** — the orchestrator and skills make
legitimate markdown, spec, plan, and `TodoWrite` writes that TDD-Guard would
otherwise block. To avoid false blocks:

- **Before entering a non-Execution phase:** issue the quick command
  `tdd-guard off` (via `UserPromptSubmit`). This disables PreToolUse
  enforcement for the duration of that phase.
- **When returning to the Execution phase:** issue `tdd-guard on` to
  re-enable enforcement.

Note: only the user (or the orchestrator acting on the user's behalf via an
explicit prompt) may toggle TDD-Guard. Sub-agents cannot toggle it.

---

## 7. On Unexpected Test Failure

If a test fails unexpectedly during any phase, invoke
`superpowers:systematic-debugging` before proposing a fix. Diagnose the root
cause; do not patch the symptom. Only after the diagnosis is clear should a
fix be applied, verified, and committed.
