# SBTDD — Spec + Behavior + Test-Driven Development Orchestrator for Claude Code

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-43%20passing-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

A Claude Code plugin that drives the **SBTDD** workflow — **S**pec + **B**ehavior + **T**est-**D**riven **D**evelopment — as a single, resumable, state-routed flow on top of the [`superpowers`](https://github.com/obra/superpowers) skill library and the [`magi`](https://github.com/BolivarTech/magi-claude) multi-perspective review gate.

One entry point, `/sbtdd`, inspects your project, figures out which phase you are in, and runs the next step — from spec refinement through planning, a MAGI plan gate, disciplined Red-Green-Refactor execution, a dual-loop pre-merge review, and finalization.

---

## Why SBTDD?

Most "AI writes the code" workflows collapse three different concerns into one prompt: *what to build*, *how it should behave*, and *whether it works*. SBTDD keeps them separate and ordered, and makes the separation **enforceable** rather than aspirational:

- **Spec (SDD)** — the objective and functional requirements are written down first (`spec-behavior-base.md` → `spec-behavior.md`).
- **Behavior (BDD)** — expected behavior is captured as Given/When/Then scenarios; test names describe behavior, not implementation.
- **Test-Driven (TDD)** — every change follows Red → Green → Refactor, with an atomic commit and a verification gate per phase.

The plugin's contribution is **orchestration with gates that don't move**:

- A **state machine** tracks the active task and TDD phase in `.claude/session-state.json`, so a half-finished plan resumes cleanly across sessions.
- **Drift detection** aborts and escalates when the recorded phase and the git history disagree — silent desync hides protocol bugs.
- Two **human gates** stay explicit (plan approval, and the MAGI verdict) — the agent never auto-approves them.
- Autonomy is scoped: the agent commits autonomously **only** under an approved plan, per the rules it is handed.

The result is a flow where the *value* is the sequencing and the gates, not just "code got written."

---

## Commands

| Command | Purpose |
|---------|---------|
| `/sbtdd` | Drive or **resume** the workflow. Detects the current phase from project artifacts + `.claude/session-state.json` and runs the next step, delegating to the right `superpowers` / `magi:magi` skill. |
| `/sbtdd-init` | Scaffold a project for SBTDD. Detects the stack (Rust / Python / C-C++), writes `CLAUDE.local.md` (rules) and the TDD-Guard hooks, creates the `sbtdd/` and `planning/` directories, and updates `.gitignore`. Idempotent. |
| `/sbtdd-check` | Read-only environment verifier. Confirms rules, hooks, directories, the `tdd-guard` binary, and the delegated `superpowers` / `magi:magi` skills are present. Diagnoses; never fixes. |

---

## Installation

### From GitHub (for users)

```bash
# 1. Add this repo as a marketplace source
/plugin marketplace add BolivarTech/SBTDD

# 2. Install the plugin
/plugin install sbtdd@bolivartech-sbtdd

# 3. Initialize a project, verify, then drive the flow
/sbtdd-init
/sbtdd-check
/sbtdd
```

To update after new versions are published:

```bash
/plugin marketplace update
```

### Dependencies

SBTDD is an **orchestrator** — it delegates to existing skills rather than reimplementing them. Install these too:

| Dependency | Why |
|------------|-----|
| [`superpowers`](https://github.com/obra/superpowers) | The skills SBTDD delegates to (`brainstorming`, `writing-plans`, `test-driven-development`, `verification-before-completion`, `requesting-code-review`, `finishing-a-development-branch`, …). |
| [`magi`](https://github.com/BolivarTech/magi-claude) | The `magi:magi` multi-perspective gate, run **twice** across the lifecycle: at the plan checkpoint and at pre-merge. |
| `tdd-guard` binary + per-stack reporter | Real-time Red-Green-Refactor enforcement. Install the binary **before** `/sbtdd-init` writes the hooks (a hook pointing at a missing binary fails closed). Optional reporters sync test output on demand: `tdd-guard-rust`, `tdd-guard-pytest`, etc. |

`/sbtdd-check` verifies all of the above and fails loudly on anything missing.

### Local Development

```bash
# Plugin flag
claude --plugin-dir /path/to/SBTDD
```

Changes are picked up with `/reload-plugins` without restarting.

---

## How It Works

`/sbtdd` is a thin command that invokes the `sbtdd` skill. The skill is deliberately short — it holds only the **routing** logic and a **delegation table**; the per-phase detail lives in `references/*` and is read on demand (progressive disclosure).

```
/sbtdd (command) ──▶ sbtdd skill (SKILL.md)
                       │
                       ├─ Preflight   verify CLAUDE.local.md, sbtdd/, planning/  (else → /sbtdd-init)
                       ├─ Route       detect phase from artifacts + session-state.json
                       │              on drift → abort & escalate
                       ├─ Execute     read the phase reference, invoke the delegated skill(s)
                       ├─ Gates       human stops (plan approval, MAGI verdict) — never auto-approved
                       └─ Loop        re-route to the next phase
```

### State-routed lifecycle

| Detected phase | Reference | Delegates to |
|----------------|-----------|--------------|
| Spec refinement | `routing.md` | `superpowers:brainstorming` |
| Planning | `routing.md` | `superpowers:writing-plans` |
| Plan gate (Checkpoint 2) | `review-gates.md` | `magi:magi` (+ manual review) |
| Execution | `tdd-cycle.md` | `superpowers:test-driven-development`, `…:verification-before-completion`, `…:systematic-debugging`; mode `…:subagent-driven-development` / `…:executing-plans` |
| Pre-merge review | `review-gates.md` | `superpowers:requesting-code-review` → `…:receiving-code-review` → `magi:magi` |
| Finalization | `finalization.md` | `superpowers:finishing-a-development-branch` |

### Multi-stack scaffolding

`/sbtdd-init` auto-detects the build stack and injects the matching per-phase verification block into the scaffolded `CLAUDE.local.md`:

| Manifest file | Stack | Test command |
|---------------|-------|--------------|
| `Cargo.toml` | Rust | `cargo nextest run` |
| `pyproject.toml` / `setup.py` | Python | `pytest` |
| `CMakeLists.txt` | C/C++ | `ctest` |

If more than one manifest is detected — or none — `/sbtdd-init` pauses and asks which stack to configure.

### Single source of truth

The skill **points to** the scaffolded `CLAUDE.local.md` for canonical rule values (commit prefixes, the state-file schema, verification commands) instead of duplicating them — change a rule in one place, no second copy drifts.

---

## Project Structure

```
.claude-plugin/
  plugin.json                 -- Plugin manifest (name, version, author, repository, license)
  marketplace.json            -- Marketplace config (bolivartech-sbtdd)
skills/sbtdd/
  SKILL.md                    -- Orchestrator: state routing + delegation table
  references/
    routing.md                -- State-detection table + authority order + drift handling
    tdd-cycle.md              -- Per-phase rules + atomic 3-step close + TDD-Guard under parallelism
    review-gates.md           -- Dual-loop pre-merge review + MAGI verdict table
    finalization.md           -- Clean git-status check + final checklist
commands/
  sbtdd.md                    -- Thin entry wrapper (invokes the skill)
  sbtdd-init.md               -- Multi-stack scaffolding (idempotent)
  sbtdd-check.md              -- Read-only environment verifier
templates/                    -- Assets /sbtdd-init writes into a target repo
  CLAUDE.local.md.tmpl        -- The immutable project rules (standards, artifact contract, commits)
  settings.json.tmpl          -- TDD-Guard hooks
  spec-behavior-base.tmpl.md  -- Flow input template
  verification/{rust,python,cpp}.md  -- Per-stack verification blocks
tests/                        -- pytest structural-validation suite (repo-dev tooling)
docs/SBTDD-Theory.md          -- The theory and quality rationale behind SBTDD
pyproject.toml                -- Python >= 3.9, dual license, pytest config
```

---

## Tracking Policy

The entire SBTDD process is **developer-local**. `/sbtdd-init` adds these to a target project's `.gitignore`: `CLAUDE.md`, `CLAUDE.local.md`, `.claude/`, `sbtdd/`, and `planning/`. Git records source code and the TDD-cycle commits only.

**Trade-off (intentional):** the spec, plan, and runtime state are not versioned or shared via git — there is no cross-machine continuity and no git audit trail of the process. Local cross-session resumability is unaffected (the files persist on disk; recovery is defined in `CLAUDE.local.md` §2.1). If a team needs to share spec/plan, use a channel other than git.

---

## Running Tests

The plugin is markdown/JSON/templates, so the test suite asserts **structure and content presence** (a green run is a presence/lint signal, not proof of agent runtime behavior). The real acceptance gate is `plugin-validator` plus manual behavioral evaluation.

```bash
# All tests (43)
python -m pytest -q

# Verbose
python -m pytest -v
```

| Layer | What it checks |
|-------|----------------|
| `test_manifest` / `test_*_template` | Manifest validity, per-stack verification blocks, settings + rules templates |
| `test_skill` / `test_references` | Frontmatter, the delegation table, per-reference required content |
| `test_commands` | The three commands (incl. the defensive `settings.json` merge contract) |
| `test_drift_model` | Behavioral classifier for the TDD-phase drift detection (consistent / lag / done / drift) |
| `test_integration` | Cross-reference integrity + section-name drift guard |

---

## Requirements

| Component | Required | Notes |
|-----------|----------|-------|
| Claude Code | Yes | The plugin runs inside Claude Code. |
| `superpowers` plugin | Yes | Delegated skills. |
| `magi` plugin | Yes | `magi:magi` review gate. |
| `tdd-guard` + reporter | For execution | Real-time TDD enforcement; install before `/sbtdd-init`. |
| Python 3.9+ | For the test suite | The plugin itself ships no runtime Python. |

---

## License

Dual licensed under [MIT](LICENSE) OR [Apache-2.0](LICENSE-APACHE), at your option.

---

## Credits

SBTDD was built by **dogfooding its own methodology**: the plugin was specified with `brainstorming`, planned with `writing-plans`, gated by `magi:magi`, implemented Red-Green-Refactor via subagent-driven development, and reviewed through a four-iteration pre-merge MAGI loop before its first release.

Authored by [Julian Bolivar](https://github.com/BolivarTech) (BolivarTech). Built on [`superpowers`](https://github.com/obra/superpowers) by Jesse Vincent and the [`magi`](https://github.com/BolivarTech/magi-claude) plugin.
