# SBTDD Orchestrator Plugin — Design

- **Date:** 2026-05-23
- **Status:** Approved (brainstorming) — pending implementation plan
- **Author:** jbolivarg
- **Source template:** `D:\jbolivarg\BolivarTech\AI_Tools\CLAUDE_local_md_SBTDD-Superpowers_template.md`
- **Target repo:** `D:\jbolivarg\PythonProjects\SBTDD-Skill`

> Design doc language is English to match the plugin content (shareability is a
> primary goal). A Spanish version can be produced on request.

---

## 1. Context & motivation

The source template is a `CLAUDE.local.md` "project constitution" that
orchestrates a multi-agent **SBTDD** (Spec + Behavior + Test-Driven
Development) workflow on top of the *superpowers* skill library. It mixes three
concerns that, in Claude Code, belong to three different mechanisms:

1. **Persistent project rules** (always enforced) → `CLAUDE.md` /
   `CLAUDE.local.md`.
2. **An on-demand procedure/playbook** → a *skill*.
3. **Automated enforcement** (TDD-Guard) → `settings.json` hooks.

Converting the *whole* template into a single skill would break its own premise:
skills load on demand, but the rules must be continuously in context. The
agreed scope is to extract **only the procedural sections (§1, §3, §6, §7)** into
an orchestrator skill, while the rules (§0, §2, §4, §5) stay as scaffolded
project configuration.

## 2. Goals / Non-goals

**Goals**
- Package the SBTDD procedural flow as an installable, shareable Claude Code
  **plugin**.
- Single predictable entry point `/sbtdd` that **routes by project state**
  (resumable across sessions).
- Self-bootstrapping: a setup command scaffolds rules + hooks + directories; a
  verifier command validates the environment.
- Multi-stack support (Rust / Python / C-C++) for the per-phase verification
  block and TDD-Guard reporter.
- Single source of truth: the skill references canonical rule values in
  `CLAUDE.local.md` rather than duplicating them.

**Non-goals**
- Re-implementing TDD, debugging, planning, or review logic. The orchestrator
  **delegates** to existing superpowers skills.
- Full autonomy. Human gates (plan approval, MAGI verdict) remain explicit
  stops.
- Sharing SBTDD artifacts (spec/plan) via git — see §9 (tracking policy):
  the entire SBTDD process is **local to the developer**.

## 3. Key decisions

| # | Decision | Choice |
|---|----------|--------|
| D1 | Packaging | Installable **plugin** (`plugin.json` + `skills/` + `commands/`) |
| D2 | Plugin scope | Orchestrator **+ setup + verifier** |
| D3 | Orchestrator structure | **One skill + reference files** (progressive disclosure) |
| D4 | Content language | **English** |
| D5 | Stack support | **Multi-stack** (Rust / Python / C-C++) |
| D6 | Operating model | **State-based routing** behind a single `/sbtdd` entry (approach A) |
| D7 | Artifact tracking | `sbtdd/` and `planning/` are **gitignored** — overrides the template; the whole SBTDD process is local; git records code only |

## 4. Architecture — plugin structure

```
sbtdd/                                    (repo root)
├── .claude-plugin/
│   └── plugin.json                       # plugin manifest
├── skills/
│   └── sbtdd/
│       ├── SKILL.md                      # orchestrator: state routing + delegation   [§1]
│       └── references/                    # progressive disclosure (read on demand)
│           ├── routing.md                # state-detection table + drift handling      [§2.1]
│           ├── tdd-cycle.md             # per-phase rules + atomic 3-step close        [§3]
│           ├── review-gates.md          # dual-loop pre-merge + MAGI verdict table     [§6]
│           └── finalization.md          # final checklist + clean git status           [§7]
├── commands/
│   ├── sbtdd.md                          # thin wrapper → invokes the sbtdd skill
│   ├── sbtdd-init.md                     # multi-stack scaffolding (one-off utility)
│   └── sbtdd-check.md                    # environment verifier (one-off utility)
├── templates/                            # assets /sbtdd-init writes into the target repo
│   ├── CLAUDE.local.md.tmpl              # the RULES kept out of the skill   [§0,§2,§4,§5]
│   ├── settings.json.tmpl                # TDD-Guard hooks                    [§4.1]
│   ├── spec-behavior-base.tmpl.md        # flow input template
│   └── verification/                     # per-stack §0.1 blocks
│       ├── rust.md
│       ├── python.md
│       └── cpp.md
└── README.md
```

### Responsibility split (anti-duplication principle)

| Lives in… | Content | Why |
|---|---|---|
| Skill `sbtdd` + references | The **procedure**: flow, executed TDD cycle, review loops, finalization (§1, §3, §6, §7) | Loaded on demand when running the flow |
| `templates/CLAUDE.local.md.tmpl` (installed as project rules by `/sbtdd-init`) | The **immutable rules**: standards, artifact contract + state-file schema, commit prefixes, stack (§0, §2, §4, §5) | Must always be in context and enforced |
| `templates/settings.json.tmpl` | TDD-Guard hooks (§4.1) | Harness-level automatic enforcement |

The skill describes the *steps* (verbs) and **points** to `CLAUDE.local.md` for
*canonical values* (commit prefixes, state-file fields, verification commands).
Changing a prefix in `CLAUDE.local.md` leaves no second copy to drift. The
dependency is deliberate: the skill assumes `/sbtdd-init` has scaffolded the
rules; if missing, `/sbtdd` stops and routes to `/sbtdd-init`, and
`/sbtdd-check` validates it explicitly.

## 5. The orchestrator skill (`/sbtdd`)

### Entry mechanism
A thin command `commands/sbtdd.md` provides the clean `/sbtdd` entry; its only
job is to invoke the `sbtdd` skill. The brain (routing + references) lives in
the skill, preserving progressive disclosure.

```
/sbtdd (commands/sbtdd.md) ──invoke──▶ skill sbtdd (SKILL.md) ──read on demand──▶ references/*.md
```

### Frontmatter
```yaml
---
name: sbtdd
description: >
  Drive or resume the SBTDD (Spec + Behavior + Test-Driven Development)
  multi-agent workflow. Use when running /sbtdd, starting an SBTDD feature,
  continuing an in-progress TDD plan, or when the user mentions SBTDD,
  spec-behavior, or the claude-plan-tdd flow. Inspects project artifacts and
  .claude/session-state.json, then executes the next phase.
---
```

### SKILL.md skeleton (5 steps, deliberately short)
1. **Preflight** — lightweight check: does `CLAUDE.local.md` and `sbtdd/`,
   `planning/` exist? If not → stop, route to `/sbtdd-init`. (Deep validation is
   `/sbtdd-check`.)
2. **Route** — read `references/routing.md`, detect the phase from artifacts +
   state file, handle drift (abort and escalate). Announce: "You are at phase X."
3. **Execute** — per the detected phase, read the matching SBTDD reference and
   invoke the superpowers skill(s) via the delegation table.
4. **Gates** — explicit human stops (Checkpoint 1 plan approval, MAGI verdict).
   Never auto-approve.
5. **Loop** — when the phase closes, re-route: continue in-session (autonomous
   execution under approved plan) or ask the user to re-invoke `/sbtdd`.

### Delegation table (core)

| Detected phase | SBTDD reference | superpowers skill(s) invoked |
|---|---|---|
| Spec refinement | routing.md | `/brainstorming` |
| Planning | routing.md | `/writing-plans` |
| Plan gate (Checkpoint 1+2) | review-gates.md | `/magi:magi` (+ manual review) |
| Execution | tdd-cycle.md | `/test-driven-development`, `/verification-before-completion`, `/systematic-debugging` (on failure); mode: `/subagent-driven-development` or `/executing-plans`; optional `/using-git-worktrees`, `/dispatching-parallel-agents` |
| Pre-merge review | review-gates.md | `/requesting-code-review` → `/receiving-code-review` → `/magi:magi` |
| Finalization | finalization.md | `/finishing-a-development-branch` |

The `SKILL.md` holds only routing + this table; per-phase detail is read from
the reference *only when entering that phase*.

## 6. Reference files

### `references/routing.md` (maps §2.1)
- Full state-detection decision table (artifact present → phase → action), with
  the §1 preconditions for each flow transition ("if X missing, stop and ask").
- Authority order (git = past, state file = present, plan = future) as the
  tie-breaker when artifacts disagree.
- Drift detection + recovery: hard rule "state says `green` but last commit is
  `refactor:` → abort and escalate"; state-file recovery from plan (last `[x]`)
  + git (last commit) with user confirmation.
- Autonomous vs manual flow distinction (when the state file applies).

### `references/tdd-cycle.md` (maps §3)
- Per-phase rules (Red/Green/Refactor): allowed vs blocked.
- Atomic 3-step close (non-negotiable): verify → atomic commit → update state
  file. Includes the Refactor-close fork (task close + possible plan close).
- TDD-Guard under parallelism: scenario table + 3 practical rules.
- Points to `CLAUDE.local.md` for canonical values: verification commands
  (§0.1), commit prefixes (§5), state-file schema (§2.2). Does not duplicate.

### `references/review-gates.md` (maps §6)
- Granularity: why MAGI runs **once** at the end, not per task/cycle.
- Sequential, independent dual loop: Loop 1 `/requesting-code-review` →
  clean-to-go; Loop 2 `/magi:magi` → `≥ GO WITH CAVEATS`. Why they don't merge.
- Full MAGI verdict table (STRONG GO … STRONG NO-GO) with each action, including
  when `GO WITH CAVEATS` requires re-evaluation (structural changes) vs not
  (low-risk).
- Correction loop with TDD mini-cycle (`test:`→`fix:`→`refactor:`) and the
  3-iteration safety valve → escalate.
- Also serves the Plan gate (Checkpoint 2 of §1), which uses the same verdict
  table — so this reference is read by both the *Plan gate* and *Pre-merge
  review* phases.

### `references/finalization.md` (maps §7)
- Clean git-status verification against plan scope, with approval criteria.
- Full final checklist (preconditions verified before invoking
  `/finishing-a-development-branch`).
- Pending-change resolution (which task it belongs to; scope creep → revert or
  separate plan).

No reference re-declares rules that live in `CLAUDE.local.md`; it references
them by § number.

## 7. Utility commands

### `/sbtdd-init` — multi-stack scaffolding (idempotent)
1. **Detect stack** — `Cargo.toml`→Rust, `pyproject.toml`/`setup.py`→Python,
   `CMakeLists.txt`→C/C++. If ambiguous/none → ask (`AskUserQuestion`).
2. **Write `CLAUDE.local.md`** from `templates/CLAUDE.local.md.tmpl`, injecting
   the correct §0.1 block from `templates/verification/<stack>.md`, the §4 stack
   section, and resolving placeholders `{ErrorType}`, `{Author}` (ask or mark
   `TODO`).
3. **Write/merge `.claude/settings.json`** with the 3 TDD-Guard hooks (§4.1).
   If it exists: **back it up first** (`settings.json.bak`), parse it, append only
   the hooks not already present, **never touch keys other than `hooks`**, and show
   the resulting diff + backup path before writing. (Per the no-scripts decision
   this merge is LLM-performed; the backup + show-diff is the safety net — see §13
   residual risks.)
4. **Create dirs** `sbtdd/` and `planning/`.
5. **Seed `sbtdd/spec-behavior-base.md`** from template if absent.
6. **Update `.gitignore`**: add `CLAUDE.local.md`, `CLAUDE.md`, `.claude/`,
   `sbtdd/`, `planning/` (see §9). Nothing of the SBTDD process is tracked.
7. **Report** what was created/skipped (idempotent: no clobber) and remind to
   install `tdd-guard` + the stack reporter, then run `/sbtdd-check`.

### `/sbtdd-check` — environment verifier (read-only)
Emits a pass/fail checklist with per-item remediation; does not fix — routes to
`/sbtdd-init` for anything missing.

Checks are **PowerShell-first** (`Get-Command`, `ConvertFrom-Json`) — no hard
dependency on `jq`/`which`; POSIX equivalents are documented as fallback.

| # | Verifies | How |
|---|---|---|
| 1 | `CLAUDE.local.md` present with rule sections | existence + key sections |
| 2 | 3 TDD-Guard hooks active | `ConvertFrom-Json` on `.claude/settings.json` (fallback `jq '.hooks'`) |
| 3 | `sbtdd/` and `planning/` exist | — |
| 4 | `.gitignore` has the local-only entries | grep the 5 entries |
| 5 | `tdd-guard` binary + stack reporter on PATH | `Get-Command` (fallback `which`) |
| 6 | State file consistent (if present) | light drift check vs git/plan |
| 7 | Delegated skills/plugins available | superpowers skills + `magi:magi` present; **fail loud** listing any missing |

## 8. Error handling & edge cases

Guiding principle: **on ambiguity or inconsistency, stop and ask — never guess.**

| Situation | Plugin response | Source |
|---|---|---|
| Project not initialized (no `CLAUDE.local.md`) | `/sbtdd` stops → route to `/sbtdd-init` | preflight |
| Drift (state `green` vs last commit `refactor:`) | Abort and escalate | §2.1 |
| State file corrupt/missing | Recover from plan (last `[x]`) + git (last commit) → confirm with user | §2.1 |
| Plan gate < threshold after 3 iterations | Escalate (likely spec defect) | §1 safety valve |
| MAGI < `GO WITH CAVEATS` after 3 iterations | Escalate (plan defect / divergence / approach) | §6 safety valve |
| Parallelism + TDD-Guard same worktree | Refuse → require worktrees or toggle off | §3 |
| Spec vs plan ambiguity | `spec-behavior.md` wins | §3 |
| Test passes without implementation | Stop, report false positive | §3 |
| `/sbtdd-init` on already-initialized repo | Idempotent: skip files, merge hooks | §7 |
| Stack undetectable | Ask (`AskUserQuestion`) | §7 |

## 9. Tracking policy (override of the template)

The template kept `sbtdd/` and `planning/` git-tracked as team-coordination
artifacts. **This design overrides that:** `sbtdd/` and `planning/` are
**gitignored**. The entire SBTDD process (spec, plan, state) is local to the
developer; git records source code and the TDD-cycle commits only.

Consequences:
- The scaffolded `CLAUDE.local.md.tmpl` §1 must be rewritten: the hierarchy
  table marks `sbtdd/*` and `planning/*` as "No — gitignored", and the §1
  rationale ("team coordination via tracked `sbtdd/`, `planning/`") is replaced
  by "the whole SBTDD process is developer-local". Without this the rules would
  say "commit the plan" while `.gitignore` excludes it (contradiction).
- §2.1 authority order still holds (git = canon of past code; state file =
  present; plan = future, as an on-disk file).
- If the team ever needs to share spec/plan, it must use a channel other than
  git.

## 10. Testing strategy

Skills/commands are markdown, so the pytest suite can only assert **content
presence** (tokens/sections present), not behavior. Be honest about this: a green
pytest run is a **presence/lint signal**, not proof of correct behavior. The
**required acceptance gate** is items 1–5 below (plugin-validator + the manual
behavioral evals), not the substring suite.

- **Presence/lint (pytest, automated, necessary-not-sufficient):** valid
  `plugin.json`, skill frontmatter, required sections per artifact, cross-reference
  integrity, and **drift checks** — referenced section names actually exist in
  `CLAUDE.local.md.tmpl`, and every delegated skill name is in the allowlist.

**Required acceptance gate (must pass before "done"):**
1. **Structural validity** — `plugin-dev:plugin-validator` reports no errors.
2. **Triggering eval** — skill `description` fires when expected.
3. **Per-stack scaffolding dry-run** — run `/sbtdd-init` in 3 throwaway repos
   (Rust/Python/C++); verify each writes the correct §0.1, `.claude/settings.json`
   merge preserved prior keys (created a `.bak`), and `/sbtdd-check` passes all 7
   items.
4. **Routing-table coverage** — for each state (artifacts created by hand),
   confirm `/sbtdd` announces the correct phase **with the evidence it found**;
   include a drift case that must abort & escalate.
5. **Idempotency** — `/sbtdd-init` twice: no clobber, hooks not duplicated.
6. **`.gitignore`** — verify the 5 entries (incl. `sbtdd/`, `planning/`) and
   that `git status` does not show those artifacts.

## 11. Master mapping (template § → plugin artifact)

| § template | Lands in | Type |
|---|---|---|
| §0 Code standards | `CLAUDE.local.md.tmpl` | rule |
| §0.1 Per-phase verification | `templates/verification/<stack>.md` | rule (multi-stack) |
| §1 Spec→plan→execution flow | `SKILL.md` (routing) + `references/routing.md` | procedure |
| §2 Artifact contract + state-file schema | `CLAUDE.local.md.tmpl` (referenced by skill) | rule |
| §2.1 Authority order + drift | `references/routing.md` | procedure |
| §3 TDD cycle | `references/tdd-cycle.md` | procedure |
| §4 Stack + TDD-Guard hooks | `CLAUDE.local.md.tmpl` §4 + `settings.json.tmpl` | rule + config |
| §5 Commit conventions | `CLAUDE.local.md.tmpl` (referenced) | rule |
| §6 Code review (dual loop + MAGI) | `references/review-gates.md` | procedure |
| §7 Finalization | `references/finalization.md` | procedure |

## 12. Component isolation summary

- **`/sbtdd` command** — input: none; output: invokes skill. Depends on: skill.
- **`sbtdd` skill** — input: project artifacts + state file; output: next-phase
  execution. Depends on: references, scaffolded `CLAUDE.local.md`, superpowers
  skills.
- **references/** — input: read by skill; output: phase-specific protocol.
  Depend on: nothing (point to `CLAUDE.local.md` by § number).
- **`/sbtdd-init`** — input: target repo + stack; output: scaffolded rules,
  hooks, dirs. Depends on: `templates/`.
- **`/sbtdd-check`** — input: target repo; output: pass/fail report. Depends on:
  nothing (read-only).
- **templates/** — static assets; no dependencies.

## 13. MAGI review revisions (2026-05-23)

MAGI verdict on design+plan: **GO WITH CAVEATS (3-0)** (all CONDITIONAL). Findings
processed via `superpowers:receiving-code-review`. User decisions on the structural
caveats:

- **D7 kept unchanged** — `sbtdd/`/`planning/`/state stay gitignored. Accepted
  trade-off: **no cross-machine continuity and no git audit trail** of spec/plan/
  state. Local cross-session resumability is unaffected (files persist on disk);
  recovery follows §2.1. (Declined: revert tracking; declined: export/backup path.)
- **Settings target kept** — hooks stay in `.claude/settings.json` (not
  `settings.local.json`). The convention-inversion MAGI flagged is accepted; all of
  `.claude/` is gitignored either way.
- **No helper scripts** — file operations stay LLM-performed (declined a shipped
  Python merge/probe script).

**Low-risk caveats applied** (this revision): defensive settings merge (backup +
diff, `hooks`-only) in `/sbtdd-init` (§7); `/sbtdd-check` PowerShell-first + new
item 7 (delegated-skill availability preflight) (§7); testing reframed — pytest is
presence/lint, plugin-validator + manual behavioral evals are the required gate
(§10); routing announces the evidence it found and confirms on ambiguity; references
use section **names** + a drift check; `magi:magi` fully qualified.

**Consciously-accepted residual risks** (consequence of the no-scripts + keep-settings
decisions): the **merge-clobber** critical is *mitigated, not closed* — its safety
net is the backup + show-diff + manual validation, not a deterministic tested
script; and the deterministic-behavior test gap remains (pytest stays substring-based,
so the manual gate in §10 carries the real assurance).
