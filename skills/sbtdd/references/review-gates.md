# sbtdd — Review Gates Reference

This reference covers the two pre-merge review loops, their sequencing,
the MAGI verdict table, and the correction loop with its safety valve.
For commit prefix conventions, see `CLAUDE.local.md` §5.

---

## 0. Plan Gate (Checkpoint 1 → Checkpoint 2)

This reference also serves the **Plan gate** at planning time (see
`references/routing.md`). The plan gate is a strict ordered sequence of two
checkpoints; the canonical flow is `CLAUDE.local.md` §1 (steps 4-7) — do not
duplicate its prose here, only operationalize it.

**Checkpoint 1 — manual review (human gate).** When `planning/claude-plan-tdd-org.md`
exists and no approved `planning/claude-plan-tdd.md` exists yet, the orchestrator
**stops** and presents the original plan to the user for explicit approval.

- **Reject:** capture the user's feedback, re-enter the Planning phase, re-run
  `superpowers:writing-plans` to regenerate `claude-plan-tdd-org.md` with that
  feedback (regeneration overwrites the prior original plan), then re-present
  Checkpoint 1. Repeat until approved.
- **Approve:** proceed to Checkpoint 2. Never run `magi:magi` before Checkpoint 1
  is approved.

**Checkpoint 2 — MAGI review.** After Checkpoint 1 approval, run `magi:magi`
against `sbtdd/spec-behavior.md` + `planning/claude-plan-tdd-org.md`, writing
`planning/claude-plan-tdd.md` from the original plan with the improvements,
iterating until the verdict is `>= GO WITH CAVEATS`. The MAGI verdict table
(§5) and the 3-iteration safety valve (§6) apply identically to this
plan-review loop.

> **Invocation contract:** `magi:magi` is interactive-only — see §7. Headless
> runtimes/dispatchers MUST NOT invoke it via `claude -p` subprocess.

---

## 1. Granularity: What Runs When

| Level | When | What runs |
|-------|------|-----------|
| Per TDD-phase close | At the close of each Red / Green / Refactor phase | `superpowers:verification-before-completion` + atomic commit + `.claude/session-state.json` update (3-step close per `references/tdd-cycle.md`). No MAGI, no `superpowers:requesting-code-review`. |
| Pre-merge (once) | Once, when the plan's finalization checklist is satisfied | Loop 1: `superpowers:requesting-code-review` then Loop 2: `magi:magi` (both mandatory, in strict sequence) |

`magi:magi` runs **once** over the full accumulated diff, not per task or per
TDD cycle. Running it per cycle introduces overhead without additional signal;
MAGI evaluates architectural trade-offs and design decisions at feature scope.

---

## 2. Sequential Independent Dual Loop

When all finalization preconditions are met, execute two review loops in
strict sequential order:

| Loop | Tool | Exit criterion |
|------|------|----------------|
| **Loop 1** | `superpowers:requesting-code-review` | Result is *clean to go* — no `[CRITICAL]` or `[WARNING]` findings pending |
| **Loop 2** | `magi:magi` | Verdict ≥ `GO WITH CAVEATS` |

Loop 2 does not start until Loop 1 exits with clean to go. A fix applied
inside Loop 2 does not automatically re-trigger Loop 1 — unless the fix
introduces a finding that Loop 1 would have caught, in which case Loop 1
must be re-run on the updated diff before returning to Loop 2.

### Why the loops are kept separate

Each loop detects a different class of defect and their verdicts are not
interchangeable. Running both in parallel (or merging them into a single loop)
produces contaminated verdicts: a mechanical `[WARNING]` from `requesting-code-review`
causes MAGI sub-agents (Melchior / Balthasar / Caspar) to emit `CONDITIONAL`
verdicts, degrading consensus to a noisy `GO WITH CAVEATS` or worse, and
hiding design decisions behind mechanical findings. Keeping them sequential and
independent makes each verdict unambiguous.

---

## 3. Step 1 — `superpowers:requesting-code-review`

Automated review against spec, plan, and code standards. The skill produces
prioritized findings (`[CRITICAL]` / `[WARNING]` / `[INFO]`). Procedure:

1. Read all reported findings.
2. Invoke `superpowers:receiving-code-review` to process each finding with
   technical rigor — understand it before acting; reject incorrect suggestions
   with justification rather than implementing them blindly. `[INFO]` findings
   may be deferred with explicit justification.
3. Apply approved fixes — each fix is its own mini TDD cycle (see
   `CLAUDE.local.md` §5 for the `test:` → `fix:` → `refactor:` sequence;
   `fix:` is the authorized prefix for post-review corrections, per
   `CLAUDE.local.md` §5).
4. Each commit in the mini-cycle must pass `superpowers:verification-before-completion`
   before landing.
5. Repeat `superpowers:requesting-code-review` after each fix batch until the
   result is **clean to go** — zero `[CRITICAL]` and zero `[WARNING]` pending.

`magi:magi` does not run until this condition is met.

---

## 4. Step 2 — `magi:magi` (Final Gate)

Multi-perspective evaluation (Melchior / Balthasar / Caspar) over the already
mechanically-clean diff. **Mandatory**, not optional — this is the final
quality gate before merge / PR.

MAGI evaluates what automated review cannot: design trade-offs, architectural
risks, engineering decisions with genuine uncertainty.

> **Invocation contract:** `magi:magi` is interactive-only — see §7. Headless
> runtimes/dispatchers MUST NOT invoke it via `claude -p` subprocess.

---

## 5. MAGI Verdict Table

The minimum acceptable verdict to proceed to merge / PR is **`GO WITH CAVEATS`**.

| Verdict | Action |
|---------|--------|
| `STRONG GO` | Proceed to merge / PR without conditions |
| `GO` | Proceed to merge / PR |
| `GO WITH CAVEATS` | Apply the *Conditions for Approval* reported by MAGI, then proceed. **No re-evaluation needed** if the conditions are low-risk (documentation, additional tests, naming, logging, error messages, comments). **Re-evaluate MAGI** (follow the correction loop below) if conditions involve structural changes — public API signature modifications, contract changes between modules, behavioral changes (not just cosmetic), or introduction / removal of layers / abstractions. |
| `HOLD -- TIE` | **Blocked.** Apply the actions recommended by the individual agents; re-run `magi:magi`. |
| `HOLD` | **Blocked.** Apply the recommended actions; re-run `magi:magi`. |
| `STRONG NO-GO` | **Blocked.** Reconsider the design; this likely requires replanning (return to the Specification phase (see `references/routing.md`)). |

---

## 6. Correction Loop

When `magi:magi` does not approve (verdict below `GO WITH CAVEATS`):

1. Read the reported findings.
2. Invoke `superpowers:receiving-code-review` for each finding — the skill
   applies equally to MAGI findings and automated-review findings. Defer
   `[INFO]` findings with explicit justification.
3. Apply approved fixes using the TDD mini-cycle (`test:` → `fix:` →
   `refactor:`) per `CLAUDE.local.md` §5.
4. Each commit must pass `superpowers:verification-before-completion` before
   landing.
5. Re-run `magi:magi` over the accumulated diff.
6. Repeat until verdict ≥ `GO WITH CAVEATS`.

### 3-Iteration Safety Valve

After **3 iterations** of the correction loop without reaching the threshold,
stop and escalate to the user. Possible causes:

- **The plan had a structural defect** — requires replanning (return to the
  Specification phase (see `references/routing.md`), regenerating the plan
  with the revised spec).
- **The implementation diverged from the plan** — review alignment between the
  accumulated diff and `planning/claude-plan-tdd.md`; correct divergences before
  continuing.
- **MAGI detects concerns intrinsic to the approach** that are not visible in
  the plan — requires redefining `sbtdd/spec-behavior.md` and regenerating the
  plan.

---

## 7. MAGI Invocation Contract

`magi:magi` is an **interactive-only** Claude Code skill. It is supported
only when invoked from an interactive Claude Code session — the orchestrator
agent calling the skill in-band.

### Not supported

Invocation as a captured-pipe subprocess from a headless dispatcher — e.g.
`claude -p "/magi:magi …"` driven by an external script with stdout/stderr
captured but not actively drained. On Windows this triggers stdio-chain
failures (pipe-buffer deadlock, `asyncio.ProactorEventLoop` hangs on
`create_subprocess_exec` under inherited non-TTY stdin, stdin reads against
closed pipes) that block the runner before any review sub-agent is spawned.

### What runtimes and dispatchers MUST do instead

Any headless SBTDD runtime that needs to drive the Plan-gate Checkpoint 2
or Pre-merge Loop 2 review **MUST NOT** invoke `magi:magi` via `claude -p`
subprocess. Acceptable alternatives:

- **Interactive handoff.** Stop the headless run at the gate, hand off to a
  human-driven interactive Claude Code session that completes the MAGI
  review, then resume the dispatcher with the verdict file as input.
- **Direct runner invocation.** If a `magi-runner` CLI is available from
  the MAGI plugin maintainer with an explicit headless contract, invoke it
  directly as a regular Python subprocess (not through `claude -p`).

This contract was added in v0.0.5 after a headless SBTDD-runtime
dispatcher hit the failure modes above when driving `magi:magi` via
`claude -p`. The runtime fix lands in a separate repo; the contract
belongs here so future runtimes read it first.

---

## 8. MAGI Backend Selection

`magi:magi` runs on one of two backends: the default **Claude** backend, or the
**Ollama** backend. This section is the single normative source for how the
orchestrator selects between them; `SKILL.md`, `commands/sbtdd.md`,
`commands/sbtdd-init.md`, and `references/routing.md` point here — they do not
restate the rule.

> **Verifier:** `/sbtdd-check` Check 8 reports the active backend and, when
> `./.claude/magi-ollama.toml` exists, smoke-tests the Ollama backend end-to-end
> (interactive `magi:magi --ollama` on a throwaway input). See
> `commands/sbtdd-check.md`.

### Resolution rule (toml-existence)

On **every** `magi:magi` invocation the orchestrator makes — Plan-gate
Checkpoint 2 (§0) and Pre-merge Loop 2 (§4) — resolve the backend by the presence
of `./.claude/magi-ollama.toml`:

| `./.claude/magi-ollama.toml` | Backend | Invocation |
|------------------------------|---------|------------|
| exists | Ollama | `magi:magi --ollama …` |
| absent | Claude (default) | `magi:magi …` |

The file's existence is the persistent signal — it spans the whole
multi-invocation flow (Checkpoint 2 runs before `.claude/session-state.json`
exists; Loop 2 runs after), so a run started on Ollama stays on Ollama across
resumes **without** a new state-file field. `/sbtdd` invoked **without**
`--ollama` still resolves to Ollama when the toml exists.

### Enabling the Ollama backend

Run `/sbtdd-init --ollama-init`, which delegates to MAGI's `--ollama-init`
(`/magi --ollama-init`) to scaffold `./.claude/magi-ollama.toml` (idempotent).
`.claude/` is gitignored, so the toml (and any API key) is never tracked.

### `/sbtdd --ollama` is fail-closed

`/sbtdd --ollama` explicitly requests the Ollama backend. If
`./.claude/magi-ollama.toml` does **not** exist, the orchestrator **MUST** stop
and instruct the user to run `/sbtdd-init --ollama-init` first. It **MUST NOT**
silently fall back to the Claude backend — failing closed surfaces a
misconfiguration instead of running the wrong backend unnoticed.

### Consistency with §7 (interactive-only)

The `--ollama` backend changes only **which models** run the Melchior /
Balthasar / Caspar trio (Ollama models from `magi-ollama.toml`). The invocation
is still the **interactive** `magi:magi` skill — it is **not** a `claude -p`
subprocess — so the interactive-only contract of §7 holds unchanged.
`--ollama-init` only scaffolds a config file; it is not an interactive review.

### Dependency: MAGI 4.0.1 or newer

`--ollama` and `--ollama-init` are provided by the MAGI plugin and **require
MAGI 4.0.1 or newer**. Building or modifying the MAGI plugin is out of scope for
the SBTDD plugin; if the installed MAGI predates 4.0.1, the Ollama backend is
unavailable and `/sbtdd-init --ollama-init` cannot produce a usable config.

### Backend unavailable, and switching back

If `./.claude/magi-ollama.toml` exists but the Ollama backend is **unavailable**
when MAGI runs — the daemon is unreachable, `ollama signin` was not completed for
`:cloud` models, or the configured trio is missing — MAGI's `--ollama`
**preflight** fails. The orchestrator **MUST** stop and tell the user to verify
the Ollama server (start the daemon / `ollama signin` / pull the configured
models); it **MUST NOT** silently fall back to the Claude backend. The
orchestrator only checks the toml's **presence** — validating the toml's contents
and reaching the models is the MAGI plugin's responsibility (its preflight).

To switch back to the Claude backend, **remove** `./.claude/magi-ollama.toml`;
its absence resolves to Claude per the table above.
