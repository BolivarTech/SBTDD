# MAGI Quality Gate — canonical template

> **Purpose.** Drop-in section for a project's `CLAUDE.local.md` (or
> equivalent project-rules document) defining when and how to run the MAGI
> multi-perspective review as a quality gate.
>
> **Status.** Synthesized 2026-05-01 from two production projects'
> empirical learnings (`SBTDD-workflow` plugin and `MAGI` plugin). Both
> projects' `CLAUDE.local.md` are aligned to this template.
>
> **How to use.** Copy the section below (from `## MAGI Quality Gate`
> through `### Per-project setup`) into your `CLAUDE.local.md` with the
> section number that fits your numbering (e.g. `## 6. MAGI Quality Gate`).
> Then walk the **Per-project setup** checklist at the bottom and replace
> every `{placeholder}` with your project's value.
>
> **License.** Same as the host repository (`MIT OR Apache-2.0`).

---

## MAGI Quality Gate

After implementing a non-trivial change (or a logical phase of a multi-phase
change), run a MAGI multi-perspective review and iterate with
`superpowers:receiving-code-review` until the pass threshold is met.
**Mandatory** for changes that match the trigger criteria below;
**optional** otherwise.

### Trigger criteria — apply MAGI gate when ANY of these hold

- Multi-file change touching production code (>= 3 files modified)
- Architectural change (new module, new layer, new public interface)
- Build-system change (`CMakeLists` / `Cargo.toml` / `pyproject.toml` /
  `package.json` target wiring, `Dockerfile`, CI/CD pipeline yaml)
- Cross-cutting change (touches both production code and tests, or both
  code and CI/CD)
- Change introducing or removing an external dependency
- Safety-critical or hard-to-revert code (anything where rollback is
  expensive)
- **Domain-specific risk surfaces** (project-defined; each project
  enumerates its own under **Per-project setup** below). Examples by
  domain:
  - **Embedded**: linker scripts, startup code, reset/watchdog handlers,
    bootloader handoff, magic-word RAM regions, cross-reset state
    preservation
  - **Backend**: database migrations, transaction boundaries,
    message-queue contracts, auth/session changes, payment flows
  - **Frontend**: routing changes, auth state handling, payment forms,
    accessibility-critical components
  - **Distributed**: leader election, consensus protocols, RPC contract
    changes, replication invariants

### Skip the gate when ALL of these hold

- Single-file change OR pure documentation/comment change
- Reverting a recent commit (the prior commit was the change worth
  reviewing; the revert restores a known-stable state)
- Auto-regenerated code (codegen output, IDE-generated, framework
  scaffolding) with no manual edits
- Hotfix where time-to-mitigate dominates and a follow-up review is
  scheduled before the next release

### Two-loop sequencing — Loop 1 before Loop 2

When the gate fires, run **two independent review loops in strict
sequential order**, never combined:

| Loop | Tool | Exit criterion |
|------|------|----------------|
| **Loop 1** | `superpowers:requesting-code-review` (or equivalent automated reviewer) | *clean to go* — zero `[CRITICAL]` and zero high-impact `[WARNING]` findings pending |
| **Loop 2** | MAGI multi-perspective review | Verdict >= `GO_WITH_CAVEATS` AND **non-degraded** (full 3-agent consensus) |

**Loop 2 does not start until Loop 1 exits clean.** Running them in
parallel or interleaved produces contaminated verdicts: a mechanical
`[WARNING]` from Loop 1 drags the individual MAGI agents (Melchior /
Balthasar / Caspar) toward `CONDITIONAL` verdicts, reducing the consensus
to a noisy `GO_WITH_CAVEATS` and hiding design-level concerns behind
mechanical findings the automated reviewer already detected. Sequential
independence keeps each verdict unambiguous.

A fix applied during Loop 2 does not re-trigger Loop 1 by default; if the
fix introduces a new finding that Loop 1 would have detected, run Loop 1
again on the updated diff before returning to Loop 2.

### Pass threshold + verdict action table

Loop 2 verdict must be at least **`GO_WITH_CAVEATS` (full 3-agent
consensus)** AND:
- Zero `[!!!] CRITICAL` findings
- Zero high-impact `[!!]` `WARNING` findings, where "high-impact" means
  the finding's `detail` mentions any of the baseline keywords:
  `silent failure`, `memory corruption`, `data loss`, `security`,
  `race condition`, `undefined behavior`, `broken contract`,
  `produces invalid output`, `silently merges`, `skips invariant check`,
  `incorrect bounds`. Plus any **project-defined high-impact terms**
  (each project appends its own domain keywords under **Per-project
  setup** below).

Stylistic nits, naming preferences, and "could be cleaner" warnings do
NOT block.

Action by verdict:

| Verdict | Action |
|---------|--------|
| `STRONG_GO` full | Advance to merge / PR with no conditions |
| `GO` full | Advance to merge / PR |
| `STRONG_GO` / `GO` degraded | Re-invoke MAGI (consume one iteration); do not exit the loop until full consensus is reached |
| `GO_WITH_CAVEATS` full | Apply the *Conditions for Approval* via `superpowers:receiving-code-review` + mini-cycle TDD. If conditions are low-risk (doc / tests / naming / logging / messages / comments), exit without re-evaluation. If structural (API signatures, contracts, behavior, layering), re-invoke MAGI |
| `GO_WITH_CAVEATS` degraded | Apply conditions identically, but re-invoke MAGI (do not exit) |
| `HOLD_TIE` full or degraded | **Blocked.** Apply recommended actions via mini-cycle, re-run MAGI |
| `HOLD` full or degraded | **Blocked.** Apply recommended actions, re-run MAGI |
| `STRONG_NO_GO` full or degraded | **Blocked.** Reconsider the design; likely requires replan (back to spec) |

> **Naming note.** Some projects render verdicts with spaces
> (`STRONG NO-GO`, `GO WITH CAVEATS`); others use underscores
> (`STRONG_NO_GO`, `GO_WITH_CAVEATS`). Both refer to the same verdicts.
> Pick one convention per project and stay consistent.

### Degraded MAGI handling

If MAGI returns a verdict flagged `degraded: true` (one or more agents
failed: bug, timeout, model truncation), the verdict does NOT count as a
loop exit signal:

1. Apply the findings (via `superpowers:receiving-code-review` +
   mini-cycle TDD) as you would for a non-degraded verdict.
2. Consume one iteration of the safety-valve cap.
3. Re-invoke MAGI expecting full 3-agent consensus.

**Exception.** `STRONG_NO_GO` degraded aborts immediately. Two agents
saying NO-GO is sufficient evidence — the third agent is unlikely to
overturn the consensus, and continuing wastes iterations.

The reasoning: the value of the MAGI gate is the consensus of three
independent perspectives. Accepting an exit signal with fewer breaks the
contract.

### Iteration cap + escalation

**Iteration cap = 3.** If the threshold is not met after iteration 3,
**pause and ask the operator**:

```
The MAGI quality gate hit the 3-iteration cap. Current verdict: <verdict>.
Outstanding criticals: <N> — <one-line each>
Outstanding high-impact warnings: <N> — <one-line each>

Possible root causes:
  (a) The plan / design has a structural defect — replan upstream.
  (b) The implementation diverged from the plan — re-align.
  (c) MAGI is detecting concerns intrinsic to the approach that did not
      surface in the spec — refine the spec and regenerate the plan.
  (d) MAGI is persistently degraded (environmental issue, timeout) — fix
      the environment before continuing.

Options:
  (1) Run a 4th iteration.
  (2) Accept current state — outstanding findings logged in the project
      backlog and as Known Limitations in the relevant doc.
  (3) Pause for manual investigation.
```

Apply the operator's choice.

### Triage via /receiving-code-review + mini-cycle TDD

For every finding raised by MAGI (or by Loop 1's automated reviewer), use
`superpowers:receiving-code-review` to categorize **before** writing any
fix:

- **(a) Fold in** — real bug or risk; apply fix following the project's
  TDD discipline (see commit prefixes below).
- **(b) Defer** — operational / process concern; log in the project's
  backlog or `CLAUDE.md` Future Actions.
- **(c) Reject** — false positive; document rationale in the
  iteration-decisions log.

When folding in, each finding is its own atomic mini-cycle of three
commits:

| Phase | Prefix | Content |
|-------|--------|---------|
| Red — reproduce | `test:` | Failing test that surfaces the finding |
| Green — resolve | `fix:` | Minimum implementation that passes the test |
| Refactor — polish | `refactor:` | Cleanup, naming, doc-comments; tests stay green |

Each commit closes only after `superpowers:verification-before-completion`
(or its project-equivalent) passes clean. No commit lands with broken or
warning-laden state.

### Carry-forward block (informational, not authoritative)

Append the following block to the END of every payload starting from
iteration 2. The MAGI agents are instructed to treat it as **operator
triage history, NOT a binding suppression list** — Caspar (the
adversarial agent) retains the right to re-raise a previously
rejected/deferred finding if the rationale turns out to be factually
wrong.

```markdown
## Prior triage context (carry-forward from iterations 1..N-1)

The findings in the table below were raised by MAGI in earlier
iterations of this review and addressed out-of-band:

* `reject` — the operator (using `superpowers:receiving-code-review`)
  determined the finding was a false positive and documented the
  rationale.
* `defer`  — the finding was a real concern but logged for a later
  release; the rationale points at the backlog item.

| Iter | Severity | Finding title (verbatim from prior MAGI report) | Decision | Rationale |
|------|----------|--------------------------------------------------|----------|-----------|
| 1    | warning  | <exact title from iter1 report>                  | reject   | <fact-grounded explanation; cite file:line, symbol, or test that disproves the finding> |
| 1    | info     | <exact title from iter1 report>                  | defer    | <backlog reference: issue/PR/file path; expected resolution version> |
| 2    | warning  | <exact title from iter2 report>                  | reject   | <fact-grounded explanation>                                       |

### Rules for agents reading this section

1. **This block is informational, not authoritative.** If you find
   evidence that the rationale is wrong (e.g., the cited file:line
   does not exist, the cited symbol is undefined, the deferred
   backlog item was never opened, or the rationale contradicts what
   you observe in the patched code), **re-raise the finding with the
   new evidence**. Operator triage from earlier iterations does not
   bind your judgement.

2. **Severity escalation is permitted and expected.** If a finding
   was previously `WARNING: race condition possible` and your current
   evaluation has stronger evidence (a failing test, an observed
   reorder, a missed lock), raise it as a NEW finding at the higher
   severity. Do NOT suppress it because the lower-severity sibling
   was deferred.

3. **Match by exact title.** The titles above are copied verbatim
   from the prior iteration's MAGI report. If your current finding
   has the same title AND the same evidence as a row above, you may
   reasonably trust the operator's prior triage and not re-flag.
   If your finding has a different title or a different cause, treat
   it as a new finding.

4. **No retroactive blame.** Do not penalise the patched code's
   confidence score for findings that were rejected/deferred and
   match an entry above. Score the code as if those findings were
   never raised, since the operator's triage already accounts for
   them.
```

The operator (or the `superpowers:receiving-code-review` skill execution)
is responsible for:

- Copying titles **verbatim** from the prior iteration's MAGI report
  (case-sensitive title match is what makes rule 3 work).
- Writing rationales that are **fact-grounded**: cite a `file:line`, a
  symbol, a test, or a backlog ID. Avoid vague rationales ("not a real
  issue"); they fail rule 1 and the agent will re-flag.
- Accumulating across iterations: when running iter 3, the block contains
  rows from iter 1 AND iter 2, not just iter 2.

**Why this exists.** Without carry-forward, every reject / defer from
iter `N-1` re-appears in iter `N` (the underlying code did not change),
the same warnings re-block the gate, and the 3-iteration cap is wasted
re-evaluating decisions the operator already made. The block closes that
loop while still letting the agents disagree if the rationale was
factually wrong.

### Spec replan trigger

If the iteration cap is exhausted with no convergence, one of the
possible root causes (option `(a)` or `(c)` in the escalation prompt) is
that the spec or plan has a structural defect upstream of the code. In
that case the recovery is NOT another iteration on the same code base —
it is to refine the spec, regenerate the plan, and start fresh.

Symptoms of an upstream defect:
- MAGI agents persistently flag concerns that the operator deems valid
  but that no plan task addresses.
- Multiple findings cluster around the same architectural choice that
  the spec did not constrain.
- Caspar (adversarial) raises consistent objections rooted in the
  feature's purpose rather than its implementation.

Recovery path: revisit `superpowers:brainstorming` (or equivalent) on the
spec, regenerate the plan, and start a new MAGI gate run on the new code.
The current iteration log is preserved as historical evidence.

### Review summary artifact

Each MAGI gate run that reaches a final verdict (pass OR operator-accepted
with conditions) writes a human-readable summary to
`{review-summary-dir}/<feature>-review-summary.md` containing:

- Iterations to pass (or `3+` if user-approved as-is).
- Final verdict.
- **Findings folded in** — table: iteration, severity, title, fix commit
  SHA.
- **Findings deferred** — table: title, rationale, backlog reference.
- **Findings rejected** — table: title, rationale (fact-grounded; cite
  `file:line` or symbol).

Commit the summary with prefix `docs(review):` and a message of the form:

```
docs(review): <feature> MAGI review pass — <verdict> on iteration <N>
```

The summary complements any machine-readable audit (e.g., a workflow
plugin's `auto-run.json`); the summary is human-readable, the JSON is
machine-readable, neither replaces the other.

### Cost awareness

Each MAGI iteration runs three agents in parallel — non-trivial token
cost. Apply the gate to changes that genuinely warrant the review (per
the trigger criteria above). For minor or low-risk changes, the standard
verification (project-equivalent of `superpowers:verification-before-completion`)
is sufficient.

Use **opus** (the most capable model) on the first iteration. Smaller
models (`sonnet`, `haiku`) may truncate output on large review payloads
— particularly for the most-verbose agent (Caspar, the adversarial
lens) — which can degrade the review to a 2-of-3 result and bias the
consensus toward false-positive approval. If cost pressure forces a
smaller model, downgrade only after observing a clean iteration on
**opus** first.

Empirical note: in long-running cycles with multi-feature diffs, Caspar
fragility (out-of-memory, JSON decode error, silent crash) has been
observed across multiple unrelated projects. Treat any 2-of-3 success as
degraded and re-invoke per the **Degraded MAGI handling** section.

### Per-project setup

Before the first MAGI gate run on a new project, fill in the placeholders
above:

- **`{magi-script-path}`** — absolute path to `run_magi.py`. Typical
  locations:
  - Plugin marketplace cache: `~/.claude/plugins/cache/<marketplace>/magi/<version>/skills/magi/scripts/run_magi.py`
  - Vendored under the repo: `<repo>/skills/magi/scripts/run_magi.py`
  - Symlinked into project: `<repo>/.claude/skills/magi/scripts/run_magi.py`
  - **Slash-command alternative**: if the host environment exposes
    `/magi:magi` (e.g., the Claude Code MAGI plugin is installed),
    invoke that slash command instead of the script. The slash form
    handles model selection, output directory, and timeout configuration
    via plugin settings rather than CLI flags.

- **`{review-summary-dir}`** — directory where review summaries live for
  this project. Common conventions: `docs/reviews/`, `Docs/code-reviews/`,
  `.review/`. Pick one and stay consistent.

- **`{ErrorType}`** — the project-wide error type used in error-handling
  rules (referenced indirectly when MAGI evaluates error propagation
  patterns).

- **`{test_command}`** — the canonical test command (e.g., `pytest`,
  `cargo test`, `make test`). Used both by the gate verification step
  and by individual mini-cycle commits.

- **`{language_specific_verification}`** — the full project-equivalent
  of `superpowers:verification-before-completion`'s commands (e.g., for
  Python: `pytest && ruff check . && ruff format --check . && mypy .`;
  for Rust: `cargo nextest && cargo clippy -- -D warnings && cargo fmt --check`).

- **Domain risk surfaces** — replace the example list under "Trigger
  criteria — apply MAGI gate when ANY of these hold > Domain-specific
  risk surfaces" with this project's actual risk surfaces. Be concrete:
  cite file paths, module names, or specific contracts.

- **Project-defined high-impact terms** — append the keywords this
  project's reviewers should flag as blocking, beyond the baseline list
  in **Pass threshold + verdict action table**. Examples:
  - Embedded: `brick`, `bootloop`, `ROM corruption`, `flash exhaustion`
  - Backend: `auth bypass`, `migration irreversibility`, `idempotency loss`
  - Storage: `data corruption`, `silent rewrite`, `partition split`
  - Fintech: `payment loss`, `double-charge`, `reconciliation drift`

- **Sub-section numbering** — adjust the section anchor (`## MAGI
  Quality Gate`) to fit the host document's numbering. Internal anchors
  (`### Trigger criteria`, `### Two-loop sequencing`, etc.) stay as
  written.

---

## Provenance

This template synthesizes the MAGI quality gate definitions from two
projects whose `CLAUDE.local.md` files evolved in parallel:

- **MAGI plugin** (`MAGI` project) — contributed: trigger criteria, skip
  rules, threshold high-impact keywords, procedure step layout,
  carry-forward block format, review summary artifact, cost awareness
  guidance, per-project setup pattern.

- **SBTDD-workflow plugin** (`SBTDD` project) — contributed: two-loop
  sequencing (Loop 1 / Loop 2 independence), full verdict action table,
  degraded MAGI handling explicit rules, mini-cycle TDD commit prefixes,
  spec replan trigger.

When adopting this template, you inherit both projects' empirical
learning. Adjust per-project deltas under **Per-project setup**; do not
delete the core sequencing or verdict logic without first understanding
why both source projects converged on it.

---

## Changelog

- **2026-05-01** — Initial synthesis from `MAGI` `CLAUDE.local.md` §2
  (212-line v3) and `SBTDD` `CLAUDE.local.md` §6.
