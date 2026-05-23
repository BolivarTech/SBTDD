---
name: sbtdd
description: >
  Drive or resume the SBTDD (Spec + Behavior + Test-Driven Development)
  multi-agent workflow. Use when running /sbtdd, starting an SBTDD feature,
  continuing an in-progress TDD plan, or when the user mentions SBTDD,
  spec-behavior, or the claude-plan-tdd flow. Inspects project artifacts and
  .claude/session-state.json, then executes the next phase.
---

# SBTDD Orchestrator Skill

This skill drives the full SBTDD lifecycle. It routes to the correct phase,
delegates to the appropriate superpowers skills, and enforces human gates.
Per-phase detail lives in the `references/` directory; this file holds only
the routing skeleton and the delegation table.

## 5-Step Operating Procedure

### 1. Preflight

Verify that `CLAUDE.local.md`, `sbtdd/`, and `planning/` exist in the project
root. If any are missing, **stop immediately** and tell the user:

> "Required SBTDD artifacts are missing. Run `/sbtdd-init` to initialize the
> project. For a full integrity check, run `/sbtdd-check`."

Do not proceed past Preflight until the project is initialized.

### 2. Route

Read `references/routing.md`. Detect the current phase by inspecting the
artifacts that are actually present on disk (use Glob/LS/Read — file existence
is the deterministic ground truth). On state drift or ambiguity, abort and
escalate to the user. **Announce the detected phase and the evidence found**,
and confirm with the user before acting when the phase is ambiguous.

### 3. Execute

Read the reference file for the detected phase (see delegation table below)
and invoke the listed skill(s) using their fully qualified names
(`superpowers:…`, `magi:magi`).

| Detected phase | Reference to read | superpowers skill(s) |
|---|---|---|
| Spec refinement | routing.md | `superpowers:brainstorming` |
| Planning | routing.md | `superpowers:writing-plans` |
| Plan gate | review-gates.md | `magi:magi` (+ manual review) |
| Execution | tdd-cycle.md | `superpowers:test-driven-development`, `superpowers:verification-before-completion`, `superpowers:systematic-debugging`; mode `superpowers:subagent-driven-development` or `superpowers:executing-plans`; optional `superpowers:using-git-worktrees`, `superpowers:dispatching-parallel-agents` |
| Pre-merge review | review-gates.md | `superpowers:requesting-code-review` → `superpowers:receiving-code-review` → `magi:magi` |
| Finalization | finalization.md | `superpowers:finishing-a-development-branch` |

> **TDD-Guard toggle:** TDD-Guard enforcement is only meaningful during the
> Execution phase. Toggle `tdd-guard off` before non-Execution phases (Spec,
> Planning, Plan gate, Pre-merge review, Finalization) so legitimate
> markdown/spec/plan/TodoWrite writes are not blocked; toggle `tdd-guard on`
> when returning to Execution. See `references/tdd-cycle.md` §6 for details.

### 4. Gates

Human stops are mandatory at plan approval and MAGI verdict checkpoints. Never
auto-approve any gate. Wait for explicit human confirmation before advancing to
the next phase.

### 5. Loop

After a phase closes, re-route (return to step 2). Under an approved plan, the
orchestrator may continue autonomously according to the rules in
`CLAUDE.local.md` §5 without prompting between sub-steps.

## Reference Files

- `references/routing.md` — phase detection rules and artifact map
- `references/tdd-cycle.md` — execution phase TDD procedure
- `references/review-gates.md` — gate criteria and MAGI integration
- `references/finalization.md` — branch completion and cleanup
