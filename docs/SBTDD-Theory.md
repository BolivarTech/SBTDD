# SBTDD: The Theory Behind Spec + Behavior + Test-Driven Development

> How a disciplined, gated workflow turns a fast-but-careless code generator into
> a producer of *quality* code — and why it matters most when the author is an LLM.

---

## 1. The problem SBTDD solves

A large language model is an extraordinary code *generator* and a mediocre code
*engineer*. Left to a single prompt, it tends to fail in predictable, well-studied
ways:

- **It collapses three questions into one.** "Write the feature" fuses *what to
  build* (specification), *how it should behave* (behavior), and *whether it
  works* (verification). When these blur, the model optimizes for plausible-looking
  output, not for correctness.
- **It hallucinates with confidence.** Plausible-but-wrong APIs, invented package
  names, off-by-one logic, and silently incorrect edge cases are emitted with the
  same fluency as correct code.
- **It over-builds.** Asked for X, it ships X plus three speculative features,
  enlarging the surface area that can break.
- **It drifts.** Over a long task it loses track of what was decided, re-litigates
  settled choices, and edits things outside the request.
- **It can't tell you what it didn't test.** "It should work" is not evidence.

These are not Claude-specific defects; they are properties of *next-token
generation under uncertainty*. You cannot prompt them away. You can, however,
**structure the work so the failure modes are caught mechanically** — and that is
exactly what SBTDD does.

---

## 2. The three disciplines SBTDD composes

SBTDD is not a new methodology invented from scratch. It is the deliberate
*composition* of three proven software disciplines, kept separate and applied in
order. Each one targets a specific failure mode above.

### Spec-Driven (SDD) — *what* and *why*, written down first

Before any code, the objective and the functional requirements are captured in a
spec (`spec-behavior-base.md` → `spec-behavior.md`). This creates a **stable
reference of intent**. When the implementation and the spec disagree, the spec
wins — the model cannot quietly substitute its own idea of the feature.

> **Targets:** scope drift, hallucinated/unrequested behavior, ambiguity.

### Behavior-Driven (BDD) — *how it should behave*, as scenarios

Expected behavior is expressed as **Given / When / Then** scenarios, and tests are
**named after behavior, not implementation**:

```
❌ test_parse_returns_ok
✅ test_parse_ignores_trailing_whitespace_in_values
```

A behavior-named test is an executable sentence about intent. Six months later it
still reads as documentation; when it fails, the failure *names the broken
behavior*.

> **Targets:** unreadable intent, brittle implementation-coupled tests, regressions.

### Test-Driven (TDD) — *whether it works*, before it exists

Every change follows the strict **Red → Green → Refactor** cycle:

1. **Red** — write a failing test that encodes the desired behavior. It must fail
   *for the right reason* (the behavior is absent), not a compile error.
2. **Green** — write the *minimum* code to pass. No extras.
3. **Refactor** — clean up with the tests as a safety net; behavior must not change.

Each phase closes with a **verification gate** (run the suite, lint, types — clean
output as *evidence*) and an **atomic commit** with a phase-specific prefix
(`test:` / `feat:` / `refactor:`).

> **Targets:** untested code, over-building, unverifiable "it should work" claims.

---

## 3. Why composing them produces *quality* code

The disciplines are valuable individually, but their power compounds when ordered
and gated. Quality is not asserted at the end — it is **manufactured at every
step** by mechanisms that make the bad outcome hard to reach:

| Mechanism | What it guarantees |
|-----------|--------------------|
| **Test before code** | No line of production code exists without a test that demanded it. The test set *is* the executable spec. |
| **Minimum-to-pass (Green)** | The model builds only what a test requires — YAGNI enforced, surface area minimized. |
| **Spec precedence** | Behavior absent from the spec is not implemented; ambiguity is resolved against the spec, not invented. |
| **Atomic, prefixed commits** | History is bisectable and reviewable; each diff has one purpose. A regression can be located, not guessed at. |
| **Per-phase verification gate** | Every transition ships *evidence* (command output), never an assertion of success. |
| **State machine + drift detection** | The active task/phase is tracked; if the recorded state and git history disagree, the flow **aborts and escalates** instead of compounding a desync. It fails *safe*. |
| **Human gates** | Plan approval and the review verdict are explicit stops the agent cannot auto-approve — design errors are caught before they propagate into dozens of commits. |

The throughline: **the value is the sequencing and the gates, not "code got
written."** A green test suite at the end is the *consequence* of a process that
refused to advance on unverified work — not a box ticked afterward.

---

## 4. Why this matters *specifically* in Claude Code

SBTDD is doubly valuable when the author is an LLM, because each LLM failure mode
from §1 maps to a counter-mechanism, and Claude Code provides the substrate to
enforce it rather than merely suggest it.

| LLM failure mode | SBTDD counter | Claude Code enforcement |
|------------------|---------------|--------------------------|
| Confident hallucination | Test-first: the test fails until the behavior is *actually* present | **TDD-Guard** hooks intercept writes in real time |
| Over-building | Green = minimum-to-pass | TDD-Guard blocks production code beyond what tests require |
| Scope drift | Spec precedence + state machine | The orchestrator routes by *project state*, not by the model's memory |
| "It should work" | Verification gate with evidence | `verification-before-completion` demands command output before any success claim |
| Single-pass blind spots | Multi-perspective review | The `magi` gate runs three adversarial reviewers |

Two properties of Claude Code make SBTDD *enforceable* rather than aspirational:

**1. Physical enforcement via hooks (TDD-Guard).** A `PreToolUse` hook inspects
every `Write`/`Edit` *before it happens*. Writing production code during the Red
phase, or a test that passes without implementation, is **physically blocked** —
not gently discouraged. Discipline that depends only on the model "remembering the
rules" degrades over a long session; a hook does not.

**2. Orchestration via skills, with state-based routing.** The flow is driven by a
small orchestrator that **inspects the project** (which artifacts exist, what the
state file says) and runs the next phase, delegating each phase to a focused,
single-purpose skill. Because routing is anchored to *files on disk* and the
recorded state — not the model's fallible recollection — the workflow is
**resumable**: a half-finished plan picks up cleanly in a fresh session, and
contradictions are detected instead of papered over.

A third property — **scoped autonomy** — is what makes hands-off execution safe.
The agent commits autonomously *only* under an approved plan, within rules it was
explicitly handed. Outside that envelope it stops and asks. Autonomy is granted by
a gate, not assumed.

---

## 5. Layered enforcement (defense in depth)

SBTDD does not trust any single safeguard. Quality is protected by four
independent layers, so a gap in one is caught by another:

1. **Skill discipline** — `test-driven-development` guides the model through each
   cycle correctly.
2. **Physical enforcement** — TDD-Guard hooks block protocol violations at write
   time, regardless of what the model intended.
3. **Verification gates** — `verification-before-completion` requires evidence
   (real command output) before a phase or task is declared done.
4. **Multi-perspective review** — at the plan checkpoint and again pre-merge, the
   `magi:magi` gate spawns three adversarial reviewers (a scientist, a pragmatist,
   and a critic) and synthesizes a verdict by weighted vote.

That last layer deserves emphasis, because it directly attacks the *cognitive*
biases of a single reviewer (including a single LLM reviewing its own work):
confirmation bias, anchoring, and optimism bias. Three independent evaluators with
different priorities rarely share the same blind spot, and the critic's job is to
*find fault*, not to agree. Disagreement between them is signal, not noise.

---

## 6. Why MAGI is vital — the layer the others cannot replace

Every safeguard in §5 except the last checks the *same thing*: does the code do
what the tests say? Tests, TDD-Guard hooks, and the verification gate are all
forms of **mechanical correctness** — invaluable, but they share one blind spot:
**they can only check what someone thought to encode.** They cannot test the
wisdom of the plan, the soundness of a design trade-off, or the bug no one
anticipated.

That leaves two gaps that are *structural*, not incidental — and in an LLM
workflow, both are dangerous:

**1. A green suite can implement a wrong plan flawlessly.** You cannot test your
way out of a bad design. If the plan is subtly wrong, every test passes and every
commit is clean while the whole thing heads in the wrong direction. Mechanical
correctness is silent about the *correctness of intent*.

**2. The author is an LLM — and so is any single reviewer.** A model reviewing its
own work, or another instance of the same model, carries the same training, the
same anchoring, the same optimism. Self-review by the author is theater: it
ratifies, it does not challenge. The blind spot is shared, so it survives the
review.

MAGI exists precisely to close these two gaps, and **nothing else in the stack
does**:

- **It evaluates judgment, not just correctness.** Three lenses — a scientist
  (technical rigor), a pragmatist (maintainability and trade-offs), and a critic
  (risk and failure modes) — assess the *design and the decision*, the dimensions
  tests cannot encode.
- **It is independent and adversarial by construction.** The agents analyze
  without seeing one another's output (no anchoring), the critic's job is to *find
  fault* (no groupthink), and the weighted vote penalizes a `reject` more heavily
  than an `approve` (a deliberate correction for optimism bias). Disagreement
  between them is the signal — not a failure to reach consensus.
- **It sits at the two highest-leverage gates.** SBTDD runs MAGI at the **plan
  checkpoint** — before a single line is written, because a bad plan multiplies
  into dozens of bad commits — and again **pre-merge** on the whole accumulated
  diff, where architectural problems hide that no per-task green suite can see.
  These are the two moments when a wrong call is most expensive to discover later.
- **Its verdict is quantified and non-negotiable.** Advancing requires at least a
  `GO WITH CAVEATS` consensus; a stuck review escalates to a human after a bounded
  number of iterations instead of looping forever. "Looks fine to me" becomes an
  auditable decision with a recorded rationale.

Remove MAGI and SBTDD degrades into *a well-tested implementation of a
possibly-wrong plan, signed off by the same mind that wrote it.* That is exactly
the outcome the methodology is built to prevent — which is why MAGI is not an
optional polish step but a **load-bearing gate**.

---

## 7. Evidence: the methodology applied to itself

The strongest argument for SBTDD is that **this plugin was built by it.** The
`sbtdd` plugin was specified with brainstorming, planned with `writing-plans`,
gated by `magi:magi`, implemented Red-Green-Refactor via subagent-driven
development, and reviewed through a multi-iteration pre-merge MAGI loop before its
first release.

That pre-merge review is the proof point. Per-task spec-and-quality reviews had
already passed on every task. Yet running the *whole accumulated diff* through the
multi-perspective gate surfaced **three genuine critical defects that the
per-task reviews missed**:

1. An **off-by-one** in the state-machine's drift detection (it compared the phase
   to the wrong commit prefix).
2. **Invented package names** for an external dependency (a supply-chain footgun).
3. A **fail-closed hook** that, installed before its binary existed, could block
   every edit in a project.

None of these were caught by "the tests pass." They were caught because the
process *required* a final, adversarial, whole-diff review before merge — and then
required fixing them before release. That is what "the value is the gates" means in
practice: the workflow found and removed real bugs that a faster path would have
shipped.

---

## 8. When *not* to use it

Discipline has a cost, and SBTDD is honest about it. The full flow is overhead for
work that does not warrant it:

- **Trivial or exploratory changes** — a typo fix, a one-line config tweak, a
  spike. Use the manual fallback (drive the TDD phases by hand) or skip the
  ceremony entirely.
- **Throwaway prototypes** where the goal is learning, not shipping.

Forcing the full lifecycle on a five-minute change is waste. The judgment of
*when* the stakes justify the structure is itself part of using SBTDD well — the
same way the review gate skips the heavy multi-perspective analysis for questions
with one obvious answer.

---

## In one sentence

> SBTDD makes an LLM produce quality code by refusing to let it advance on
> unverified work — separating intent, behavior, and verification; ordering them;
> and enforcing the order with tests, hooks, state, and adversarial review instead
> of trust.

---

*See the [README](../README.md) for installation and command reference. Authored by
[Julian Bolivar](https://github.com/BolivarTech) (BolivarTech).*
