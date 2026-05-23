# sbtdd — Review Gates Reference

This reference covers the two pre-merge review loops, their sequencing,
the MAGI verdict table, and the correction loop with its safety valve.
For commit prefix conventions, see `CLAUDE.local.md` §5.

> **Note:** this reference also serves the Plan gate (Checkpoint 2) described
> in `references/routing.md` — the MAGI verdict table and the 3-iteration safety
> valve apply identically to the plan-review loop at planning time.

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
