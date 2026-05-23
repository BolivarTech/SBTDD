# SBTDD Orchestrator Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable Claude Code plugin (`sbtdd`) that orchestrates the SBTDD multi-agent workflow via a single state-routed `/sbtdd` entry, plus `/sbtdd-init` scaffolding and `/sbtdd-check` verification utilities.

**Architecture:** A thin command `/sbtdd` invokes the `sbtdd` skill, whose `SKILL.md` detects the current phase from project artifacts + `.claude/session-state.json` and delegates to existing superpowers skills; per-phase detail lives in `references/*` (progressive disclosure). The procedural flow (template §1/§3/§6/§7) lives in the skill; the immutable rules (template §0/§2/§4/§5) are shipped as `templates/` assets that `/sbtdd-init` scaffolds into a target repo. The skill points to the scaffolded `CLAUDE.local.md` by § number — single source of truth, no duplication.

**Tech Stack:** Markdown (skills/commands/references), JSON (plugin manifest, settings template), Python + pytest (structural-validation test suite, stdlib-only — no third-party parsing deps).

---

## Canonical sources (REQUIRED READING before any content task)

Two files on disk are the authoritative source for all prose content. Content tasks **adapt/translate** from them; they are not placeholders:

1. **Original template:** `D:\jbolivarg\BolivarTech\AI_Tools\CLAUDE_local_md_SBTDD-Superpowers_template.md` — the full SBTDD rules + procedure in Spanish. Each content task cites the exact § to adapt.
2. **Approved design:** `docs/superpowers/specs/2026-05-23-sbtdd-orchestrator-plugin-design.md` — decisions D1–D7, structure, delegation table, mapping table, tracking-policy override (§9).

**Language:** all plugin content is **English** (decision D4). When a task says "adapt template §X", translate the Spanish source to English and apply any design overrides noted in the task.

## Conventions for every task

- **Strict TDD (per `~/.claude/CLAUDE.md`):** write the failing test → commit `test:` → implement → commit `feat:`. Add a `refactor:` commit only if cleanup is needed.
- **Commit messages:** English, imperative, ≤72 chars, no AI mentions, no `Co-Authored-By`.
- **Test runner:** `python -m pytest` (install once: `python -m pip install pytest`).
- A "failing test" here legitimately means a test asserting on a file/section that does not exist yet — it fails with `FileNotFoundError` or `AssertionError`. This is the intended Red.
- **Test honesty (MAGI caveat):** the pytest suite asserts *content presence*, not behavior — a green run is a presence/lint signal, not proof of correctness. The **required acceptance gate** is Task 16 Step 5 (`plugin-validator` + the manual behavioral evals); it is **not optional**.

## File structure (decomposition locked here)

```
sbtdd/                                       (repo root — already git-initialized on main)
├── .claude-plugin/plugin.json               # manifest                              [Task 2]
├── skills/sbtdd/
│   ├── SKILL.md                             # orchestrator entry + delegation        [Task 11]
│   └── references/
│       ├── routing.md                       # state detection + drift                [Task 7]
│       ├── tdd-cycle.md                     # per-phase rules + atomic close         [Task 8]
│       ├── review-gates.md                  # dual-loop pre-merge + MAGI table       [Task 9]
│       └── finalization.md                  # final checklist + clean git status     [Task 10]
├── commands/
│   ├── sbtdd.md                             # thin wrapper → invokes skill           [Task 12]
│   ├── sbtdd-init.md                        # multi-stack scaffolding                 [Task 13]
│   └── sbtdd-check.md                       # environment verifier                    [Task 14]
├── templates/
│   ├── CLAUDE.local.md.tmpl                 # scaffolded rules (§0,§2,§4,§5 + §1)     [Task 5]
│   ├── settings.json.tmpl                   # TDD-Guard hooks                          [Task 4]
│   ├── spec-behavior-base.tmpl.md           # flow input template                      [Task 6]
│   └── verification/{rust,python,cpp}.md    # per-stack §0.1 blocks                    [Task 3]
├── tests/
│   ├── conftest.py                          # ROOT + helpers                           [Task 1]
│   ├── test_manifest.py                                                                [Task 2]
│   ├── test_verification_templates.py                                                  [Task 3]
│   ├── test_settings_template.py                                                       [Task 4]
│   ├── test_claude_local_template.py                                                   [Task 5]
│   ├── test_spec_base_template.py                                                      [Task 6]
│   ├── test_references.py                                                              [Tasks 7-10]
│   ├── test_skill.py                                                                   [Task 11]
│   ├── test_commands.py                                                                [Tasks 12-14]
│   ├── test_readme.py                                                                  [Task 15]
│   └── test_integration.py                  # cross-reference integrity                [Task 16]
├── pyproject.toml                           # pytest config                            [Task 1]
└── README.md                                                                           [Task 15]
```

The `tests/` suite and `pyproject.toml` are repo-dev tooling (validate the plugin); they are not shipped behavior. `.remember/` stays gitignored (already configured).

---

## Task 1: Test harness

**Files:**
- Create: `pyproject.toml`
- Create: `tests/conftest.py`
- Create: `tests/test_harness.py` (sanity test, removed implicitly by being trivial — keep as smoke test)

- [ ] **Step 1: Write the failing smoke test**

Create `tests/test_harness.py`:

```python
from conftest import ROOT


def test_repo_root_resolves():
    assert (ROOT / ".git").is_dir()


def test_design_doc_committed():
    spec = ROOT / "docs/superpowers/specs/2026-05-23-sbtdd-orchestrator-plugin-design.md"
    assert spec.is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_harness.py -v`
Expected: collection error / `ModuleNotFoundError: No module named 'conftest'` (conftest + config not present yet).

- [ ] **Step 3: Create pytest config**

Create `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
pythonpath = ["tests"]
```

- [ ] **Step 4: Create conftest helpers**

Create `tests/conftest.py`:

```python
"""Shared paths and helpers for the plugin structural-validation suite."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    """Return the text of a repo-relative file (UTF-8)."""
    return (ROOT / rel).read_text(encoding="utf-8")


def frontmatter(text: str) -> str:
    """Return the YAML frontmatter block (between the first two '---' lines)."""
    assert text.startswith("---"), "file must start with YAML frontmatter"
    end = text.index("\n---", 3)
    return text[3:end]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_harness.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit (test + harness together — bootstrap exception)**

The harness and its smoke test bootstrap the suite; commit as one `test:` unit.

```bash
git add pyproject.toml tests/conftest.py tests/test_harness.py
git commit -m "test: add pytest structural-validation harness"
```

---

## Task 2: Plugin manifest

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_manifest.py`:

```python
import json
from conftest import ROOT


def _manifest():
    return json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))


def test_manifest_is_valid_json_with_required_fields():
    m = _manifest()
    assert m["name"] == "sbtdd"
    assert m["version"]
    assert "SBTDD" in m["description"]


def test_manifest_lists_expected_keywords():
    m = _manifest()
    assert {"sbtdd", "tdd", "workflow"} <= set(m.get("keywords", []))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: FAIL — `FileNotFoundError: .claude-plugin/plugin.json`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_manifest.py
git commit -m "test: add plugin manifest validation"
```

- [ ] **Step 4: Create the manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "sbtdd",
  "description": "SBTDD orchestrator: drives the Spec + Behavior + Test-Driven Development multi-agent workflow on top of superpowers (spec, plan, MAGI gate, TDD execution, dual-loop review, finalization).",
  "version": "0.1.0",
  "author": { "name": "jbolivarg" },
  "keywords": ["sbtdd", "tdd", "workflow", "orchestrator", "superpowers"]
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add sbtdd plugin manifest"
```

---

## Task 3: Per-stack verification templates

Source: template **§0.1** (Rust / Python / C-C++ verification blocks). These become the `§0.1` content injected by `/sbtdd-init` per detected stack.

**Files:**
- Create: `templates/verification/rust.md`
- Create: `templates/verification/python.md`
- Create: `templates/verification/cpp.md`
- Create: `tests/test_verification_templates.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_verification_templates.py`:

```python
from conftest import ROOT

VDIR = ROOT / "templates/verification"


def test_three_stacks_present():
    for stack in ("rust", "python", "cpp"):
        assert (VDIR / f"{stack}.md").is_file()


def test_rust_has_core_commands():
    t = (VDIR / "rust.md").read_text(encoding="utf-8")
    for cmd in ("cargo nextest run", "cargo clippy", "cargo fmt", "cargo audit"):
        assert cmd in t


def test_python_has_core_commands():
    t = (VDIR / "python.md").read_text(encoding="utf-8")
    for cmd in ("pytest", "ruff check", "ruff format", "mypy"):
        assert cmd in t


def test_cpp_has_core_commands():
    t = (VDIR / "cpp.md").read_text(encoding="utf-8")
    for cmd in ("cmake --build", "ctest"):
        assert cmd in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_verification_templates.py -v`
Expected: FAIL — files missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_verification_templates.py
git commit -m "test: add per-stack verification template checks"
```

- [ ] **Step 4: Create the three verification templates**

Each file contains an English markdown fragment titled "Per-phase verification (run after each Red/Green/Refactor)" with a fenced `bash` block. Transcribe template §0.1 verbatim per stack.

`templates/verification/rust.md`:

````markdown
#### Rust

```bash
cargo nextest run                       # All pass, 0 fail
cargo clippy --tests -- -D warnings     # 0 warnings
cargo fmt --check                       # Clean
cargo build --release                   # Compiles without warnings
cargo doc --no-deps                     # No doc warnings
cargo audit                             # No known vulnerabilities
```
````

`templates/verification/python.md`:

````markdown
#### Python

```bash
pytest                                  # All pass, 0 fail
ruff check .                            # 0 warnings
ruff format --check .                   # Clean
mypy .                                  # No type errors
```
````

`templates/verification/cpp.md`:

````markdown
#### C/C++ (CMake)

```bash
cmake --build build --target all        # Compiles without warnings
ctest --test-dir build                  # All pass, 0 fail
```
````

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_verification_templates.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add templates/verification
git commit -m "feat: add per-stack verification templates"
```

---

## Task 4: TDD-Guard settings template

Source: template **§4.1** (the full `.claude/settings.json` with 3 hooks).

**Files:**
- Create: `templates/settings.json.tmpl`
- Create: `tests/test_settings_template.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_settings_template.py`:

```python
import json
from conftest import ROOT


def _settings():
    raw = (ROOT / "templates/settings.json.tmpl").read_text(encoding="utf-8")
    return json.loads(raw)


def test_settings_template_is_valid_json():
    assert "hooks" in _settings()


def test_settings_template_has_three_tdd_guard_hooks():
    hooks = _settings()["hooks"]
    assert {"PreToolUse", "SessionStart", "UserPromptSubmit"} <= set(hooks)
    # every configured hook command is tdd-guard
    cmds = [
        h["command"]
        for event in hooks.values()
        for group in event
        for h in group["hooks"]
    ]
    assert cmds and all(c == "tdd-guard" for c in cmds)


def test_pretooluse_matcher_covers_write_edit():
    matcher = _settings()["hooks"]["PreToolUse"][0]["matcher"]
    for tool in ("Write", "Edit", "MultiEdit", "TodoWrite"):
        assert tool in matcher
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_settings_template.py -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_settings_template.py
git commit -m "test: add TDD-Guard settings template checks"
```

- [ ] **Step 4: Create the settings template**

Create `templates/settings.json.tmpl` (verbatim from template §4.1):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|TodoWrite",
        "hooks": [{ "type": "command", "command": "tdd-guard" }]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [{ "type": "command", "command": "tdd-guard" }]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{ "type": "command", "command": "tdd-guard" }]
      }
    ]
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_settings_template.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add templates/settings.json.tmpl
git commit -m "feat: add TDD-Guard settings template"
```

---

## Task 5: Scaffolded rules template (`CLAUDE.local.md.tmpl`)

Source: template **§0, §2, §4, §5** (rules) + **§1 rewritten** per design §9 (tracking override). This is the largest content artifact. Adapt to English; apply the tracking override: `sbtdd/` and `planning/` are gitignored, and the §1 rationale becomes "the whole SBTDD process is developer-local".

**Files:**
- Create: `templates/CLAUDE.local.md.tmpl`
- Create: `tests/test_claude_local_template.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_claude_local_template.py`:

```python
from conftest import ROOT

T = ROOT / "templates/CLAUDE.local.md.tmpl"


def _txt():
    return T.read_text(encoding="utf-8")


def test_template_exists_and_is_english():
    t = _txt()
    assert "Mandatory Code Standards" in t  # §0 heading (English)
    assert "Commit" in t                    # §5


def test_keeps_rules_sections_only():
    t = _txt()
    # rules that must be present
    assert "session-state.json" in t        # §2 state schema
    assert "tdd-guard" in t                  # §4 stack/hooks reference
    assert "Co-Authored-By" in t             # §5 commit prohibition


def test_tracking_override_applied():
    t = _txt()
    # sbtdd/ and planning/ are now gitignored, not committed
    assert "planning/" in t and "gitignored" in t
    # the old "team coordination via tracked sbtdd/planning" rationale is gone
    assert "team coordination" not in t.lower() or "developer-local" in t.lower()


def test_has_stack_and_errortype_placeholders():
    t = _txt()
    assert "{ErrorType}" in t
    assert "{Author}" in t
    assert "{StackVerification}" in t  # injection point for templates/verification/<stack>.md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_claude_local_template.py -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_claude_local_template.py
git commit -m "test: add scaffolded rules template checks"
```

- [ ] **Step 4: Create the rules template**

Create `templates/CLAUDE.local.md.tmpl`. Required structure (English; adapt the cited template sections, omit the procedural §3/§6/§7 which live in the skill):

1. **Header** — note this is `CLAUDE.local.md` (gitignored project rules); state that `CLAUDE.md`, `CLAUDE.local.md`, `.claude/`, **`sbtdd/`**, and **`planning/`** are all gitignored (design §9 override).
2. **§0 Mandatory Code Standards** — adapt template §0: defer to `~/.claude/CLAUDE.md` as authoritative; precedence rules.
3. **§0.1 Per-phase verification** — insert the literal token `{StackVerification}` here (the marker `/sbtdd-init` replaces with `templates/verification/<stack>.md`).
4. **§0.2 Project-specific rules** — adapt template §0.2 table with `{ErrorType}` and `{Author}` / version / date file-header placeholders.
5. **§1 Methodology + document hierarchy** — adapt template §1 BUT rewrite the tracking table so `sbtdd/*` and `planning/*` read "No — gitignored", and replace the team-coordination rationale with "the whole SBTDD process is developer-local; git records source code and TDD-cycle commits only" (design §9).
6. **§2 Artifacts & state sources** — adapt template §2 fully (artifact contract table, §2.1 authority order + drift rule, §2.2 state-file schema + field table, §2.3 write protocol, §2.4 rules-vs-state). This is the canonical schema the skill points to.
7. **§4 Stack + §4.1 hooks** — adapt template §4/§4.1; the stack line is filled by `/sbtdd-init`; reference `templates/settings.json.tmpl` content for the 3 hooks.
8. **§5 Git commit conventions** — adapt template §5 fully (authorized prefixes table, "exception under approved plan", always-on rules incl. no `Co-Authored-By`, English-only).

Do NOT include template §3/§6/§7 here — those are the skill's references.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_claude_local_template.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add templates/CLAUDE.local.md.tmpl
git commit -m "feat: add scaffolded project-rules template"
```

---

## Task 6: Spec-behavior-base template

Source: template §1 "Flujo de especificación" (what `spec-behavior-base.md` must contain: objective, SDD requirements, BDD Given/When/Then, constraints, non-goals).

**Files:**
- Create: `templates/spec-behavior-base.tmpl.md`
- Create: `tests/test_spec_base_template.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_spec_base_template.py`:

```python
from conftest import ROOT

T = ROOT / "templates/spec-behavior-base.tmpl.md"


def test_spec_base_has_required_sections():
    t = T.read_text(encoding="utf-8")
    for section in ("Objective", "Requirements", "Given", "When", "Then", "Constraints", "Non-goals"):
        assert section in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_spec_base_template.py -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_spec_base_template.py
git commit -m "test: add spec-behavior-base template checks"
```

- [ ] **Step 4: Create the template**

Create `templates/spec-behavior-base.tmpl.md` — an English skeleton with headings: `# Spec-Behavior Base`, `## Objective`, `## Requirements (SDD)` (bulleted), `## Scenarios (BDD)` with a `Given / When / Then` block, `## Constraints`, `## Non-goals`. Include one filled example scenario as a guide plus `<!-- replace -->` markers.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_spec_base_template.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add templates/spec-behavior-base.tmpl.md
git commit -m "feat: add spec-behavior-base template"
```

---

## Task 7: Reference — routing.md

Source: template §1 (flow preconditions) + §2.1 (authority order, drift, recovery) + §2.2 "Alcance" (autonomous vs manual). Maps design §6 routing.md.

**Files:**
- Create: `skills/sbtdd/references/routing.md`
- Create: `tests/test_references.py` (shared file; this task adds the routing tests)

- [ ] **Step 1: Write the failing test**

Create `tests/test_references.py`:

```python
from conftest import ROOT

REF = ROOT / "skills/sbtdd/references"


def test_routing_present_with_state_detection_table():
    t = (REF / "routing.md").read_text(encoding="utf-8")
    # detection covers every artifact gate
    for art in ("spec-behavior-base", "spec-behavior.md", "claude-plan-tdd-org",
                "claude-plan-tdd.md", "session-state.json"):
        assert art in t
    # authority order + drift abort rule
    assert "authority" in t.lower()
    assert "drift" in t.lower()
    assert "abort" in t.lower() and "escalate" in t.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_references.py -v`
Expected: FAIL — `routing.md` missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_references.py
git commit -m "test: add routing reference checks"
```

- [ ] **Step 4: Create routing.md**

Create `skills/sbtdd/references/routing.md` (English). Required content:
- A **state-detection decision table** (artifact present → phase → action) covering each row from design §5/§6: no base → stop & ask; base only → `/brainstorming`; spec only → `/writing-plans`; org-plan only → Plan gate; approved plan + state≠done → Execution (resume from state); all `[x]` + `phase=done` → Pre-merge review; pre-merge clean → Finalization.
- **Authority order** block: git=past, state file=present, plan=future.
- **Drift detection + recovery**: hard rule (`state=green` but last commit `refactor:` → abort & escalate); recovery from plan last `[x]` + git last commit, then confirm with user.
- **Autonomous vs manual** scope note (when `session-state.json` applies; manual fallback ignores it).
- Cross-reference rule values by `CLAUDE.local.md` § (do not duplicate the state schema — point to §2.2).

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_references.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/sbtdd/references/routing.md
git commit -m "feat: add routing reference"
```

---

## Task 8: Reference — tdd-cycle.md

Source: template §3 (per-phase rules, atomic 3-step close + Refactor fork, TDD-Guard under parallelism). Maps design §6 tdd-cycle.md.

**Files:**
- Create: `skills/sbtdd/references/tdd-cycle.md`
- Modify: `tests/test_references.py` (add tdd-cycle tests)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_references.py`:

```python
def test_tdd_cycle_present_with_phase_rules_and_close():
    t = (REF / "tdd-cycle.md").read_text(encoding="utf-8")
    for phase in ("Red", "Green", "Refactor"):
        assert phase in t
    # atomic 3-step close: verify -> commit -> update state
    assert "verification-before-completion" in t
    assert "atomic commit" in t.lower()
    assert "session-state.json" in t
    # parallelism guidance
    assert "worktree" in t.lower()
    # points to canonical values rather than duplicating
    assert "§5" in t or "CLAUDE.local.md" in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_references.py::test_tdd_cycle_present_with_phase_rules_and_close -v`
Expected: FAIL — `tdd-cycle.md` missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_references.py
git commit -m "test: add tdd-cycle reference checks"
```

- [ ] **Step 4: Create tdd-cycle.md**

Create `skills/sbtdd/references/tdd-cycle.md` (English). Required content:
- **Per-phase rules table** (Red/Green/Refactor → allowed vs blocked), from template §3 "Reglas por fase".
- **Bookkeeping note** at Refactor close (plan checkbox + state mutation are not "adding functionality").
- **Atomic 3-step close** (non-negotiable): (1) `/verification-before-completion` with evidence, (2) atomic commit with the phase prefix, (3) update `session-state.json`. Include the Refactor-close fork: task close (`chore: mark task {id} complete`) + the two cases (next `[ ]` → advance & reset to red; none → close plan).
- **TDD-Guard under multi-agent** scenario table (serial/parallel × same/different worktree × ON/OFF) + 3 practical rules.
- **On unexpected failure** → invoke `/systematic-debugging`.
- Point to `CLAUDE.local.md` §0.1 (verification commands), §5 (prefixes), §2.2 (schema) — do not duplicate.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_references.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/sbtdd/references/tdd-cycle.md
git commit -m "feat: add tdd-cycle reference"
```

---

## Task 9: Reference — review-gates.md

Source: template §6 (granularity, dual loop, MAGI verdict table, correction loop, safety valve) + §1 Checkpoint 2 (Plan gate uses same verdict table). Maps design §6 review-gates.md.

**Files:**
- Create: `skills/sbtdd/references/review-gates.md`
- Modify: `tests/test_references.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_references.py`:

```python
def test_review_gates_present_with_dual_loop_and_verdicts():
    t = (REF / "review-gates.md").read_text(encoding="utf-8")
    assert "requesting-code-review" in t
    assert "receiving-code-review" in t
    assert "magi" in t.lower()
    assert "clean to go" in t.lower()
    assert "GO WITH CAVEATS" in t
    for verdict in ("STRONG GO", "HOLD", "STRONG NO-GO"):
        assert verdict in t
    # safety valve: 3 iterations -> escalate
    assert "3 iterations" in t.lower() or "three iterations" in t.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_references.py::test_review_gates_present_with_dual_loop_and_verdicts -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_references.py
git commit -m "test: add review-gates reference checks"
```

- [ ] **Step 4: Create review-gates.md**

Create `skills/sbtdd/references/review-gates.md` (English). Required content:
- **Granularity**: per-TDD-phase close vs pre-merge once; MAGI runs once on the full diff.
- **Sequential independent dual loop**: Loop 1 `/requesting-code-review` → clean-to-go (no CRITICAL/WARNING); Loop 2 `/magi:magi` → ≥ GO WITH CAVEATS. Why they don't merge (contaminated verdicts).
- **Step 1 detail** (`/requesting-code-review` flow incl. `/receiving-code-review`, fixes as TDD mini-cycles `test:`→`fix:`→`refactor:`, repeat until clean).
- **Step 2 detail** (`/magi:magi` final gate).
- **MAGI verdict table** (STRONG GO, GO, GO WITH CAVEATS [+ when low-risk vs structural re-eval], HOLD -- TIE, HOLD, STRONG NO-GO) with actions.
- **Correction loop** + 3-iteration safety valve → escalate (causes list).
- Note this reference also serves the **Plan gate** (Checkpoint 2).
- Reference commit prefixes by `CLAUDE.local.md` §5.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_references.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/sbtdd/references/review-gates.md
git commit -m "feat: add review-gates reference"
```

---

## Task 10: Reference — finalization.md

Source: template §7 (clean git status, final checklist, pending resolution). Maps design §6 finalization.md.

**Files:**
- Create: `skills/sbtdd/references/finalization.md`
- Modify: `tests/test_references.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_references.py`:

```python
def test_finalization_present_with_checklist():
    t = (REF / "finalization.md").read_text(encoding="utf-8")
    assert "finishing-a-development-branch" in t
    assert "git status" in t
    assert "current_phase" in t and "done" in t
    # final checklist markers
    assert "- [ ]" in t
    assert "MAGI" in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_references.py::test_finalization_present_with_checklist -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_references.py
git commit -m "test: add finalization reference checks"
```

- [ ] **Step 4: Create finalization.md**

Create `skills/sbtdd/references/finalization.md` (English). Required content:
- **Clean git-status verification** against plan scope + approval criteria (no modified/staged/untracked of plan scope; permitted untracked only those documented).
- **Final checklist** (all template §7 preconditions as `- [ ]` items: all tasks `[x]`; state `current_task_id: null` + `current_phase: "done"`; §0.1 clean; git status clean; spec/plan reflect final state; Loop 1 clean-to-go; MAGI ≥ GO WITH CAVEATS; commits follow §5; CLAUDE.md updated if needed).
- **Pending-change resolution** (assign to a task; scope creep → revert or separate plan).
- Then invoke `/finishing-a-development-branch`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_references.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/sbtdd/references/finalization.md
git commit -m "feat: add finalization reference"
```

---

## Task 11: Orchestrator skill (`SKILL.md`)

Source: design §5 (entry mechanism, frontmatter, 5-step skeleton, delegation table) + template §1 flow.

**Files:**
- Create: `skills/sbtdd/SKILL.md`
- Create: `tests/test_skill.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_skill.py`:

```python
from conftest import ROOT, frontmatter

SKILL = ROOT / "skills/sbtdd/SKILL.md"

# the only skills the orchestrator is allowed to delegate to
ALLOWED_DELEGATES = {
    "brainstorming", "writing-plans", "magi", "test-driven-development",
    "verification-before-completion", "systematic-debugging",
    "subagent-driven-development", "executing-plans", "using-git-worktrees",
    "dispatching-parallel-agents", "requesting-code-review", "receiving-code-review",
    "finishing-a-development-branch",
}


def _txt():
    return SKILL.read_text(encoding="utf-8")


def test_frontmatter_has_name_and_description():
    fm = frontmatter(_txt())
    assert "name: sbtdd" in fm
    assert "description:" in fm
    assert "SBTDD" in fm


def test_skill_describes_five_step_flow():
    t = _txt().lower()
    for step in ("preflight", "route", "execute", "gate", "loop"):
        assert step in t


def test_delegation_table_only_references_known_skills():
    t = _txt()
    for skill in ("brainstorming", "writing-plans", "magi",
                  "test-driven-development", "requesting-code-review",
                  "finishing-a-development-branch"):
        assert skill in t


def test_skill_links_all_four_references():
    t = _txt()
    for ref in ("routing.md", "tdd-cycle.md", "review-gates.md", "finalization.md"):
        assert ref in t


def test_preflight_routes_to_init_when_uninitialized():
    t = _txt()
    assert "sbtdd-init" in t
    assert "CLAUDE.local.md" in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_skill.py -v`
Expected: FAIL — `SKILL.md` missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_skill.py
git commit -m "test: add orchestrator skill checks"
```

- [ ] **Step 4: Create SKILL.md**

Create `skills/sbtdd/SKILL.md`. Frontmatter (verbatim):

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

Body — the 5-step skeleton (keep it short; detail lives in references):
1. **Preflight** — verify `CLAUDE.local.md`, `sbtdd/`, `planning/` exist; if not, stop and tell the user to run `/sbtdd-init` (deep validation: `/sbtdd-check`).
2. **Route** — read `references/routing.md`; detect phase from the artifacts actually present (use Glob/LS/Read — file existence is the deterministic ground truth); on drift, abort & escalate; **announce the detected phase and the evidence found**, and confirm before acting when ambiguous.
3. **Execute** — per detected phase, read the matching reference and invoke the delegated skill(s). Skill names are **fully qualified** (`superpowers:…`, `magi:magi`) so delegation survives plugin namespacing. Include the delegation table verbatim:

   | Detected phase | Reference to read | superpowers skill(s) |
   |---|---|---|
   | Spec refinement | routing.md | `superpowers:brainstorming` |
   | Planning | routing.md | `superpowers:writing-plans` |
   | Plan gate | review-gates.md | `magi:magi` (+ manual review) |
   | Execution | tdd-cycle.md | `superpowers:test-driven-development`, `superpowers:verification-before-completion`, `superpowers:systematic-debugging`; mode `superpowers:subagent-driven-development` or `superpowers:executing-plans`; optional `superpowers:using-git-worktrees`, `superpowers:dispatching-parallel-agents` |
   | Pre-merge review | review-gates.md | `superpowers:requesting-code-review` → `superpowers:receiving-code-review` → `magi:magi` |
   | Finalization | finalization.md | `superpowers:finishing-a-development-branch` |

4. **Gates** — human stops (plan approval, MAGI verdict); never auto-approve.
5. **Loop** — re-route after a phase closes; under approved plan, continue autonomously per `CLAUDE.local.md` §5.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_skill.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/sbtdd/SKILL.md
git commit -m "feat: add sbtdd orchestrator skill"
```

---

## Task 12: Entry command (`/sbtdd`)

**Files:**
- Create: `commands/sbtdd.md`
- Create: `tests/test_commands.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_commands.py`:

```python
from conftest import ROOT, frontmatter

CMD = ROOT / "commands"


def test_sbtdd_command_invokes_skill():
    t = (CMD / "sbtdd.md").read_text(encoding="utf-8")
    assert "description:" in frontmatter(t)
    assert "sbtdd" in t.lower() and "skill" in t.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_commands.py -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_commands.py
git commit -m "test: add /sbtdd command checks"
```

- [ ] **Step 4: Create the command**

Create `commands/sbtdd.md`:

```markdown
---
description: Drive or resume the SBTDD workflow — routes by project state to the next phase
---

Use the `sbtdd` skill (via the Skill tool) to inspect the current project state
(`sbtdd/`, `planning/`, `.claude/session-state.json`) and execute the next SBTDD
phase. Do not duplicate the skill's logic here — invoke it.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_commands.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add commands/sbtdd.md
git commit -m "feat: add /sbtdd entry command"
```

---

## Task 13: Scaffolding command (`/sbtdd-init`)

Source: design §7 (init steps) + the templates from Tasks 3–6.

**Files:**
- Create: `commands/sbtdd-init.md`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_commands.py`:

```python
def test_sbtdd_init_covers_all_scaffolding_steps():
    t = (CMD / "sbtdd-init.md").read_text(encoding="utf-8")
    # stack detection
    for sig in ("Cargo.toml", "pyproject.toml", "CMakeLists.txt"):
        assert sig in t
    # writes the five gitignore entries (design §9)
    for entry in ("CLAUDE.local.md", "CLAUDE.md", ".claude/", "sbtdd/", "planning/"):
        assert entry in t
    # references the templates it installs
    for tmpl in ("CLAUDE.local.md.tmpl", "settings.json.tmpl",
                 "spec-behavior-base.tmpl.md", "verification/"):
        assert tmpl in t
    # idempotency + merge behavior
    assert "idempotent" in t.lower() or "do not overwrite" in t.lower()
    assert "merge" in t.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_commands.py::test_sbtdd_init_covers_all_scaffolding_steps -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_commands.py
git commit -m "test: add /sbtdd-init command checks"
```

- [ ] **Step 4: Create the command**

Create `commands/sbtdd-init.md` with frontmatter `description:` and a numbered procedure (design §7):
1. Detect stack (`Cargo.toml`→rust, `pyproject.toml`/`setup.py`→python, `CMakeLists.txt`→cpp); if ambiguous/none, ask via AskUserQuestion.
2. Write `CLAUDE.local.md` from `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.local.md.tmpl`, replacing `{StackVerification}` with `templates/verification/<stack>.md`, filling the §4 stack line, and resolving `{ErrorType}`/`{Author}` (ask or leave TODO).
3. Write/merge `.claude/settings.json` from `templates/settings.json.tmpl`. If the file exists: **back it up to `settings.json.bak` first**, parse it, append only hooks not already present, **never modify keys other than `hooks`**, and **show the diff + backup path before writing** (LLM-performed per the no-scripts decision — backup + show-diff is the safety net).
4. Create dirs `sbtdd/` and `planning/`.
5. Seed `sbtdd/spec-behavior-base.md` from `templates/spec-behavior-base.tmpl.md` if absent.
6. Append to `.gitignore`: `CLAUDE.local.md`, `CLAUDE.md`, `.claude/`, `sbtdd/`, `planning/`.
7. Report created/skipped (idempotent — do not overwrite existing files); remind to install `tdd-guard` + the stack reporter, then run `/sbtdd-check`.

Use `${CLAUDE_PLUGIN_ROOT}` for all template paths so it resolves inside the installed plugin.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_commands.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add commands/sbtdd-init.md
git commit -m "feat: add /sbtdd-init scaffolding command"
```

---

## Task 14: Verifier command (`/sbtdd-check`)

Source: design §7 (6-item checklist).

**Files:**
- Create: `commands/sbtdd-check.md`
- Modify: `tests/test_commands.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_commands.py`:

```python
def test_sbtdd_check_covers_six_items():  # now 7 items; name kept for stability
    t = (CMD / "sbtdd-check.md").read_text(encoding="utf-8")
    assert "CLAUDE.local.md" in t
    assert "PreToolUse" in t and "SessionStart" in t and "UserPromptSubmit" in t
    assert "sbtdd/" in t and "planning/" in t
    assert ".gitignore" in t
    assert "tdd-guard" in t
    assert "drift" in t.lower()
    # item 7: delegated-skill availability preflight (qualified names)
    assert "magi:magi" in t
    assert "superpowers" in t.lower()
    # PowerShell-first, no hard jq/which dependency
    assert "Get-Command" in t
    # read-only, routes to init
    assert "read-only" in t.lower() or "does not fix" in t.lower()
    assert "sbtdd-init" in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_commands.py::test_sbtdd_check_covers_six_items -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_commands.py
git commit -m "test: add /sbtdd-check command checks"
```

- [ ] **Step 4: Create the command**

Create `commands/sbtdd-check.md` with frontmatter `description:` and a read-only checklist that reports pass/fail + remediation per item, routing to `/sbtdd-init` for anything missing. Checks are **PowerShell-first** (`Get-Command`, `ConvertFrom-Json`) with POSIX fallbacks documented — no hard dependency on `jq`/`which`:
1. `CLAUDE.local.md` present with rule sections.
2. 3 TDD-Guard hooks active (`ConvertFrom-Json` on `.claude/settings.json`; fallback `jq '.hooks'`).
3. `sbtdd/` and `planning/` exist.
4. `.gitignore` contains the 5 local-only entries.
5. `tdd-guard` binary + stack reporter on PATH (`Get-Command`; fallback `which`).
6. State-file consistency (if present): light drift check vs git/plan (defer to `routing.md` rule).
7. **Delegated skills/plugins available** — verify `superpowers:*` skills and `magi:magi` are installed; **fail loud** listing any missing (the orchestrator depends on them at runtime).

State explicitly: this command is read-only — it diagnoses, it does not fix.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_commands.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add commands/sbtdd-check.md
git commit -m "feat: add /sbtdd-check verifier command"
```

---

## Task 15: README

**Files:**
- Create: `README.md`
- Create: `tests/test_readme.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_readme.py`:

```python
from conftest import ROOT


def test_readme_documents_entrypoints():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    for cmd in ("/sbtdd", "/sbtdd-init", "/sbtdd-check"):
        assert cmd in t
    assert "SBTDD" in t
    # documents the install-then-init-then-run flow
    assert "install" in t.lower()
    # documents runtime dependencies + the gitignore trade-off (MAGI caveats)
    assert "superpowers" in t.lower() and "magi" in t.lower()
    assert "gitignore" in t.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_readme.py -v`
Expected: FAIL — file missing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_readme.py
git commit -m "test: add README checks"
```

- [ ] **Step 4: Create README.md**

Create `README.md` (English): what the plugin is, the three commands, the install → `/sbtdd-init` → `/sbtdd-check` → `/sbtdd` flow, the multi-stack note, the tracking policy (everything SBTDD is gitignored), and the dependency on superpowers + `tdd-guard` + (for MAGI gate) the magi skill.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_readme.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: add plugin README"
```

---

## Task 16: Integration — cross-reference integrity + behavioral checklist

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_integration.py`:

```python
import json
from conftest import ROOT
from test_skill import ALLOWED_DELEGATES


def test_every_reference_linked_from_skill_exists():
    skill = (ROOT / "skills/sbtdd/SKILL.md").read_text(encoding="utf-8")
    for ref in ("routing.md", "tdd-cycle.md", "review-gates.md", "finalization.md"):
        assert ref in skill
        assert (ROOT / "skills/sbtdd/references" / ref).is_file()


def test_skill_delegates_only_to_known_skills():
    skill = (ROOT / "skills/sbtdd/SKILL.md").read_text(encoding="utf-8")
    # capture the skill name inside backticks, dropping any plugin: prefix
    # (e.g. `superpowers:brainstorming` -> brainstorming, `magi:magi` -> magi)
    import re
    cited = set(re.findall(r"`(?:[a-z-]+:)?([a-z][a-z-]+)`", skill))
    suspicious = {c for c in cited if c.endswith("-development") or c in
                  {"brainstorming", "writing-plans", "magi", "executing-plans"}}
    assert suspicious <= ALLOWED_DELEGATES


def test_init_templates_all_exist():
    init = (ROOT / "commands/sbtdd-init.md").read_text(encoding="utf-8")
    for tmpl in ("CLAUDE.local.md.tmpl", "settings.json.tmpl",
                 "spec-behavior-base.tmpl.md"):
        assert (ROOT / "templates" / tmpl).is_file()
    for stack in ("rust", "python", "cpp"):
        assert (ROOT / "templates/verification" / f"{stack}.md").is_file()


def test_manifest_parses():
    json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))


def test_referenced_rule_sections_exist_in_template():
    # drift guard: references point to CLAUDE.local.md rule sections by name;
    # those names must actually exist in the scaffolded template
    tmpl = (ROOT / "templates/CLAUDE.local.md.tmpl").read_text(encoding="utf-8")
    for section in ("Mandatory Code Standards", "session-state.json", "Commit"):
        assert section in tmpl
```

- [ ] **Step 2: Run test to verify it fails (then passes — all deps now exist)**

Run: `python -m pytest tests/test_integration.py -v`
Expected: PASS if Tasks 2–15 are complete. If any FAIL, fix the offending artifact before committing (this task is the integrity gate).

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -v`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add cross-reference integrity checks"
```

- [ ] **Step 5: Manual behavioral validation (cannot be unit-tested — run Claude)**

These require a live Claude session and a throwaway target repo. Record results in the PR/notes:

1. **Plugin validity** — run `plugin-dev:plugin-validator` against the repo; expect no errors.
2. **Scaffolding dry-run per stack** — in three throwaway repos containing `Cargo.toml`, `pyproject.toml`, and `CMakeLists.txt` respectively: run `/sbtdd-init`; confirm `CLAUDE.local.md` got the correct §0.1 block, `.claude/settings.json` has the 3 hooks, dirs + `.gitignore` entries created. Then run `/sbtdd-check` → all 6 items pass.
3. **Idempotency** — run `/sbtdd-init` again in one repo; confirm no files clobbered and hooks not duplicated.
4. **Routing coverage** — create artifacts by hand to simulate each state; run `/sbtdd`; confirm it announces the correct phase. Include a drift case (state `green`, last commit `refactor:`) and confirm it aborts & escalates.
5. **Triggering** — confirm the `sbtdd` skill surfaces for prompts like "continue the SBTDD plan".

- [ ] **Step 6: Commit any fixes from manual validation**

Use the appropriate prefix (`fix:` / `docs:`) per `~/.claude/CLAUDE.md` §Git.

---

## Self-Review (completed during planning)

**1. Spec coverage** — every design section maps to a task: D1/manifest→T2; D2 setup+verifier→T13/T14; D3 skill+refs→T7-11; D4 English→all content tasks; D5 multi-stack→T3/T13; D6 routing→T7/T11; D7 tracking override→T5/T13; design §11 mapping table→T3-T15; design §10 testing→T1-T16; design §12 isolation→file structure.

**2. Placeholder scan** — no "TBD/implement later". Content tasks cite exact template § + enumerated required elements enforced by tests; canonical source files are named in the header.

**3. Type/name consistency** — `ALLOWED_DELEGATES` defined in `test_skill.py` and imported by `test_integration.py`; reference filenames (`routing.md`, `tdd-cycle.md`, `review-gates.md`, `finalization.md`) identical across SKILL, tests, and file structure; gitignore 5-entry set identical in T5/T13/T14; `{StackVerification}`/`{ErrorType}`/`{Author}` placeholders consistent between T5 and T13.

---

## MAGI review revisions (2026-05-23)

MAGI verdict on design+plan: **GO WITH CAVEATS (3-0)**. Findings processed via
`superpowers:receiving-code-review`. User decisions on the structural caveats:
**keep D7** (gitignored, no export), **keep `settings.json`** target, **no helper
scripts** (file ops stay LLM-performed). Plan deltas applied this revision:

- **T13 (`/sbtdd-init`)** — settings merge is now defensive: back up to
  `settings.json.bak`, append only missing hooks, never touch non-`hooks` keys,
  show diff + backup path before writing.
- **T14 (`/sbtdd-check`)** — PowerShell-first (`Get-Command`, `ConvertFrom-Json`,
  no hard `jq`/`which`); added **item 7**: delegated-skill availability preflight
  (`superpowers:*` + `magi:magi`), fail loud on missing. Test asserts these.
- **T11 (`SKILL.md`)** — delegated skill names fully qualified (`superpowers:…`,
  `magi:magi`); routing announces the **evidence found** and confirms on ambiguity.
- **T16 (integration)** — delegation regex handles qualified names; added a
  **drift guard** test (referenced rule-section names exist in the template).
- **T15 (README)** — must document the runtime dependency (superpowers + magi) and
  the gitignore trade-off; test enforces their presence.
- **Conventions** — pytest reframed as presence/lint; Task 16 Step 5 (plugin-validator
  + manual behavioral evals) is the **required** acceptance gate, not optional.

**Consciously-accepted residual risks** (from the no-scripts + keep-settings
decisions): the **merge-clobber** critical is *mitigated, not closed* (safety net =
backup + show-diff + manual validation, no tested deterministic script); the
behavior-test gap remains (pytest stays substring-based — the manual gate carries the
real assurance). See design §13.
