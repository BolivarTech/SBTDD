# Cross-project patch: MAGI plugin `CLAUDE.local.md` §2 alignment

**Source repo (this patch lives here):** `SBTDD-workflow` (sibling project).
**Target repo (apply patch there):** `MAGI` plugin project at
`D--jbolivarg-PythonProjects-MAGI`.

**Generated:** 2026-05-01
**Generated against MAGI's `CLAUDE.local.md` v3** (cached at
`/tmp/magi-claude-local.md` for diff reference; 212 lines, sections
§0, §2.1-§2.6).

**Goal:** absorb 5 deltas from SBTDD's `CLAUDE.local.md` §6 "Code review"
that MAGI's §2 lacks. After applying this patch, MAGI's §2 will be
operationally equivalent to `docs/magi-gate-template.md` (modulo
project-specific deltas legitimately specific to MAGI).

**How to apply:** open MAGI project session, edit
`CLAUDE.local.md` directly per the 5 patch entries below. Each entry
specifies INSERT LOCATION + VERBATIM TEXT TO INSERT + RATIONALE.

This artifact is committed to the SBTDD repo as audit trail of the
cross-project sync. Not gitignored. Once applied to MAGI, it can be
left as historical record in SBTDD or deleted (your call).

---

## Patch 1 — Two-loop sequencing (Loop 1 before Loop 2)

### Insert location

NEW sub-section between §2.3 (Pass threshold) and §2.4 (Procedure).
Number it `### 2.3.1 Two-loop sequencing (recommended)` and renumber
`§2.4` and below by +0.5 (or skip renumbering and just append `2.3.1`
without disturbing existing numbers — your choice).

Additionally, ADD a one-line note at the very start of §2.4 Procedure
before step 1: "*This procedure describes Loop 2 (MAGI). It assumes
Loop 1 has already exited clean per §2.3.1.*"

### Verbatim text to insert

```markdown
### 2.3.1 Two-loop sequencing (recommended)

When the gate fires, run **two independent review loops in strict
sequential order**, never combined:

| Loop | Tool | Exit criterion |
|------|------|----------------|
| **Loop 1** | `superpowers:requesting-code-review` (or equivalent automated reviewer) | *clean to go* — zero `[CRITICAL]` and zero high-impact `[WARNING]` findings pending |
| **Loop 2** | MAGI (this section's procedure §2.4) | Verdict >= `GO WITH CAVEATS` AND **non-degraded** (full 3-agent consensus, see §2.4.2) |

**Loop 2 does not start until Loop 1 exits clean.** Running them in
parallel or interleaved produces contaminated verdicts: a mechanical
`[WARNING]` from Loop 1 drags the individual MAGI agents (Melchior /
Balthasar / Caspar) toward `CONDITIONAL` verdicts, reducing the consensus
to a noisy `GO WITH CAVEATS` and hiding design-level concerns behind
mechanical findings the automated reviewer already detected. Sequential
independence keeps each verdict unambiguous.

A fix applied during Loop 2 does not re-trigger Loop 1 by default; if the
fix introduces a new finding that Loop 1 would have detected, run Loop 1
again on the updated diff before returning to Loop 2.
```

### Rationale

SBTDD INV-9 empirical: running automated reviewer + MAGI in parallel
contaminates consensus. The mechanical findings drag agent verdicts and
hide architectural concerns behind syntactic noise. Sequential ordering
keeps each gate's signal clean.

---

## Patch 2 — Verdict action table (extends §2.3 Pass threshold)

### Insert location

APPEND to §2.3 Pass threshold, after the existing paragraph that ends
"Stylistic nits, naming preferences, and 'could be cleaner' warnings do
NOT block." — add a new sub-heading "**Action by verdict:**" plus the
table below.

### Verbatim text to insert

```markdown
**Action by verdict:**

| Verdict | Action |
|---------|--------|
| `STRONG GO` full | Advance to merge / PR with no conditions |
| `GO` full | Advance to merge / PR |
| `STRONG GO` / `GO` degraded | Re-invoke MAGI (consume one iteration); do not exit the loop until full consensus is reached |
| `GO WITH CAVEATS` full | Apply the *Conditions for Approval* via `superpowers:receiving-code-review` + mini-cycle TDD. If conditions are low-risk (doc / tests / naming / logging / messages / comments), exit without re-evaluation. If structural (API signatures, contracts, behavior, layering), re-invoke MAGI |
| `GO WITH CAVEATS` degraded | Apply conditions identically, but re-invoke MAGI (do not exit) |
| `HOLD -- TIE` full or degraded | **Blocked.** Apply recommended actions via mini-cycle, re-run MAGI |
| `HOLD` full or degraded | **Blocked.** Apply recommended actions, re-run MAGI |
| `STRONG NO-GO` full or degraded | **Blocked.** Reconsider the design; likely requires replan (see §2.4 step 6 escalation) |
```

### Rationale

§2.3 currently states the threshold (`GO WITH CAVEATS (3-0)`) but does not
enumerate what action to take per each of the six possible verdicts. The
table makes the verdict-to-action mapping explicit and resolves edge
cases (e.g., `GO WITH CAVEATS` with low-risk vs structural conditions).
SBTDD's §6 verdict table has been used in production across 4+ ship
cycles with zero ambiguity reports.

---

## Patch 3 — Degraded MAGI handling (NEW sub-section)

### Insert location

NEW sub-section between §2.3 (Pass threshold) and §2.4 (Procedure), AFTER
patch 1's §2.3.1. Number it `### 2.3.2 Degraded MAGI handling`.

### Verbatim text to insert

```markdown
### 2.3.2 Degraded MAGI handling

If MAGI returns a verdict flagged `degraded: true` (one or more agents
failed: bug, timeout, model truncation), the verdict does NOT count as
a loop exit signal:

1. Apply the findings (via `superpowers:receiving-code-review` +
   mini-cycle TDD) as you would for a non-degraded verdict.
2. Consume one iteration of the safety-valve cap (§2.4 step 6).
3. Re-invoke MAGI expecting full 3-agent consensus.

**Exception.** `STRONG NO-GO` degraded aborts immediately. Two agents
saying NO-GO is sufficient evidence — the third agent is unlikely to
overturn the consensus, and continuing wastes iterations.

The reasoning: the value of the MAGI gate is the consensus of three
independent perspectives. Accepting an exit signal with fewer breaks
the contract.

**Empirical note.** Caspar fragility chronic across 4+ unrelated cycles
(out-of-memory, JSON decode error, silent crash). Any 2-of-3 success is
degraded by definition; do not exit on it.
```

### Rationale

Empirical: across SBTDD's v0.3.0, v0.4.0 (iter 1 and iter 2), and adjacent
projects, Caspar (adversarial agent) crashed multiple times with valid
output from the other two agents. Without explicit degraded handling, the
operator faces a judgment call: accept 2-agent verdict (cheap, but breaks
the consensus contract) or re-invoke (correct, but the procedure didn't
mandate it). SBTDD made it mandatory in §6 and Caspar fragility has not
caused a cycle abort since.

---

## Patch 4 — Mini-cycle TDD commit prefixes (edit §2.4 step 4)

### Insert location

EDIT §2.4 step 4 sub-bullet `(a) Fold in`. Current text reads:

> **(a) Fold in** — real bug or risk; apply fix following project
> TDD/coding rules (failing test first when testable, implementation,
> green confirmation, atomic commit).

REPLACE with the verbatim text below.

### Verbatim text to insert

```markdown
   - **(a) Fold in** — real bug or risk; apply fix as a 3-commit
     mini-cycle following the project's TDD discipline:

     | Phase | Prefix | Content |
     |-------|--------|---------|
     | Red — reproduce | `test:` | Failing test that surfaces the finding |
     | Green — resolve | `fix:` | Minimum implementation that passes the test |
     | Refactor — polish | `refactor:` | Cleanup, naming, doc-comments; tests stay green |

     Each commit closes only after `superpowers:verification-before-completion`
     (or its project-equivalent) passes clean. No commit lands with broken
     or warning-laden state. The mini-cycle is atomic per finding — never
     batch fixes for multiple findings into a single trio of commits.
```

### Rationale

§2.4 step 4 (a) currently says "atomic commit" (singular) — implying one
commit per finding. SBTDD empirically found that the 3-commit pattern
(test → fix → refactor) gives:
- Better audit trail (verdict regression isolated to which sub-step
  introduced it).
- Atomic verification gate per phase (each commit is verified
  independently).
- Compatibility with TDD-Guard real-time enforcement (one phase per
  commit matches the guard's state machine).

This pattern shipped in SBTDD v0.1+, no friction observed.

---

## Patch 5 — Spec replan trigger (extend §2.4 step 6 escalation)

### Insert location

EDIT §2.4 step 6. Current escalation prompt has 3 options. INSERT a
"**Possible root causes:**" block BEFORE the "Options:" block, listing
4 candidate causes for cap exhaustion.

### Verbatim text to insert

REPLACE the current §2.4 step 6 prompt block with:

```markdown
6. **Iteration cap = 3**. If the threshold is not met after iteration 3,
   **pause and ask the user**:
   ```
   The MAGI quality gate hit the 3-iteration cap. Current verdict: <verdict>.
   Outstanding criticals: <N> — <one-line each>
   Outstanding high-impact warnings: <N> — <one-line each>

   Possible root causes:
     (a) The plan / design has a structural defect — replan upstream
         (return to spec / brainstorming, regenerate the plan).
     (b) The implementation diverged from the plan — re-align the diff
         against the plan's task list before continuing.
     (c) MAGI is detecting concerns intrinsic to the approach that did
         not surface in the spec — refine the spec and regenerate the plan.
     (d) MAGI is persistently degraded (environmental issue, timeout,
         model fragility) — fix the environment before continuing.

   Options:
     (1) Run a 4th iteration.
     (2) Accept current state — outstanding findings logged in CLAUDE.md
         Future Actions and as Known Limitations in the relevant doc.
     (3) Pause for manual investigation.
   ```
   Apply the user's choice.
```

### Rationale

§2.4 step 6 currently presents the user with 3 options but does NOT
help them diagnose WHY the cap exhausted. Without root-cause hints, the
default tends toward option (1) "iter 4" — which often just re-runs the
same impasse. SBTDD's §6 explicit root-cause enumeration produces better
operator decisions:
- Cause (a) (defective plan) → option (3) or replan, not iter 4.
- Cause (b) (divergent impl) → fix the divergence, then iter 4.
- Cause (c) (intrinsic spec problem) → refine spec, regenerate plan,
  start fresh.
- Cause (d) (env / Caspar fragility) → fix env, retry.

Empirical: SBTDD v0.3.0 final review hit cap with cause (c) — refining
the spec was the correct path; iter 4 would have hit the same issues.

---

## Application checklist

When applying this patch in MAGI project session:

- [ ] **Patch 1**: insert §2.3.1 Two-loop sequencing + add note at top of §2.4.
- [ ] **Patch 2**: append "Action by verdict" table to §2.3.
- [ ] **Patch 3**: insert §2.3.2 Degraded MAGI handling.
- [ ] **Patch 4**: replace §2.4 step 4 (a) "Fold in" with mini-cycle TDD pattern.
- [ ] **Patch 5**: extend §2.4 step 6 escalation with "Possible root causes" block.
- [ ] Run `grep -nE '^### 2\.' CLAUDE.local.md` to verify section numbering is consistent (or accept the new `.1` and `.2` sub-sections without renumbering existing ones — both are valid).
- [ ] Cross-check with `docs/magi-gate-template.md` (in SBTDD repo, sibling project) to confirm operational equivalence.
- [ ] Commit MAGI's `CLAUDE.local.md` change. **Note:** MAGI's `CLAUDE.local.md` is gitignored per project policy (same as SBTDD); the edit stays local to your machine. No commit to MAGI repo needed for this patch.

---

## Provenance and verification

This patch synthesizes 5 deltas where SBTDD's `CLAUDE.local.md` §6 has
content MAGI's `CLAUDE.local.md` §2 lacks. The deltas were identified by
direct file-history inspection on 2026-05-01.

After applying this patch, MAGI's §2 will have:
- All 6 sections it currently has (§2.1 - §2.6) — unchanged in content.
- 2 new sub-sections (§2.3.1 Two-loop sequencing, §2.3.2 Degraded MAGI
  handling).
- 1 enhanced section (§2.3 Pass threshold gains action-by-verdict table).
- 2 enhanced steps (§2.4 step 4 (a) gains mini-cycle prefixes, §2.4
  step 6 gains root-cause enumeration).

Together this brings MAGI's §2 to operational equivalence with
`docs/magi-gate-template.md` (in SBTDD repo at the same date), modulo:
- MAGI's reference to a script-path-based invocation (`python {magi-script-path} ...`)
  vs SBTDD's slash-command invocation (`/magi:magi`). Both are documented
  as alternatives in the template; each project legitimately picks its own.
- MAGI's `CLAUDE.local.md` is shorter and does not have a counterpart to
  SBTDD's §1 (SBTDD methodology), §3 (TDD cycle), §4 (stack), §5 (Git),
  §7 (Finalization). Those sections are project-specific and out of
  scope for this patch.

If MAGI's §2 changes between this patch's generation date (2026-05-01) and
the application date, regenerate the patch by re-diffing against the
new content.
