---
name: sbtdd
description: >
  SBTDD + Superpowers multi-agent workflow orchestrator. Use when working on a
  project that follows the SBTDD methodology (Spec + Behavior + Test Driven
  Development) and needs to execute one of the nine workflow operations:
  init, spec, close-phase, close-task, status, pre-merge, finalize, auto,
  resume. Trigger phrases: "sbtdd init", "sbtdd close phase", "advance TDD
  phase", "run pre-merge review", "finalize SBTDD plan", "sbtdd auto",
  "shoot-and-forget SBTDD run", "resume SBTDD", "sbtdd resume", "continue
  interrupted SBTDD session", or any "/sbtdd <subcommand>" invocation. NOT
  suitable for projects that do not use SBTDD -- only invoke when the project
  has `sbtdd/spec-behavior-base.md` or `.claude/plugin.local.md` with `stack` set.
---

# SBTDD Workflow -- Spec + Behavior + Test Driven Development Orchestrator

> `~/.claude/CLAUDE.md` has absolute precedence (INV-0). This skill is a
> dispatcher -- it never overrides the developer's global Code Standards.

## Overview

SBTDD (Spec + Behavior + Test Driven Development) combines three disciplines:

- **SDD (Spec Driven Development):** a textual specification (`sbtdd/spec-behavior.md`)
  is authoritative. No behavior is implemented that is not declared there.
- **BDD (Behavior Driven Development):** Given/When/Then scenarios in the spec
  document expected behavior in testable form.
- **TDD (Test Driven Development):** Red-Green-Refactor discipline, enforced
  physically by TDD-Guard hooks and procedurally by `/test-driven-development`.

This plugin orchestrates the SBTDD lifecycle end to end: from blank spec through
pre-merge gates to a ship-ready branch. Every state transition produces an atomic
git commit following the sec.M.5 prefix map (`test:` / `feat:` / `fix:` /
`refactor:` / `chore:`). Two mandatory pre-merge loops -- automated code review
(`/requesting-code-review`) and multi-perspective review (`/magi:magi`) -- gate
the branch before `/finishing-a-development-branch`.

The plugin follows the architectural pattern of MAGI (one skill, one entrypoint,
Python-backed scripts). The skill below is the dispatcher; all state-changing
logic lives in `scripts/run_sbtdd.py` and the nine `{subcommand}_cmd.py` modules.

## Subcommand dispatch

| Subcommand | Purpose | When to invoke |
|------------|---------|----------------|
| `init` | Bootstrap an SBTDD project (generate rules, hooks, skeleton spec) | Once per destination project, greenfield |
| `spec` | Run the spec pipeline (`/brainstorming` -> `/writing-plans` -> MAGI Checkpoint 2) | After `init`, before any code; iteratively until MAGI approves |
| `close-phase` | Close one TDD phase (Red/Green/Refactor) atomically: verify + commit + advance state | After implementing each phase, before moving to the next |
| `close-task` | Mark `[x]` in the plan + commit `chore:` + advance state to the next `[ ]` | After the Refactor phase of a task (also auto-invoked by `close-phase refactor`) |
| `status` | Read-only structured report of state + git + plan + drift | At any time, safe to invoke (read-only) |
| `pre-merge` | Run Loop 1 (`/requesting-code-review` until clean-to-go) + Loop 2 (`/magi:magi` gate) | When all plan tasks are `[x]` and `current_phase: "done"` |
| `finalize` | Run the sec.M.7 checklist + invoke `/finishing-a-development-branch` | After `pre-merge` returns exit 0 |
| `auto` | Shoot-and-forget full cycle: task loop + pre-merge + checklist (stops before `/finishing-a-development-branch`) | When the user wants unattended execution of an approved plan |
| `resume` | Diagnose interrupted runs (quota exhaustion, crash, reboot) and delegate recovery | After an `auto` run aborted mid-flight, or after any interruption |

Invocation pattern: `/sbtdd <subcommand> [args...]`. Under the hood, every
subcommand routes through `run_sbtdd.py` (see `## Execution pipeline` below).

## Complexity gate

Before delegating to Python, assess whether the user's request actually needs
state transitions. If the user asks a simple factual question about SBTDD
methodology (e.g., "what does INV-27 mean?", "what is the commit prefix for a
Refactor phase?"), respond directly from the embedded rules in `## sbtdd-rules`
below -- no Python invocation needed.

Invoke Python (via `run_sbtdd.py`) when the user asks for:

- Any of the nine subcommands (explicit: `/sbtdd init`, `/sbtdd close-phase`, ...).
- State interrogation that must be accurate (e.g., "what phase am I on?",
  "is my plan complete?").
- Any action that mutates `.claude/session-state.json`, the plan, or git.

Do NOT invoke Python for:

- Explaining methodology sections (answer from the embedded `## sbtdd-rules`).
- Clarifying commit prefix rules (answer from the embedded `## sbtdd-tdd-cycle`).
- Meta-questions about the plugin (version, repository, license) -- answer
  from the `plugin.json` manifest directly.
