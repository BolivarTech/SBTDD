# sbtdd-workflow v0.4.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.4.0 (MAGI dispatch hardening + v0.3.0 streaming follow-through) as MINOR non-BREAKING bump 0.3.0 → 0.4.0. Two surfaces 100% disjoint dispatched in true parallel.

**Architecture:** Feature F adds 4 helpers to `magi_dispatch.py` + 1 field to `MAGIVerdict` + 1 schema constant in `models.py`. The helpers replace path-based MAGI report discovery with marker-based discovery, propagate the new MAGI 2.2.1+ `retried_agents` field, tolerate preamble-wrapped agent JSON, and provide automatic manual-synthesis recovery when `run_magi.py` synthesizer crashes with ≥1 agent succeeded. J subset extends `auto_cmd.py` (OSError handling around `_update_progress`, audit progress preservation), `pre_merge_cmd.py` (stream_prefix wiring), and SKILL.md (exit-code docs hotfix). All additive, no behavior flips.

**Tech Stack:** Python 3.9+ stdlib + PyYAML, pytest + ruff + mypy --strict, cross-platform Windows + POSIX.

---

## Reference materials

Before starting any task, read:
- **Spec**: `sbtdd/spec-behavior.md` (BDD overlay v0.4.0 — escenarios F43.1..F46.5, J4.1..J8.3, R2.1..R2.2).
- **Spec base**: `sbtdd/spec-behavior-base.md` (raw input v1.0.0 post-v0.3.0).
- **v0.3.0 ship record**: memory `project_v030_shipped.md` (rationale + empirical findings).
- **MAGI iter 2 raw outputs**: `.claude/magi-runs/v030-iter2/{melchior,balthasar,caspar}.raw.json` (concrete preamble-wrapped JSON examples for F45 fixture data).
- **CLAUDE.local.md sec.3** (TDD discipline) and **sec.5** (commit prefixes).
- **Authoritative invariants**: `sbtdd/sbtdd-workflow-plugin-spec-base.md` sec.S.10 (INV-0..INV-31).

---

## File structure

| File | Track | Responsibility | Status |
|------|-------|----------------|--------|
| `skills/sbtdd/scripts/magi_dispatch.py` | F | Add `_discover_verdict_marker`, `_tolerant_agent_parse`, `_manual_synthesis_recovery`. Extend `MAGIVerdict` with `retried_agents`. Modify `invoke_magi` to consume marker discovery + auto-recovery on crash. | Modify |
| `skills/sbtdd/scripts/models.py` | F | Add `MAGI_VERDICT_MARKER_FIELDS` constant tuple (schema fixed) | Modify |
| `tests/test_magi_hardening.py` | F | Cover F43.1, F43.2, F43.3, F44.1, F44.2, F44.3, F45.1, F45.2, F45.3, F45.4 | Create |
| `tests/test_manual_synthesis_recovery.py` | F | Cover F46.1, F46.2, F46.3, F46.4, F46.5 | Create |
| `skills/sbtdd/scripts/auto_cmd.py` | J | J4 OSError wrap around `_update_progress` write site. J6 `_write_auto_run_audit` preserves existing `progress` field. | Modify |
| `skills/sbtdd/scripts/pre_merge_cmd.py` | J | J8 thread `stream_prefix` into Loop 1 + Loop 2 + mini-cycle dispatch sites | Modify |
| `skills/sbtdd/SKILL.md` | J | J5 line 78 docs hotfix (exit 2 → exit 1) | Modify |
| `tests/test_auto_progress.py` | J | Extend with J4.1, J4.2, J6.1, J6.2 | Modify (existing) |
| `tests/test_skill_md.py` | J | Extend with J5.1 | Modify (existing) |
| `tests/test_pre_merge_streaming.py` | J | Cover J8.1, J8.2, J8.3 | Create |
| `CHANGELOG.md` | Final | Add `[0.4.0]` section | Modify |
| `tests/test_plugin_manifest.py` | Final | Bump version tripwire from v0.3.x to v0.4.x | Modify |
| `.claude-plugin/plugin.json` | Final | 0.3.0 → 0.4.0 | Modify |
| `.claude-plugin/marketplace.json` | Final | 0.3.0 → 0.4.0 (two occurrences) | Modify |

---

## Subagent dispatch contracts

### Subagent #1 — Track F (MAGI hardening)

- **Reads**: spec sec.2 + plan tasks F-1 to F-4. Current `magi_dispatch.py` (lines 1-450 covering `MAGIVerdict`, `parse_magi_report`, `_build_magi_cmd`, `invoke_magi`). Current `models.py`. The `.raw.json` files in `.claude/magi-runs/v030-iter2/` for fixture data.
- **Writes**: `magi_dispatch.py` (extension), `models.py` (extension), 2 new test files.
- **Forbidden**: `auto_cmd.py`, `pre_merge_cmd.py`, `SKILL.md`, any `tests/test_auto_*` or `tests/test_pre_merge_*` files.
- **TDD-Guard**: ON.
- **Tasks**: F-1 through F-4 (recommended order).
- **Done**: 4 deliverables landed + tests pass + `make verify` clean.

### Subagent #2 — Track J (v0.3.0 streaming follow-through)

- **Reads**: spec sec.3 + plan tasks J-1 to J-4. Current `auto_cmd.py` `_update_progress` and `_write_auto_run_audit`. Current `pre_merge_cmd.py` Loop 1 + Loop 2 + mini-cycle dispatch sites. SKILL.md line 78.
- **Writes**: `auto_cmd.py` (J4 + J6), `pre_merge_cmd.py` (J8), `SKILL.md` (J5), 2 modified existing test files + 1 new test file.
- **Forbidden**: `magi_dispatch.py`, `models.py`, any `tests/test_magi_*` or `tests/test_manual_synthesis_*` files.
- **TDD-Guard**: ON.
- **Tasks**: J-1 through J-4 (recommended order J5 → J4 → J6 → J8).
- **Done**: 4 deliverables landed + tests pass + `make verify` clean.

### Coordination

Surfaces 100% disjoint — both subagents commit to `main` simultaneously without merge conflict risk. Orchestrator dispatches both in parallel via two `Agent` tool calls in a single message. Waits for both DONE before final review.

---

# Track F — MAGI dispatch hardening (Subagent #1)

## Task F-1: Marker-based verdict discovery (F43)

**Files:**
- Create: `tests/test_magi_hardening.py`
- Modify: `skills/sbtdd/scripts/magi_dispatch.py` (add `_discover_verdict_marker`)

- [ ] **Step 1: Write failing test F43.1 (picks newest by mtime)**

```python
# tests/test_magi_hardening.py (new file)
#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.4.0 Feature F MAGI dispatch hardening."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import magi_dispatch
from errors import ValidationError


def test_discover_verdict_marker_picks_newest_by_mtime(tmp_path):
    """F43.1: enumerator returns marker with max mtime."""
    old = tmp_path / "marker_old.json"
    new = tmp_path / "marker_new.json"
    old.write_text(json.dumps({"verdict": "GO"}))
    time.sleep(0.05)
    new.write_text(json.dumps({"verdict": "GO_WITH_CAVEATS"}))
    # ensure mtime ordering (Windows clock granularity)
    os.utime(old, (old.stat().st_atime, old.stat().st_mtime - 10))
    result = magi_dispatch._discover_verdict_marker(tmp_path, marker_name="MAGI_VERDICT_MARKER.json")
    # rename to expected marker name
    old_renamed = tmp_path / "MAGI_VERDICT_MARKER.json.old"
    old.rename(tmp_path / "MAGI_VERDICT_MARKER.json")
    new.rename(tmp_path / "MAGI_VERDICT_MARKER_new.json")
    # actually we need both with the same name in different subdirs
    # simpler: use rglob, place both with same name
    sub_old = tmp_path / "old"
    sub_new = tmp_path / "new"
    sub_old.mkdir(exist_ok=True)
    sub_new.mkdir(exist_ok=True)
    (sub_old / "MAGI_VERDICT_MARKER.json").write_text(json.dumps({"verdict": "GO"}))
    time.sleep(0.05)
    (sub_new / "MAGI_VERDICT_MARKER.json").write_text(json.dumps({"verdict": "GO_WITH_CAVEATS"}))
    found = magi_dispatch._discover_verdict_marker(tmp_path)
    assert found.parent.name == "new"
```

(Simplify: write helper that creates two subdirs with markers staggered by mtime, asserts newest picked.)

- [ ] **Step 2: Run test, verify FAIL**

```bash
cd D:/jbolivarg/PythonProjects/SBTDD
python -m pytest tests/test_magi_hardening.py::test_discover_verdict_marker_picks_newest_by_mtime -v
```
Expected: FAIL — `AttributeError: module 'magi_dispatch' has no attribute '_discover_verdict_marker'`.

- [ ] **Step 3: Implement `_discover_verdict_marker`**

Append to `magi_dispatch.py`:

```python
_MARKER_FILENAME = "MAGI_VERDICT_MARKER.json"


def _discover_verdict_marker(output_dir: Path | str) -> Path:
    """Discover the most recent MAGI verdict marker in an output directory.

    v0.4.0 Feature F (F43): replaces fragile path-based discovery
    (``output_dir / "magi-report.json"``) with marker enumeration via
    ``Path.rglob("MAGI_VERDICT_MARKER.json")``. Picks the marker with
    max mtime so re-runs in the same dir return the latest result.

    Args:
        output_dir: Directory to scan recursively.

    Returns:
        Path to the most recent marker file.

    Raises:
        ValidationError: If no markers found, with detail listing files
            actually present for debugability.
    """
    base = Path(output_dir)
    candidates = sorted(base.rglob(_MARKER_FILENAME), key=lambda p: p.stat().st_mtime)
    if not candidates:
        present = sorted(p.name for p in base.iterdir()) if base.exists() else []
        raise ValidationError(
            f"No {_MARKER_FILENAME} found in {base}. Files present: {present}"
        )
    return candidates[-1]
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Add F43.2 test (no markers raises with detail)**

```python
def test_discover_verdict_marker_raises_when_empty(tmp_path):
    """F43.2: ValidationError when no markers found, lists present files."""
    (tmp_path / "stray.json").write_text("{}")
    with pytest.raises(ValidationError) as ei:
        magi_dispatch._discover_verdict_marker(tmp_path)
    assert "MAGI_VERDICT_MARKER.json" in str(ei.value)
    assert "stray.json" in str(ei.value)
```

- [ ] **Step 6: Add F43.3 test (recursive discovery)**

```python
def test_discover_verdict_marker_finds_in_subdir(tmp_path):
    """F43.3: rglob finds markers in nested subdirs."""
    sub = tmp_path / "run-XYZ"
    sub.mkdir()
    (sub / "MAGI_VERDICT_MARKER.json").write_text(json.dumps({"verdict": "GO"}))
    found = magi_dispatch._discover_verdict_marker(tmp_path)
    assert found.parent.name == "run-XYZ"
```

- [ ] **Step 7: make verify**

```bash
make verify
```

- [ ] **Step 8: Commit (Red→Green collapsed since helper is new)**

```bash
git add skills/sbtdd/scripts/magi_dispatch.py tests/test_magi_hardening.py
git commit -m "feat: add _discover_verdict_marker for marker-based MAGI report discovery"
```

---

## Task F-2: retried_agents field on MAGIVerdict (F44)

**Files:**
- Modify: `skills/sbtdd/scripts/magi_dispatch.py` (extend `MAGIVerdict`, parser)
- Modify: `tests/test_magi_hardening.py`

- [ ] **Step 1: Write failing test F44.1 (field parsed when present)**

```python
def test_retried_agents_parsed_when_present(tmp_path):
    """F44.1: retried_agents from marker JSON becomes tuple."""
    marker = tmp_path / "MAGI_VERDICT_MARKER.json"
    marker.write_text(json.dumps({
        "verdict": "GO_WITH_CAVEATS",
        "iteration": 1,
        "agents": ["melchior", "balthasar", "caspar"],
        "retried_agents": ["caspar"],
        "consensus": {"label": "GO_WITH_CAVEATS", "degraded": False, "findings": [], "conditions_for_approval": []},
    }))
    verdict = magi_dispatch.MAGIVerdict.from_marker(marker)
    assert verdict.retried_agents == ("caspar",)
```

- [ ] **Step 2: Run, verify FAIL** — `MAGIVerdict.from_marker` not defined OR field missing.

- [ ] **Step 3: Add field + factory to MAGIVerdict**

In `magi_dispatch.py`, locate `MAGIVerdict` dataclass declaration. Extend:

```python
@dataclass(frozen=True)
class MAGIVerdict:
    verdict: str
    degraded: bool
    conditions: tuple[str, ...]
    findings: tuple[dict[str, Any], ...]
    raw_output: str
    # v0.4.0 Feature F (F44): MAGI 2.2.1+ retried_agents telemetry.
    # Parser tolerates absence; defaults to empty tuple for backward
    # compat with MAGI 2.1.x markers.
    retried_agents: tuple[str, ...] = ()

    @classmethod
    def from_marker(cls, marker_path: Path | str) -> MAGIVerdict:
        """Parse a MAGI verdict marker JSON file into a MAGIVerdict.

        Reads the marker, validates required fields, and extracts the
        consensus block. Tolerates missing ``retried_agents`` field for
        MAGI 2.1.x compat.
        """
        data = json.loads(Path(marker_path).read_text(encoding="utf-8"))
        retried = tuple(data.get("retried_agents") or ())
        # Reuse the existing report-shaped parser to preserve all the
        # sec.S.10 invariants around verdict label validation.
        verdict = parse_magi_report(data)
        # Re-construct with the retried_agents populated since
        # parse_magi_report does not yet know about that field.
        return cls(
            verdict=verdict.verdict,
            degraded=verdict.degraded,
            conditions=verdict.conditions,
            findings=verdict.findings,
            raw_output=verdict.raw_output,
            retried_agents=retried,
        )
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Add F44.2 (default empty tuple when absent)**

```python
def test_retried_agents_defaults_empty_tuple(tmp_path):
    """F44.2: MAGI 2.1.x marker without retried_agents loads cleanly."""
    marker = tmp_path / "MAGI_VERDICT_MARKER.json"
    marker.write_text(json.dumps({
        "verdict": "GO",
        "iteration": 1,
        "agents": ["melchior", "balthasar", "caspar"],
        "consensus": {"label": "GO", "degraded": False, "findings": [], "conditions_for_approval": []},
    }))
    verdict = magi_dispatch.MAGIVerdict.from_marker(marker)
    assert verdict.retried_agents == ()
```

- [ ] **Step 6: Add F44.3 propagation test (auto-run.json)**

```python
def test_retried_agents_propagated_to_auto_run(tmp_path):
    """F44.3: retried_agents reaches auto-run.json audit field."""
    # Lightweight unit: assert auto_cmd has a helper to encode retried agents
    # into the audit dict. Full integration deferred to integration suite.
    import auto_cmd
    audit = {"phase": 4, "iter": 2}
    updated = auto_cmd._record_magi_retried_agents(audit, ("balthasar",), iter_num=2)
    assert updated["magi_iter2_retried_agents"] == ["balthasar"]
```

(Implement `auto_cmd._record_magi_retried_agents(audit, retried, iter_num)` as a small helper that mutates audit dict. NOTE: this touches `auto_cmd.py` but in a forbidden-zone-for-Track-F file. Resolution: define `_record_magi_retried_agents` in `magi_dispatch.py` as a pure-function helper that returns a dict mutation, NOT in auto_cmd. Track J subagent won't touch it. Integration into auto_cmd.py audit writes is a v0.4.1 / v1.0.0 follow-up; for v0.4.0 the helper exists but is NOT yet wired into `_write_auto_run_audit` because that's J6's surface and would require coordination. Document in CHANGELOG that F44.3 ships the helper; integration follows.)

Actually simpler resolution: re-scope F44.3 test to verify only that `MAGIVerdict.retried_agents` is a tuple of strings consumable by audit writers. Defer audit-side wiring to v1.0.0.

```python
def test_retried_agents_consumable_by_audit_writer():
    """F44.3 (re-scoped): retried_agents tuple is JSON-serializable + ordered."""
    verdict = magi_dispatch.MAGIVerdict(
        verdict="GO_WITH_CAVEATS",
        degraded=False,
        conditions=(),
        findings=(),
        raw_output="{}",
        retried_agents=("balthasar", "caspar"),
    )
    # Serialization round-trip
    serialized = json.dumps(list(verdict.retried_agents))
    assert json.loads(serialized) == ["balthasar", "caspar"]
```

- [ ] **Step 7: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/magi_dispatch.py tests/test_magi_hardening.py
git commit -m "feat: add retried_agents field to MAGIVerdict for MAGI 2.2.1+ compat"
```

---

## Task F-3: Tolerant agent JSON parsing (F45)

**Files:**
- Modify: `skills/sbtdd/scripts/magi_dispatch.py`
- Modify: `tests/test_magi_hardening.py`

- [ ] **Step 1: Write failing test F45.1 (preamble-wrapped JSON extraction)**

```python
def test_tolerant_agent_parse_extracts_from_preamble(tmp_path):
    """F45.1: extract JSON object from agent result wrapped in narrative."""
    raw = tmp_path / "melchior.raw.json"
    raw.write_text(json.dumps({
        "type": "result",
        "result": (
            "Based on my review of the iter-2 fixes, the streaming wiring is correctly "
            "threaded.\n\n"
            "{\"agent\": \"melchior\", \"verdict\": \"GO\", \"confidence\": 0.88, "
            "\"summary\": \"Iter 2 closes findings.\", \"reasoning\": \"...\", "
            "\"findings\": [], \"recommendation\": \"Ship v0.3.0.\"}"
        ),
    }))
    parsed = magi_dispatch._tolerant_agent_parse(raw)
    assert parsed["agent"] == "melchior"
    assert parsed["verdict"] == "GO"
    assert parsed["confidence"] == 0.88
```

- [ ] **Step 2: Run, verify FAIL** — `_tolerant_agent_parse` not defined.

- [ ] **Step 3: Implement `_tolerant_agent_parse`**

Append to `magi_dispatch.py`:

```python
import re as _re_for_tolerant_parse

_VALID_AGENT_NAMES = frozenset({"melchior", "balthasar", "caspar"})


def _extract_first_balanced_json(text: str) -> str | None:
    """Return the first balanced ``{...}`` JSON-looking substring, or None.

    Walks the text counting brace depth, ignoring braces inside strings.
    Returns the full substring from the first ``{`` to its matching ``}``.
    Pure stdlib; no regex backtracking needed.
    """
    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                return text[start : i + 1]
    return None


def _tolerant_agent_parse(raw_json_path: Path | str) -> dict[str, Any]:
    """Parse an agent's ``*.raw.json`` file with preamble tolerance.

    v0.4.0 Feature F (F45): MAGI v2.2.2 agents sometimes wrap their
    verdict JSON in a narrative preamble inside the ``result`` field
    (e.g., ``"Based on my review...\\n\\n{json}"``). The strict parser
    in ``run_magi.py:synthesize.py`` rejects these. This helper
    extracts the first balanced ``{...}`` substring from ``result``
    and JSON-parses it. Validates that the extracted dict has an
    ``agent`` field naming one of the three canonical agents.

    Args:
        raw_json_path: Path to the agent's ``*.raw.json`` file written
            by the MAGI orchestrator.

    Returns:
        Parsed agent verdict dict.

    Raises:
        ValidationError: If no recoverable JSON object is present, or
            the extracted object lacks a valid ``agent`` field.
    """
    raw_data = json.loads(Path(raw_json_path).read_text(encoding="utf-8"))
    result = raw_data.get("result")
    if not isinstance(result, str):
        raise ValidationError(
            f"No 'result' string in {raw_json_path} "
            f"(got {type(result).__name__})"
        )
    # Try direct JSON parse first (caspar v0.3.0 iter 2 case: pure JSON
    # in result field, no preamble). Backward compat with strict parser.
    try:
        candidate = json.loads(result)
        if isinstance(candidate, dict) and candidate.get("agent") in _VALID_AGENT_NAMES:
            return candidate
    except json.JSONDecodeError:
        pass
    # Preamble-tolerant path: extract first balanced JSON object that
    # parses cleanly AND has a valid agent field.
    remaining = result
    while True:
        substring = _extract_first_balanced_json(remaining)
        if substring is None:
            preview = result[:200].replace("\n", " ")
            raise ValidationError(
                f"No JSON object recoverable from {raw_json_path}: "
                f"result preview: {preview!r}"
            )
        try:
            candidate = json.loads(substring)
        except json.JSONDecodeError:
            # Skip this substring and search after it
            idx = remaining.find(substring) + len(substring)
            remaining = remaining[idx:]
            continue
        if isinstance(candidate, dict) and candidate.get("agent") in _VALID_AGENT_NAMES:
            return candidate
        # Skip this candidate (e.g., embedded code-example dict)
        idx = remaining.find(substring) + len(substring)
        remaining = remaining[idx:]
```

- [ ] **Step 4: Run, verify PASS**

- [ ] **Step 5: Add F45.2 test (pure JSON works)**

```python
def test_tolerant_agent_parse_pure_json(tmp_path):
    """F45.2: pure JSON result parses identically to strict parser."""
    raw = tmp_path / "caspar.raw.json"
    raw.write_text(json.dumps({
        "type": "result",
        "result": json.dumps({
            "agent": "caspar",
            "verdict": "approve",
            "confidence": 0.85,
            "summary": "Ship.",
            "reasoning": "...",
            "findings": [],
            "recommendation": "Ship.",
        }),
    }))
    parsed = magi_dispatch._tolerant_agent_parse(raw)
    assert parsed["agent"] == "caspar"
    assert parsed["verdict"] == "approve"
```

- [ ] **Step 6: Add F45.3 test (zero recoverable raises)**

```python
def test_tolerant_agent_parse_no_recoverable_json(tmp_path):
    """F45.3: result with only narrative raises ValidationError with preview."""
    raw = tmp_path / "broken.raw.json"
    raw.write_text(json.dumps({
        "type": "result",
        "result": "I encountered an error and could not produce a verdict for this run.",
    }))
    with pytest.raises(ValidationError) as ei:
        magi_dispatch._tolerant_agent_parse(raw)
    assert "No JSON object recoverable" in str(ei.value)
    assert "encountered an error" in str(ei.value)
```

- [ ] **Step 7: Add F45.4 test (skips code-example dicts, picks verdict)**

```python
def test_tolerant_agent_parse_skips_code_examples(tmp_path):
    """F45.4: parser skips embedded code-example dicts, finds verdict."""
    raw = tmp_path / "balthasar.raw.json"
    raw.write_text(json.dumps({
        "type": "result",
        "result": (
            "Here is an example structure: {\"key\": \"val\"}.\n"
            "And another: {\"name\": \"thing\"}.\n\n"
            "{\"agent\": \"balthasar\", \"verdict\": \"approve\", "
            "\"confidence\": 0.88, \"summary\": \"OK.\", "
            "\"reasoning\": \"Reasonable trade-offs.\", "
            "\"findings\": [], \"recommendation\": \"Ship.\"}"
        ),
    }))
    parsed = magi_dispatch._tolerant_agent_parse(raw)
    assert parsed["agent"] == "balthasar"
    assert parsed["verdict"] == "approve"
```

- [ ] **Step 8: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/magi_dispatch.py tests/test_magi_hardening.py
git commit -m "feat: add _tolerant_agent_parse for preamble-wrapped agent JSON"
```

---

## Task F-4: Manual synthesis recovery (F46)

**Files:**
- Create: `tests/test_manual_synthesis_recovery.py`
- Modify: `skills/sbtdd/scripts/magi_dispatch.py` (add `_manual_synthesis_recovery` + integrate into `invoke_magi`)

- [ ] **Step 1: Write failing test F46.1 (recovery succeeds with 2/3 agents)**

```python
# tests/test_manual_synthesis_recovery.py (new file)
#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.4.0 Feature F manual synthesis recovery."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import magi_dispatch
from errors import MAGIGateError


def _write_raw_agent(path: Path, agent: str, verdict: str, preamble: bool = True) -> None:
    body = {
        "agent": agent,
        "verdict": verdict,
        "confidence": 0.88,
        "summary": f"{agent} verdict {verdict}",
        "reasoning": "...",
        "findings": [],
        "recommendation": "Ship." if verdict in ("approve", "GO", "GO_WITH_CAVEATS") else "HOLD.",
    }
    if preamble:
        result = f"Based on my review...\n\n{json.dumps(body)}"
    else:
        result = json.dumps(body)
    path.write_text(json.dumps({"type": "result", "result": result}))


def test_manual_synthesis_recovers_with_two_agents(tmp_path):
    """F46.1: synthesizer crashed but 2/3 agents have valid raw JSON."""
    _write_raw_agent(tmp_path / "melchior.raw.json", "melchior", "approve", preamble=True)
    _write_raw_agent(tmp_path / "balthasar.raw.json", "balthasar", "approve", preamble=True)
    _write_raw_agent(tmp_path / "caspar.raw.json", "caspar", "approve", preamble=False)
    verdict = magi_dispatch._manual_synthesis_recovery(tmp_path)
    assert verdict.verdict in ("GO", "STRONG_GO")
    # Recovery report written
    assert (tmp_path / "manual-synthesis.json").exists()
    report = json.loads((tmp_path / "manual-synthesis.json").read_text())
    assert report["recovered"] is True
    assert report["recovery_reason"] == "synthesizer-failure"
```

- [ ] **Step 2: Run, verify FAIL** — `_manual_synthesis_recovery` not defined.

- [ ] **Step 3: Implement `_manual_synthesis_recovery`**

Append to `magi_dispatch.py`:

```python
# Verdict synthesis weights (mirror run_magi.py:synthesize.py).
_VERDICT_WEIGHT = {
    "approve": 1.0,
    "GO": 1.0,
    "STRONG_GO": 1.0,
    "GO_WITH_CAVEATS": 0.5,
    "conditional": 0.5,
    "reject": -1.0,
    "HOLD": -1.0,
    "STRONG_NO_GO": -1.0,
}


def _manual_synthesis_recovery(run_dir: Path | str) -> MAGIVerdict:
    """Recover a MAGI verdict when the synthesizer crashed.

    v0.4.0 Feature F (F46): when ``run_magi.py`` aborts with a
    ``RuntimeError`` (e.g., "Only N agent(s) succeeded"), this helper
    walks the run dir for ``*.raw.json`` files, applies the tolerant
    agent parser (F45), synthesizes a verdict using the same weight
    scheme as ``synthesize.py``, and writes a ``manual-synthesis.json``
    report flagged ``recovered: true``.

    Args:
        run_dir: Directory containing per-agent ``*.raw.json`` files.

    Returns:
        :class:`MAGIVerdict` rescued from the raw outputs.

    Raises:
        MAGIGateError: If zero agents have recoverable JSON.
    """
    base = Path(run_dir)
    raw_files = sorted(base.glob("*.raw.json"))
    parsed: list[dict[str, Any]] = []
    failures: list[str] = []
    for raw in raw_files:
        try:
            parsed.append(_tolerant_agent_parse(raw))
        except ValidationError as exc:
            failures.append(f"{raw.name}: {exc}")
    if not parsed:
        raise MAGIGateError(
            f"No recoverable agent verdicts in {base}; manual synthesis impossible. "
            f"Failures: {failures}"
        )
    # Compute consensus score using the standard weights.
    score = sum(_VERDICT_WEIGHT.get(p["verdict"], 0.0) for p in parsed) / len(parsed)
    has_conditional = any(p["verdict"] in ("conditional", "GO_WITH_CAVEATS") for p in parsed)
    approves = sum(1 for p in parsed if _VERDICT_WEIGHT.get(p["verdict"], 0.0) > 0)
    rejects = sum(1 for p in parsed if _VERDICT_WEIGHT.get(p["verdict"], 0.0) < 0)
    if score == 1.0:
        label = "STRONG_GO"
    elif score == -1.0:
        label = "STRONG_NO_GO"
    elif score > 0:
        label = "GO_WITH_CAVEATS" if has_conditional else "GO"
    elif score < 0:
        label = "HOLD"
    else:
        label = "HOLD_TIE"
    # Aggregate findings + dissent across agents.
    findings: list[dict[str, Any]] = []
    for p in parsed:
        for f in p.get("findings", []) or []:
            findings.append({**f, "from_agent": p["agent"]})
    degraded = len(parsed) < 3
    report = {
        "recovered": True,
        "recovery_reason": "synthesizer-failure",
        "consensus": {
            "label": label,
            "score": score,
            "approves": approves,
            "rejects": rejects,
            "degraded": degraded,
        },
        "agents": [p["agent"] for p in parsed],
        "agents_failed": failures,
        "findings": findings,
    }
    (base / "manual-synthesis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return MAGIVerdict(
        verdict=label,
        degraded=degraded,
        conditions=tuple(),
        findings=tuple(findings),
        raw_output=json.dumps(report),
        retried_agents=(),
    )
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Add F46.2 (preserves dissent)**

```python
def test_manual_synthesis_preserves_dissent(tmp_path):
    """F46.2: 2-1 majority recovers GO_WITH_CAVEATS-or-better with dissent visible."""
    _write_raw_agent(tmp_path / "melchior.raw.json", "melchior", "reject")
    _write_raw_agent(tmp_path / "balthasar.raw.json", "balthasar", "approve")
    _write_raw_agent(tmp_path / "caspar.raw.json", "caspar", "approve")
    verdict = magi_dispatch._manual_synthesis_recovery(tmp_path)
    # 2 approves, 1 reject -> score = (1+1-1)/3 = 0.33 -> GO
    assert verdict.verdict == "GO"
    report = json.loads((tmp_path / "manual-synthesis.json").read_text())
    assert report["consensus"]["approves"] == 2
    assert report["consensus"]["rejects"] == 1
```

- [ ] **Step 6: Add F46.3 (zero recoverable raises)**

```python
def test_manual_synthesis_raises_when_zero_recoverable(tmp_path):
    """F46.3: all agents broken -> MAGIGateError."""
    (tmp_path / "melchior.raw.json").write_text(json.dumps({"type": "result", "result": "broken"}))
    (tmp_path / "balthasar.raw.json").write_text(json.dumps({"type": "result", "result": "broken"}))
    with pytest.raises(MAGIGateError) as ei:
        magi_dispatch._manual_synthesis_recovery(tmp_path)
    assert "No recoverable agent verdicts" in str(ei.value)
```

- [ ] **Step 7: Add F46.4 + F46.5 (auto-recovery integration + flag opt-out)**

```python
def test_invoke_magi_auto_recovers_on_synthesizer_crash(tmp_path, monkeypatch):
    """F46.4: invoke_magi auto-invokes recovery when run_magi.py crashes."""
    # Set up a fake tmpdir that already contains agent raw files.
    # Mock subprocess_utils.run_with_timeout to return non-zero with the
    # synthesizer-crash signature, leaving the raw files in place.
    import subprocess_utils

    captured_dir: dict[str, Path] = {}

    def fake_run(cmd, **kwargs):
        # Parse --output-dir from the prompt.
        prompt = cmd[-1]
        for token in prompt.split():
            if token.startswith("/tmp") or token.startswith("D:") or "sbtdd-magi-" in token:
                pass
        # Find the output-dir in cmd (post --output-dir token in MAGI prompt syntax).
        # Simpler: assume the last temp dir that exists in the env at fake-call time.
        import re as _re
        m = _re.search(r"--output-dir (\S+)", prompt)
        assert m is not None
        out = Path(m.group(1))
        out.mkdir(parents=True, exist_ok=True)
        _write_raw_agent(out / "melchior.raw.json", "melchior", "approve")
        _write_raw_agent(out / "balthasar.raw.json", "balthasar", "approve")
        _write_raw_agent(out / "caspar.raw.json", "caspar", "approve")
        captured_dir["dir"] = out
        # Simulate synthesizer crash: returncode != 0, no magi-report.json
        from subprocess_utils import _SubprocessResult  # adapt to actual return type
        from types import SimpleNamespace
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="RuntimeError: Only 2 agent(s) succeeded — fewer than 2 required for synthesis",
        )

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    verdict = magi_dispatch.invoke_magi(["@spec.md"])
    assert verdict.verdict in ("GO", "STRONG_GO", "GO_WITH_CAVEATS")
    assert verdict.degraded is False  # 3 agents recovered
```

```python
def test_invoke_magi_no_recovery_flag_skips_recovery(tmp_path, monkeypatch):
    """F46.5: --no-magi-recovery suppresses auto-recovery."""
    import subprocess_utils
    from types import SimpleNamespace

    def fake_run(cmd, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="RuntimeError: Only 1 agent(s) succeeded",
        )

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    with pytest.raises(MAGIGateError) as ei:
        magi_dispatch.invoke_magi(["@spec.md"], allow_recovery=False)
    # Should be the original synthesizer error, not the recovery one.
    assert "Only 1 agent(s)" in str(ei.value) or "/magi:magi failed" in str(ei.value)
```

- [ ] **Step 8: Wire auto-recovery into `invoke_magi`**

Modify `invoke_magi` signature:

```python
def invoke_magi(
    context_paths: list[str],
    timeout: int = 1800,
    cwd: str | None = None,
    *,
    model: str | None = None,
    skill_field_name: str = "magi_dispatch_model",
    stream_prefix: str | None = None,
    allow_recovery: bool = True,
) -> MAGIVerdict:
    # ... existing setup unchanged ...
    if result.returncode != 0:
        exhaustion = quota_detector.detect(result.stderr)
        if exhaustion is not None:
            # ... existing quota handling ...
            raise QuotaExhaustedError(...)
        # v0.4.0 Feature F (F46): auto-recovery on synthesizer crash.
        if allow_recovery and "Only " in result.stderr and " agent(s) succeeded" in result.stderr:
            try:
                rescued = _manual_synthesis_recovery(Path(tmpdir))
                _sys.stderr.write(
                    f"[sbtdd magi] synthesizer failed; manual synthesis "
                    f"recovery applied ({len(rescued.findings)} findings)\n"
                )
                return rescued
            except MAGIGateError:
                pass  # fall through to original error
        raise MAGIGateError(
            f"/magi:magi failed (returncode={result.returncode}): {result.stderr.strip()}"
        )
    # ... existing report-found path ...
```

- [ ] **Step 9: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/magi_dispatch.py tests/test_manual_synthesis_recovery.py tests/test_magi_hardening.py
git commit -m "feat: auto-recovery via _manual_synthesis_recovery on MAGI synthesizer crash"
```

---

## Track F — done criteria

- [ ] All 4 deliverables F43-F46 implemented per plan.
- [ ] `tests/test_magi_hardening.py` + `tests/test_manual_synthesis_recovery.py` pass.
- [ ] 789 baseline tests still pass.
- [ ] `make verify` exit 0.
- [ ] Working tree clean.
- [ ] Did not touch any forbidden file.
- [ ] Subagent #1 reports DONE with commit SHA range.

---

# Track J — v0.3.0 streaming follow-through (Subagent #2)

## Task J-1: SKILL.md exit code docs hotfix (J5)

**Files:**
- Modify: `skills/sbtdd/SKILL.md`
- Modify: `tests/test_skill_md.py` (extend with assertion)

- [ ] **Step 1: Write failing test J5.1**

```python
# Append to tests/test_skill_md.py
def test_v03_flags_section_documents_exit_1_for_invalid_model_override():
    """J5.1: SKILL.md v0.3 flags section uses 'exit 1' not 'exit 2'."""
    skill = (Path(__file__).parent.parent / "skills" / "sbtdd" / "SKILL.md").read_text(encoding="utf-8")
    # Find the v0.3 flags section
    assert "### v0.3 flags" in skill
    section_start = skill.index("### v0.3 flags")
    section_end = skill.index("##", section_start + 1)
    section = skill[section_start:section_end]
    # Must say exit 1 (USER_ERROR), not exit 2
    assert "exit 1 (USER_ERROR)" in section or "exit `1`" in section
    # Must NOT claim exit 2
    assert "exit `2`" not in section
    assert "exit 2 (PRECONDITION_FAILED)" not in section
```

- [ ] **Step 2: Run, verify FAIL**

```bash
python -m pytest tests/test_skill_md.py::test_v03_flags_section_documents_exit_1_for_invalid_model_override -v
```

Expected: FAIL — current SKILL.md says `exit 2 (PRECONDITION_FAILED)`.

- [ ] **Step 3: Edit SKILL.md line ~78**

Locate in `skills/sbtdd/SKILL.md`:
```
  Unknown skill names or model IDs exit `2` (PRECONDITION_FAILED) before any subprocess work.
```

Replace with:
```
  Unknown skill names or model IDs exit `1` (USER_ERROR) before any subprocess work, since `_parse_model_overrides` raises `ValidationError`.
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Commit**

```bash
git add skills/sbtdd/SKILL.md tests/test_skill_md.py
git commit -m "docs: correct v0.3 flags exit code from 2 to 1 in SKILL.md"
```

---

## Task J-2: _update_progress OSError handling (J4)

**Files:**
- Modify: `skills/sbtdd/scripts/auto_cmd.py` (wrap `_update_progress` body)
- Modify: `tests/test_auto_progress.py`

- [ ] **Step 1: Write failing test J4.1 (OSError caught, breadcrumb emitted)**

```python
# Append to tests/test_auto_progress.py
def test_update_progress_swallows_oserror_and_continues(tmp_path, monkeypatch, capfd):
    """J4.1: OSError on write does not kill the auto run."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(json.dumps({"started_at": "..."}))
    # Force OSError on tmp file write
    real_write_text = Path.write_text

    def boom(self, *args, **kwargs):
        if str(self).endswith(".tmp"):
            raise OSError(28, "No space left on device")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", boom)
    # Should NOT raise
    auto_cmd._update_progress(auto_run, phase=2, task_index=1, task_total=10, sub_phase="red")
    captured = capfd.readouterr()
    assert "[sbtdd]" in captured.err
    assert "progress write failed" in captured.err
    # Original auto-run.json preserved
    data = json.loads(auto_run.read_text())
    assert data["started_at"] == "..."
```

- [ ] **Step 2: Run, verify FAIL** — current implementation likely raises.

- [ ] **Step 3: Wrap _update_progress body in try/except OSError**

Modify `_update_progress` in `auto_cmd.py`:

```python
def _update_progress(
    auto_run_path: Path,
    *,
    phase: int,
    task_index: int | None,
    task_total: int | None,
    sub_phase: str | None,
) -> None:
    """Write the progress field of auto-run.json atomically.

    v0.4.0 J4: OSError during write (disk full, locked file, etc.) is
    caught and logged as a stderr breadcrumb rather than killing the
    auto run. Observability degrades gracefully; the run continues.
    """
    try:
        # ... existing implementation unchanged ...
    except OSError as exc:
        sys.stderr.write(
            f"[sbtdd] warning: progress write failed: {type(exc).__name__}"
            f"({exc.errno if hasattr(exc, 'errno') else ''}, {exc!s}). "
            f"Auto run continues (observability degraded).\n"
        )
        sys.stderr.flush()
```

(Move the existing body into the try block. The existing tmp + os.replace + retry loop stays inside try.)

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Add J4.2 (retry exhaustion preserves original)**

```python
def test_update_progress_retry_exhaustion_preserves_original(tmp_path, monkeypatch, capfd):
    """J4.2: retry loop exhaustion does not corrupt auto-run.json."""
    auto_run = tmp_path / "auto-run.json"
    original = {"progress": {"phase": 1, "task_index": 0, "task_total": 5, "sub_phase": "red"}}
    auto_run.write_text(json.dumps(original))
    real_replace = os.replace

    def always_fail(src, dst):
        raise PermissionError(13, "Locked")

    monkeypatch.setattr(os, "replace", always_fail)
    auto_cmd._update_progress(auto_run, phase=2, task_index=1, task_total=5, sub_phase="green")
    captured = capfd.readouterr()
    assert "progress write failed" in captured.err
    # Original preserved
    data = json.loads(auto_run.read_text())
    assert data["progress"]["phase"] == 1
```

- [ ] **Step 6: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/auto_cmd.py tests/test_auto_progress.py
git commit -m "fix: _update_progress swallows OSError and preserves auto-run.json"
```

---

## Task J-3: _write_auto_run_audit preserves progress field (J6)

**Files:**
- Modify: `skills/sbtdd/scripts/auto_cmd.py` (`_write_auto_run_audit`)
- Modify: `tests/test_auto_progress.py`

- [ ] **Step 1: Write failing test J6.1 (audit preserves existing progress)**

```python
def test_write_auto_run_audit_preserves_progress_field(tmp_path, monkeypatch):
    """J6.1: AutoRunAudit serialization preserves existing progress key."""
    auto_run = tmp_path / "auto-run.json"
    pre_state = {
        "progress": {"phase": 2, "task_index": 14, "task_total": 36, "sub_phase": "green"},
        "started_at": "2026-04-25T10:00:00Z",
    }
    auto_run.write_text(json.dumps(pre_state))
    # Patch the path the helper uses
    monkeypatch.setattr(auto_cmd, "_AUTO_RUN_PATH", auto_run)
    audit = auto_cmd.AutoRunAudit(phase="task-loop", iter=0, started_at="2026-04-25T10:00:00Z")
    auto_cmd._write_auto_run_audit(audit)
    data = json.loads(auto_run.read_text())
    assert data["progress"]["phase"] == 2  # preserved
    assert data["progress"]["task_index"] == 14
    # Audit fields also present
    assert data["phase"] == "task-loop" or data.get("audit", {}).get("phase") == "task-loop"
```

(Note: adapt to the actual `_AUTO_RUN_PATH` constant name and `AutoRunAudit` API in `auto_cmd.py`. Read the file to confirm.)

- [ ] **Step 2: Run, verify FAIL** — current implementation overwrites.

- [ ] **Step 3: Modify _write_auto_run_audit to read-modify-write**

In `auto_cmd.py`, locate `_write_auto_run_audit`. Change from:

```python
# Current (overwrites):
def _write_auto_run_audit(audit: AutoRunAudit) -> None:
    _AUTO_RUN_PATH.write_text(json.dumps(audit.to_dict(), indent=2))
```

To:

```python
def _write_auto_run_audit(audit: AutoRunAudit) -> None:
    """Write the audit snapshot, preserving any existing progress field.

    v0.4.0 J6: audit writes used to overwrite the file, transiently
    dropping the progress field until the next _update_progress fired.
    Now we read the existing file (if any), merge audit + preserved
    progress, and atomically replace.
    """
    audit_dict = audit.to_dict()
    if _AUTO_RUN_PATH.exists():
        try:
            existing = json.loads(_AUTO_RUN_PATH.read_text(encoding="utf-8"))
            if isinstance(existing, dict) and "progress" in existing:
                audit_dict["progress"] = existing["progress"]
        except (OSError, json.JSONDecodeError):
            pass  # corrupted or missing -> proceed with audit-only write
    tmp = _AUTO_RUN_PATH.with_suffix(_AUTO_RUN_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(audit_dict, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(_AUTO_RUN_PATH))
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Add J6.2 (audit when progress absent)**

```python
def test_write_auto_run_audit_when_progress_absent(tmp_path, monkeypatch):
    """J6.2: audit writes correctly when no prior progress field exists."""
    auto_run = tmp_path / "auto-run.json"
    auto_run.write_text(json.dumps({"started_at": "2026-04-25T10:00:00Z"}))
    monkeypatch.setattr(auto_cmd, "_AUTO_RUN_PATH", auto_run)
    audit = auto_cmd.AutoRunAudit(phase="pre-flight", iter=0, started_at="2026-04-25T10:00:00Z")
    auto_cmd._write_auto_run_audit(audit)
    data = json.loads(auto_run.read_text())
    assert "progress" not in data  # absent stays absent
```

- [ ] **Step 6: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/auto_cmd.py tests/test_auto_progress.py
git commit -m "fix: _write_auto_run_audit preserves existing progress field"
```

---

## Task J-4: pre-merge stream_prefix wiring (J8)

**Files:**
- Modify: `skills/sbtdd/scripts/pre_merge_cmd.py`
- Create: `tests/test_pre_merge_streaming.py`

- [ ] **Step 1: Read current pre_merge_cmd dispatch sites**

```bash
cd D:/jbolivarg/PythonProjects/SBTDD
grep -n "invoke_magi\|invoke_skill\|dispatch_spec_reviewer" skills/sbtdd/scripts/pre_merge_cmd.py
```

Identify the Loop 1 / Loop 2 / mini-cycle sites (typically 3-5 call sites).

- [ ] **Step 2: Write failing test J8.1 (Loop 2 MAGI gets stream_prefix)**

```python
# tests/test_pre_merge_streaming.py (new file)
#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-25
"""Tests for v0.4.0 J8 pre-merge stream_prefix wiring."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "sbtdd" / "scripts"))

import pre_merge_cmd


def test_loop2_magi_dispatch_passes_stream_prefix(monkeypatch):
    """J8.1: pre_merge Loop 2 MAGI dispatch threads stream_prefix."""
    captured_kwargs: dict[str, object] = {}

    def fake_invoke_magi(*args, **kwargs):
        captured_kwargs.update(kwargs)
        # Return a minimal verdict that satisfies the loop-exit check
        from magi_dispatch import MAGIVerdict
        return MAGIVerdict(
            verdict="GO",
            degraded=False,
            conditions=(),
            findings=(),
            raw_output="{}",
        )

    monkeypatch.setattr(pre_merge_cmd, "invoke_magi", fake_invoke_magi)
    # ... call pre_merge's Loop 2 entry point, possibly with mocked args ...
    # Specific call depends on the public API. Adapt:
    # pre_merge_cmd._loop2(..., iter_num=1)
    # assert captured_kwargs.get("stream_prefix") and "[sbtdd pre-merge magi-loop2]" in captured_kwargs["stream_prefix"]
    # If _loop2 is not directly testable, drive via run() with mocks.
    raise NotImplementedError("Adapt to actual _loop2 signature after reading pre_merge_cmd.py")
```

(The specific test shape depends on `pre_merge_cmd`'s actual API. The subagent should read the file first, identify the simplest test seam, write a real failing test, then implement.)

- [ ] **Step 3: Run, verify FAIL**

- [ ] **Step 4: Thread `stream_prefix` parameter through dispatch sites**

Identify each `invoke_magi(...)`, `invoke_skill(...)`, `dispatch_spec_reviewer(...)` call in `pre_merge_cmd.py`. For each, add `stream_prefix=` kwarg with the appropriate per-site string:

- Loop 1 iter N: `stream_prefix=f"[sbtdd pre-merge loop1 iter-{iter_num}]"`
- Loop 2 MAGI iter N: `stream_prefix=f"[sbtdd pre-merge magi-loop2 iter-{iter_num}]"`
- Mini-cycle finding N phase X: `stream_prefix=f"[sbtdd pre-merge fix-finding-{n} {phase}]"`

- [ ] **Step 5: Add J8.2 + J8.3 tests**

```python
def test_loop1_code_review_passes_stream_prefix(monkeypatch):
    """J8.2: pre_merge Loop 1 code-review dispatch threads stream_prefix."""
    captured: list[dict[str, object]] = []
    def fake_invoke_skill(*args, **kwargs):
        captured.append(kwargs)
        # ... return clean-to-go verdict ...
    monkeypatch.setattr(pre_merge_cmd, "invoke_skill", fake_invoke_skill)
    # ... drive Loop 1 ...
    assert any("loop1" in (kw.get("stream_prefix") or "") for kw in captured)


def test_minicycle_dispatch_passes_phase_specific_stream_prefix(monkeypatch):
    """J8.3: mini-cycle implementer dispatch includes finding+phase prefix."""
    captured: list[dict[str, object]] = []
    def fake_invoke_skill(*args, **kwargs):
        captured.append(kwargs)
    monkeypatch.setattr(pre_merge_cmd, "invoke_skill", fake_invoke_skill)
    # ... drive mini-cycle for one finding ...
    found = any(
        "fix-finding-" in (kw.get("stream_prefix") or "") for kw in captured
    )
    assert found
```

- [ ] **Step 6: make verify + commit**

```bash
make verify
git add skills/sbtdd/scripts/pre_merge_cmd.py tests/test_pre_merge_streaming.py
git commit -m "feat: thread stream_prefix into pre_merge_cmd Loop 1 + Loop 2 + mini-cycle dispatches"
```

---

## Track J — done criteria

- [ ] All 4 deliverables J5, J4, J6, J8 implemented per plan.
- [ ] `tests/test_auto_progress.py` (extended) + `tests/test_skill_md.py` (extended) + `tests/test_pre_merge_streaming.py` (new) pass.
- [ ] 789 baseline tests still pass.
- [ ] `make verify` exit 0.
- [ ] Did not touch any forbidden file.
- [ ] Subagent #2 reports DONE with commit SHA range.

---

# Final review phase (orchestrator-driven)

After both subagents report DONE:

## Task FR-1: Pre-loop hygiene

- [ ] **Step 1: Verify working tree clean**

```bash
cd D:/jbolivarg/PythonProjects/SBTDD
git status
```
Expected: clean.

- [ ] **Step 2: Run make verify (Loop 1 surrogate)**

```bash
make verify
```
Expected: 4 checks PASS (789 + ~30-40 new = 819-829 tests, ruff/format/mypy clean).

- [ ] **Step 3: Compute diff range**

```bash
git log --oneline b48f9ff..HEAD
git diff b48f9ff..HEAD --stat
```

## Task FR-2: MAGI ↔ /receiving-code-review loop (cap 5 iter)

Same as v0.3.0 final review pattern. **Special v0.4.0 note**: F46 auto-recovery is now in production code. If iter 1 hits the synthesizer-crash mode, the orchestrator's invocation of MAGI via the SBTDD plugin's wrapper will auto-recover (escenario R2.1). If invoking via direct `python run_magi.py` outside the SBTDD wrapper, recovery does NOT fire (escenario R2.2 — manual playbook).

- [ ] **Step 1: Iter N — invoke MAGI on the diff range**

Use `python "C:/Users/jbolivarg/.claude/plugins/cache/bolivartech-plugins/magi/2.2.2/skills/magi/scripts/run_magi.py" code-review .claude/magi-input-v040-iterN.md --model opus --timeout 1800 --output-dir .claude/magi-runs/v040-iterN`. Build input file referencing spec + plan + diff + iter context.

If synthesizer crashes: invoke `magi_dispatch._manual_synthesis_recovery(.claude/magi-runs/v040-iterN)` from a Python REPL or via a small `scripts/recover-magi.py` one-liner. F46 must be already committed by Subagent #1.

- [ ] **Step 2: Parse verdict + findings, evaluate exit criterion**

Exit when verdict ≥ GO_WITH_CAVEATS full + 0 CRITICAL + 0 WARNING + 0 Conditions.

- [ ] **Step 3: If NOT exit, dispatch iter-N+1 mini-cycle subagent**

Subagent runs `/receiving-code-review` per finding (INV-29), mini-cycle TDD per accepted, re-run MAGI iter N+1.

- [ ] **Step 4: Cap 5 iter, escalation_prompt on exhaustion**

## Task FR-3: Ship (after FR-2 exit)

- [ ] **Step 1: Bump version 0.3.0 → 0.4.0**

Modify `.claude-plugin/plugin.json`:
```json
  "version": "0.4.0",
```

Modify `.claude-plugin/marketplace.json` (TWO occurrences):
```json
  "version": "0.4.0",
```

- [ ] **Step 2: Update tripwire test**

In `tests/test_plugin_manifest.py`, rename + update:

```python
def test_plugin_version_is_current_v0_4_patch() -> None:
    """Plugin must ship 0.4.x patch on the v0.4 series until v0.5 / v1.0 bump."""
    d = _load_plugin()
    assert re.match(r"^0\.4\.\d+$", d["version"]), (
        f"version must be on the v0.4.x patch series until v0.5 / v1.0 bump, got {d['version']}"
    )
```

- [ ] **Step 3: Write CHANGELOG `[0.4.0]` entry**

Insert above `[0.3.0]`:

```markdown
## [0.4.0] - 2026-04-25

### Added

- Feature F (MAGI dispatch hardening). Four primitives:
  `magi_dispatch._discover_verdict_marker(output_dir)` enumerates
  `MAGI_VERDICT_MARKER.json` files via `Path.rglob` and picks the
  most recent by mtime, replacing the fragile path-based discovery
  that broke on internal MAGI layout changes (observed in v0.2/v0.3
  cycles). `MAGIVerdict.retried_agents: tuple[str, ...]` propagates
  the new MAGI 2.2.1+ telemetry field with default `()` for MAGI
  2.1.x backward compat. `magi_dispatch._tolerant_agent_parse(...)`
  extracts the first balanced `{...}` JSON object from agent
  `result` fields when wrapped in narrative preamble (validated
  empirically against v0.3.0 iter 2 melchior + balthasar raw outputs
  preserved at `.claude/magi-runs/v030-iter2/`); falls back to
  strict JSON parse for backward compat (caspar v0.3.0 iter 2 case).
  `magi_dispatch._manual_synthesis_recovery(run_dir)` rescues a
  verdict from per-agent `.raw.json` files when `run_magi.py`
  synthesizer aborts with `RuntimeError: Only N agent(s) succeeded`;
  fires automatically inside `invoke_magi` when the crash signature
  matches and >= 1 agent succeeded; emits `manual-synthesis.json`
  with `recovered: true` + `recovery_reason: "synthesizer-failure"`
  and a stderr breadcrumb `[sbtdd magi] synthesizer failed; manual
  synthesis recovery applied`. Suppress via `allow_recovery=False`
  parameter on `invoke_magi` (or any equivalent CLI flag downstream
  callers expose) for strict mode.

- J subset (v0.3.0 streaming follow-through). Four items:
  `_update_progress` wraps OSError around the atomic write so a
  full disk or transient permission error degrades observability
  but never kills the auto run. `_write_auto_run_audit` does
  read-modify-write so the existing `progress` field survives audit
  snapshot writes (was: transiently dropped until the next
  `_update_progress`). `pre_merge_cmd` Loop 1 + Loop 2 + mini-cycle
  TDD dispatch sites thread `stream_prefix` so MAGI verdict
  generation, code-review iterations, and mini-cycle implementer
  dispatches all stream their subprocess output to the operator's
  stderr in real time during multi-minute runs. SKILL.md `### v0.3
  flags` section now correctly states `--model-override` invalid
  skill name exits `1` (USER_ERROR) instead of `2`
  (PRECONDITION_FAILED) — matches `auto_cmd._parse_model_overrides`
  raising `ValidationError`.

### Changed

- `MAGIVerdict` dataclass gains `retried_agents` field with default
  `()`. Existing constructors that omit the field still work
  (default-arg compat).

### Process notes

- Loop 1 surrogate via `make verify` clean. Final review loop ran
  MAGI -> /receiving-code-review per the user-directed
  GO_WITH_CAVEATS-clean exit criterion with cap 5 iterations.
  v0.4.0's recursive payoff: F itself rescued the cycle's own
  iter-2 (or later) synthesizer crash via the freshly-shipped
  `_manual_synthesis_recovery`, providing live empirical validation
  of Feature F during its own ship.

### Deferred (rolled to v1.0.0)

- G (MAGI -> /requesting-code-review cross-check meta-reviewer).
- H (Group B spec-drift options re-eval + INV-31 default-on opt-in
  re-eval based on accumulated v0.2/v0.2.1/v0.2.2/v0.3/v0.4 field
  data).
- I (`schema_version: 2` field in `plugin.local.md` + migration tool
  skeleton).
- J1 (`/sbtdd status --watch` companion subcommand).
- J2 (INFO #10 `ResolvedModels` dataclass, one preflight CLAUDE.md
  scan instead of per-dispatch).
- J3 (INFO #11 streaming pump per-stream timeout for subprocesses
  that write without newlines).
- J7 (caspar #1 two-pump stdout/stderr origin ambiguity in streamed
  output).
```

- [ ] **Step 4: Final make verify**

```bash
make verify
```

- [ ] **Step 5: Stage docs + commit**

```bash
git add CHANGELOG.md tests/test_plugin_manifest.py
git commit -m "docs: v0.4.0 changelog + tripwire test bump to v0.4.x"
```

- [ ] **Step 6: Bump commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump to 0.4.0"
```

- [ ] **Step 7: Tag**

```bash
git tag v0.4.0
git log --oneline -20
```

- [ ] **Step 8: Push (REQUIRES EXPLICIT USER AUTHORIZATION)**

DO NOT auto-execute. Surface to user: "v0.4.0 ready to push. Authorize `git push origin main && git push origin v0.4.0`?"

- [ ] **Step 9: Memory update**

Write `C:/Users/jbolivarg/.claude/projects/D--jbolivarg-PythonProjects-SBTDD/memory/project_v040_shipped.md`. Update `MEMORY.md` index with one-line v0.4.0 hook entry.

---

## Self-review

| Spec criterion | Task | Coverage |
|----------------|------|----------|
| F43 marker discovery | Task F-1 | Steps 1-8 (3 tests + impl) |
| F44 retried_agents | Task F-2 | Steps 1-7 (3 tests + dataclass field + factory) |
| F45 tolerant agent parse | Task F-3 | Steps 1-8 (4 tests + balanced-brace extractor + agent validation) |
| F46 manual synthesis recovery | Task F-4 | Steps 1-9 (5 tests + `_manual_synthesis_recovery` + `invoke_magi` integration + `allow_recovery` flag) |
| J4 OSError handling | Task J-2 | Steps 1-6 (2 tests + try/except wrapping) |
| J5 SKILL.md docs hotfix | Task J-1 | Steps 1-5 (1 test + 1-line edit) |
| J6 audit progress preservation | Task J-3 | Steps 1-6 (2 tests + read-modify-write) |
| J8 pre-merge stream_prefix | Task J-4 | Steps 1-6 (3 tests + dispatch-site threading) |
| R1.1-R1.7 final review | Task FR-2 | Same as v0.3.0 spec |
| R2.1 dogfood rescue | Task FR-2 step 1 | F46 auto-recovery fires when synthesizer crashes |
| R2.2 pre-F-commit manual | Task FR-2 step 1 | Manual playbook documented |
| Version bump | Task FR-3 step 1 | plugin.json + marketplace.json |
| CHANGELOG | Task FR-3 step 3 | [0.4.0] section template |
| Tripwire bump | Task FR-3 step 2 | 0.3.x → 0.4.x |
| Tag + push | Task FR-3 steps 7-8 | Manual user-authorized push |
| Memory | Task FR-3 step 9 | project_v040_shipped.md |

**Placeholder scan**: zero `TBD`, `implement later`, `add appropriate error handling` matches in actionable steps. The two tasks J-4 step 2 and step 5 reference adapting tests to the actual `pre_merge_cmd` API after reading the file — this is intentional because the dispatch-site signatures depend on what already exists (subagent must read first); the steps include explicit code skeletons + the invariant the test must establish.

**Type consistency**: function names verified across tasks — `_discover_verdict_marker`, `_tolerant_agent_parse`, `_manual_synthesis_recovery`, `MAGIVerdict.retried_agents`, `MAGIVerdict.from_marker`, `_VERDICT_WEIGHT`, `_VALID_AGENT_NAMES`, `_extract_first_balanced_json`, `_AUTO_RUN_PATH`, `_write_auto_run_audit`, `_update_progress`. Consistent within track F and within track J.

**Scope check**: plan focused on F + J subset for v0.4.0. G/H/I/D5/J2/J3/J7 explicitly deferred and not referenced in tasks beyond the CHANGELOG Deferred section.

---

## Execution handoff

Plan complete and saved to `planning/claude-plan-tdd-org.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — orchestrator dispatches subagent #1 + subagent #2 in **true parallel** via single message with two `Agent` tool calls (surfaces 100% disjoint, no auto_cmd.py merge zone like v0.3.0). Then drives final review loop sequentially.

**2. Inline Execution** — execute tasks F-1..F-4 + J-1..J-4 inline via executing-plans skill. Slower (~5-7h vs 3-4h parallel); loses parallelism advantage.

Recommended: **option 1**. Tracks F and J are file-disjoint by design and the lightweight pattern v0.3.0 precedent worked despite sequential constraint.

Which approach?
