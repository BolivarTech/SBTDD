# sbtdd — Spec + Behavior + Test-Driven Development Plugin

`sbtdd` is a Claude Code plugin that orchestrates the **SBTDD** (Spec +
Behavior + Test-Driven Development) multi-agent workflow on top of the
`superpowers` skill suite. It acts as a state-routing engine: each time you
invoke `/sbtdd`, it reads the current project state and advances you to the
next phase — from initial spec capture through MAGI gate, TDD execution,
dual-loop review, and finalization.

---

## Commands

### `/sbtdd` — Drive or resume the workflow

Routes by project state (`sbtdd/`, `planning/`, `.claude/session-state.json`)
and executes the next SBTDD phase. Run this at any point to start the workflow
or to continue from where you left off.

### `/sbtdd-init` — Scaffold a project

Idempotent setup command that prepares a project for the SBTDD workflow:

- Detects the build stack (`Cargo.toml` → Rust, `pyproject.toml`/`setup.py`
  → Python, `CMakeLists.txt` → C/C++) and injects the correct per-phase
  verification block into `CLAUDE.local.md`.
- Writes `CLAUDE.local.md` from the plugin template (skips if already present).
- Creates or merges `.claude/settings.json` with the three required
  `tdd-guard` hooks (`PreToolUse`, `SessionStart`, `UserPromptSubmit`).
- Creates the `sbtdd/` and `planning/` working directories.
- Seeds `sbtdd/spec-behavior-base.md` from the plugin template.
- Updates `.gitignore` with the five local-only entries (see Tracking Policy
  below).

`/sbtdd-init` never overwrites existing files and always reports what was
created vs. skipped.

### `/sbtdd-check` — Verify the environment (read-only)

Runs seven diagnostic checks and reports `PASS`, `FAIL`, or `N/A` for each:

1. `CLAUDE.local.md` present and contains required rule sections
2. Three `tdd-guard` hooks active in `.claude/settings.json`
3. `sbtdd/` and `planning/` directories exist
4. `.gitignore` contains all five local-only entries
5. `tdd-guard` binary and stack reporter on `PATH`
6. State-file drift check (skipped if no session state yet)
7. `superpowers` skills and `magi:magi` reachable by the harness

`/sbtdd-check` diagnoses only — it does not modify anything. To repair a
failing check, run `/sbtdd-init`.

---

## Getting Started

1. **Install the plugin** — place this plugin directory where your Claude Code
   harness loads plugins, then restart the harness. Command template paths that
   reference `${CLAUDE_PLUGIN_ROOT}` are resolved by the harness to the installed
   plugin directory automatically.

2. **Install runtime dependencies** (see Dependencies below) — ensure
   `tdd-guard` and the stack reporter are on `PATH`.

3. **Scaffold your project** — run `/sbtdd-init` in your project. The command
   detects your stack (Rust / Python / C-C++) and creates all required files
   and directories.

4. **Verify the setup** — run `/sbtdd-check` to confirm every check passes.

5. **Run the workflow** — run `/sbtdd` to start the SBTDD flow. Run it again
   any time to advance to the next phase or to resume after an interruption.

---

## Multi-Stack Support

`/sbtdd-init` auto-detects the build stack and injects the right per-phase
verification block into `CLAUDE.local.md`:

| Manifest file           | Stack   | Test command             |
|-------------------------|---------|--------------------------|
| `Cargo.toml`            | Rust    | `cargo test`             |
| `pyproject.toml` / `setup.py` | Python | `python -m pytest` |
| `CMakeLists.txt`        | C/C++   | CMake + CTest            |

If more than one manifest is detected — or none — `/sbtdd-init` pauses and
asks which stack to configure.

---

## Tracking Policy and Trade-off

All SBTDD process files are **developer-local** and excluded from version
control. `/sbtdd-init` appends these entries to `.gitignore`:

```
# SBTDD local-only files
CLAUDE.local.md
CLAUDE.md
.claude/
sbtdd/
planning/
```

**Trade-off:** Because these paths are gitignored, the spec, plan, state
machine, and SBTDD configuration are not committed to the repository.
This means:

- No cross-machine continuity — the workflow state does not follow you to
  another machine or a new clone.
- No git audit trail of spec changes, planning documents, or SBTDD phase
  transitions.

The design is intentional: SBTDD is a developer-local thinking and execution
aid, not a shared artifact. Only the production code and its tests are
committed; the scaffolding that produced them stays private.

---

## Dependencies

The following must be installed and reachable by the harness before running
`/sbtdd`:

### `superpowers` plugin

`/sbtdd` delegates to these `superpowers` skills at various phases:

- `superpowers:writing-plans` — structured planning phase
- `superpowers:test-driven-development` — Red-Green-Refactor execution
- `superpowers:systematic-debugging` — diagnosis when tests stay red
- `superpowers:verification-before-completion` — pre-commit gate
- `superpowers:requesting-code-review` — review before finalization

Install the `superpowers` plugin via your Claude Code plugin manager.

### `magi` plugin

The MAGI gate (`magi:magi`) is used as a multi-perspective review checkpoint
between planning and TDD execution. Install the `magi` plugin separately.

Note: MAGI requires genuine uncertainty to be useful — it is a deliberation
gate, not a rubber stamp. If `magi:magi` is unavailable, `/sbtdd` will report
the missing skill and halt rather than skip the gate silently.

### `tdd-guard` binary + per-stack reporter

`tdd-guard` enforces the TDD cycle via Claude Code hooks. The stack reporter
feeds test results back to the guard.

- **Rust:** `cargo install sbtdd-reporter`
- **Python:** `pip install sbtdd-reporter`
- **C/C++:** build from source

Both binaries must be on `PATH`. Run `/sbtdd-check` (Check 5) to verify.

---

## Workflow Phases (overview)

```
/sbtdd-init  →  /sbtdd-check  →  /sbtdd
                                    │
                          ┌─────────▼──────────┐
                          │  1. Spec capture    │
                          │  2. Behavior spec   │
                          │  3. Planning        │
                          │  4. MAGI gate       │
                          │  5. TDD execution   │
                          │     (Red→Green→     │
                          │      Refactor)      │
                          │  6. Dual-loop review│
                          │  7. Finalization    │
                          └────────────────────┘
```

Each phase is driven by the `sbtdd` skill; `/sbtdd` is the single entry point
to advance through all of them.
