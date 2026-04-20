# Milestone D: Gates Polish + Edge-Case Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Endurecer el plugin `sbtdd-workflow` tras Milestones A+B+C — codificar el schema de `.claude/auto-run.json`, reforzar INV-25/INV-26 con tests de regresion, aplicar parsing estricto a las shims de toolchain Rust, validar version floor de Python, hacer fail-loud al reporter Rust cuando falta el env var `NEXTEST_EXPERIMENTAL_LIBTEST_JSON`, blindar `ctest_reporter` contra XML vacio, mejorar `resume` ante interrupciones en Loop 2 + escrituras concurrentes + dry-run end-to-end, enriquecer los reportes de salida exit 8 en `pre_merge_cmd` y `auto_cmd`, y consolidar 3 INFOs diferidos de documentacion de milestones anteriores. **Cero nuevas superficies de feature** — es un milestone de estabilidad/correctitud/ops.

**Architecture:** Python 3.9+ stdlib only. Se anaden dos dataclasses (`AutoRunAudit`, opcional `AutoRunStatus` enum via `typing.Literal`) para formalizar el schema JSON de `auto-run.json`, reemplazando los dict-writes ad-hoc. Se anade un helper `_parse_version_string` en `dependency_check.py` y un `_REQUIRED_VERSION_REGEX` (patron por binario). Se anade `ensure_nextest_experimental_env()` en `reporters/rust_reporter.py` para detectar el flag antes de lanzar el pipeline. Se enriquecen `_write_magi_conditions_file` (pre_merge_cmd) y `_write_auto_run_audit` (auto_cmd) con resumenes estructurados de conditions accepted/rejected. `resume_cmd` gana una rama nueva en `_decide_delegation` para detectar `magi-conditions.md` pendiente y dirigir al usuario. Todos los cambios son TDD-Guard-amigables y siguen el commit-prefix mapping de sec.M.5.

**Tech Stack:** Python 3.9+ stdlib + PyYAML (ya en dev deps desde Milestone A). Sin nuevas runtime deps. Tests con pytest + monkeypatch. mypy strict. ruff line-length 100.

---

## File Structure

Archivos modificados/creados en este milestone:

```
skills/sbtdd/scripts/
├── auto_cmd.py               # MODIFIED: AutoRunAudit dataclass, INV-25/26 hardening, exit 8 enriquecido
├── dependency_check.py       # MODIFIED: version floor Python, parsing de version cargo-clippy/cargo-fmt
├── reporters/
│   ├── rust_reporter.py      # MODIFIED: deteccion env var NEXTEST_EXPERIMENTAL_LIBTEST_JSON
│   └── ctest_reporter.py     # MODIFIED: manejo de JUnit XML vacio (0 bytes)
├── pre_merge_cmd.py          # MODIFIED: stderr summary de exit 8, docstring INV-29
├── resume_cmd.py             # MODIFIED: rama magi-conditions.md pendiente, docstring
└── init_cmd.py               # MODIFIED: comentario TOCTOU en _mkdir_tracked

tests/
├── test_auto_run_audit.py    # NEW: schema AutoRunAudit dataclass
├── test_auto_cmd_inv25.py    # NEW: INV-25 branch-scoped enforcement (no push/merge/gh/pr)
├── test_auto_cmd_inv26.py    # NEW: INV-26 audit trail completeness
├── test_auto_cmd_exit8.py    # NEW: exit 8 enriquecido con counts
├── test_dependency_check_rust_versions.py  # NEW: version-regex validation
├── test_dependency_check_python_floor.py   # NEW: Python < 3.9 rejection
├── test_rust_reporter_nextest_env.py       # NEW: env var detection
├── test_ctest_reporter_empty_xml.py        # NEW: 0-byte XML handling
├── test_resume_cmd_magi_conditions.py      # NEW: resume mid-pre-merge exit 8
├── test_resume_cmd_concurrent_state.py     # NEW: concurrent state file write
├── test_resume_cmd_dry_run_integration.py  # NEW: dry-run end-to-end
├── test_pre_merge_cmd_exit8.py             # NEW: stderr summary de exit 8
└── test_inv_documentation.py               # NEW: docstring contract (INV-24, INV-29)

tests/fixtures/
├── junit-xml/
│   ├── empty.xml             # NEW: 0-byte file
│   └── malformed.xml         # NEW: opening tag only
└── auto-run/
    ├── happy-path.json       # NEW: AutoRunAudit OK round-trip
    └── gate-blocked.json     # NEW: status=magi_gate_blocked
```

Tareas: 18 total. Orden lineal por fase — Fase 1 entrega el schema de auto-run + hardening INV-25/26 (consumido por Fases 3 y 4); Fase 2 endurece las pre-flight checks y reporters (independiente del resto); Fase 3 mejora `resume` + exit 8 UX (depende del schema de Fase 1); Fase 4 consolida INFOs de documentacion de milestones previos.

**Comandos de verificacion por fase TDD** (sec.M.0.1 + CLAUDE.local.md §0.1):

```bash
python -m pytest tests/ -v          # All pass, 0 fail
python -m ruff check .              # 0 warnings
python -m ruff format --check .     # Clean
python -m mypy .                    # No type errors
```

Atajo: `make verify` corre los 4 en orden.

**Supuestos post-Milestones A+B+C (consumidos, no re-implementados):**

- `errors.SBTDDError`, `ValidationError`, `StateFileError`, `DriftError`, `DependencyError`, `PreconditionError`, `MAGIGateError`, `QuotaExhaustedError`, `CommitError`, `Loop1DivergentError`, `VerificationIrremediableError`, `ChecklistError`, `EXIT_CODES`.
- `models.COMMIT_PREFIX_MAP`, `VERDICT_RANK`, `VALID_SUBCOMMANDS`, `verdict_meets_threshold`.
- `state_file.SessionState`, `load`, `save`, `validate_schema`.
- `drift.detect_drift`, `DriftReport`.
- `config.PluginConfig`, `load_plugin_local`.
- `templates.expand`.
- `hooks_installer.merge`, `read_existing`.
- `subprocess_utils.run_with_timeout`, `kill_tree`.
- `quota_detector.detect`.
- `commits.create`, `validate_prefix`, `validate_message`.
- `dependency_check.check_python`, `check_git`, `check_tdd_guard_binary`, `check_tdd_guard_data_dir`, `check_claude_cli`, `check_superpowers`, `check_magi`, `check_stack_toolchain`, `check_working_tree`, `check_environment`, `DependencyReport`, `DependencyCheck`, `_check_binary`, `_CARGO_SUBCOMMAND_SHIMS`, `_STACK_TOOLCHAINS`.
- `superpowers_dispatch` (12 typed wrappers).
- `magi_dispatch.invoke_magi`, `parse_verdict`, `MAGIVerdict`, `verdict_is_strong_no_go`, `verdict_passes_gate`, `write_verdict_artifact`.
- `reporters.tdd_guard_schema` (`TestEntry`, `TestError`, `TestJSON`, `TestModule`, `write_test_json`).
- `reporters.rust_reporter.run_pipeline`, `_NEXTEST_CMD`, `_TDD_GUARD_RUST_CMD`.
- `reporters.ctest_reporter.parse_junit`, `run`.
- `run_sbtdd.SUBCOMMAND_DISPATCH`, `SubcommandHandler`, `_exit_code_for`.
- `auto_cmd._write_auto_run_audit`, `_phase5_report`.
- `pre_merge_cmd._write_magi_conditions_file`, `_write_magi_feedback_file`, `_loop1`, `_loop2`.
- `resume_cmd._report_diagnostic`, `_recheck_environment`, `_decide_delegation`, `_delegate`, `_resolve_uncommitted`.
- `init_cmd._mkdir_tracked`, `_rollback_partial_copy`, `_phase5_relocate`.

---

## Commit prefix policy

Precedente de Milestones A, B y C:

- Cuando un task introduce **un modulo nuevo** (test file + impl file que no existian), un commit unico con prefijo `test:` es canonico (sec.M.5 row 1).
- Cuando un task agrega **nueva logica a un modulo preexistente** con tests downstream que dependen del contrato, se exige split `test:` (Red) → `feat:`/`fix:` (Green) → opcional `refactor:`.

En Milestone D **no se introducen modulos nuevos en `skills/sbtdd/scripts/`**. Todas las tareas de este milestone modifican modulos preexistentes (Milestones A-C); por lo tanto cada task sigue el patron estricto:

1. `test:` — nuevo test que falla por contrato ausente (Red).
2. `feat:` o `fix:` — implementacion minima que cubre el test (Green). `feat:` para comportamiento nuevo; `fix:` para hardening ante input invalido / edge cases / bugs latentes.
3. `refactor:` — opcional, solo si aplica limpieza post-Green.

Excepciones explicitas por task:

- **Task 0 (fixtures bootstrap):** `chore:` cuando solo agrega JSON/XML/MD bajo `tests/fixtures/` sin codigo Python.
- **Tasks 16-18 (documentacion, Fase 4):** `docs:` para cambios que son puramente docstrings cross-reference / comentarios.

Todos los commits:

1. Ingles, sin `Co-Authored-By`, sin menciones a Claude/AI/asistente (`~/.claude/CLAUDE.md` §Git, INV-5..7).
2. Atomico — un task == un commit (o el ciclo Red-Green-Refactor cuando aplica).
3. Prefijo del mapa sec.M.5 via `commits.create` cuando se commitea codigo del plan; para bookkeeping (fixtures, docstrings) se usa `git commit` directo sin pasar por `commits.create`.

---

## Test isolation policy

Heredada de Milestones B y C: todos los tests que sustituyen atributos de modulos DEBEN usar `monkeypatch.setattr(...)` / `monkeypatch.setitem(...)` exclusivamente — nunca asignacion directa. La auto-restauracion de `monkeypatch` evita polucion cross-test.

Cada test file de Milestone D usa `tmp_path` para aislar filesystem state (state file + plan + git repo + auto-run.json + magi-verdict.json). Cuando hace falta un git repo real, usa `subprocess.run(["git", "init"], cwd=tmp_path)` dentro de una fixture `pytest.fixture`.

Los tests de "spy" para INV-25 (no push/merge) y INV-26 (audit trail completeness) usan un wrapper de `subprocess_utils.run_with_timeout` capturado en una lista `recorded_calls: list[list[str]]` via `monkeypatch.setattr(subprocess_utils, "run_with_timeout", spy)`. Al final del test, se asserta que ningun item de `recorded_calls` contiene `"push" | "merge" | "gh" | "pr"` como argv[1] o argv[0].

---

## Frozen-module policy

**Milestones A, B y C estan congelados.** Este milestone modifica modulos de A/B/C solo cuando el hardening lo exige, y cada modificacion lleva su propio test de regresion explicito. Ningun test existente debe romperse: si un test previo falla tras un cambio, hay que entender el motivo (no silenciarlo) y ajustar el cambio. Los archivos frozen tocables en Milestone D y la razon:

| Archivo | Razon | Test de regresion |
|---------|-------|-------------------|
| `auto_cmd.py` | AutoRunAudit + INV-25/26 + exit 8 enriquecido | `test_auto_run_audit.py`, `test_auto_cmd_inv25.py`, `test_auto_cmd_inv26.py`, `test_auto_cmd_exit8.py` |
| `dependency_check.py` | Python floor + cargo-clippy/fmt version regex | `test_dependency_check_python_floor.py`, `test_dependency_check_rust_versions.py` |
| `reporters/rust_reporter.py` | NEXTEST_EXPERIMENTAL_LIBTEST_JSON detection | `test_rust_reporter_nextest_env.py` |
| `reporters/ctest_reporter.py` | 0-byte XML handling | `test_ctest_reporter_empty_xml.py` |
| `pre_merge_cmd.py` | Stderr summary de exit 8, docstring INV-29 | `test_pre_merge_cmd_exit8.py`, `test_inv_documentation.py` |
| `resume_cmd.py` | Magi-conditions.md pendiente, concurrent state write, dry-run integration, docstring INV-24 | `test_resume_cmd_magi_conditions.py`, `test_resume_cmd_concurrent_state.py`, `test_resume_cmd_dry_run_integration.py`, `test_inv_documentation.py` |
| `init_cmd.py` | Comentario TOCTOU en _mkdir_tracked | `test_inv_documentation.py` |

---

## Phase 0: Pre-flight and fixtures (Task 0)

### Task 0: Fixture scaffolding for D tests

**Files:**
- Create: `tests/fixtures/junit-xml/empty.xml`
- Create: `tests/fixtures/junit-xml/malformed.xml`
- Create: `tests/fixtures/auto-run/happy-path.json`
- Create: `tests/fixtures/auto-run/gate-blocked.json`

Estos fixtures alimentan tests de Fases 1 y 2. Se crean una sola vez al inicio del milestone.

- [ ] **Step 1: Create junit-xml fixtures**

Create `tests/fixtures/junit-xml/empty.xml` as a zero-byte file:

```bash
mkdir -p tests/fixtures/junit-xml
: > tests/fixtures/junit-xml/empty.xml
```

Create `tests/fixtures/junit-xml/malformed.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
```

(Intentionally truncated — missing closing tag. Parse must raise `ValidationError`, not a bare `ParseError`.)

- [ ] **Step 2: Create auto-run fixtures**

Create `tests/fixtures/auto-run/happy-path.json`:

```json
{
  "schema_version": 1,
  "auto_started_at": "2026-04-19T10:00:00Z",
  "auto_finished_at": "2026-04-19T10:15:00Z",
  "status": "success",
  "verdict": "GO",
  "degraded": false,
  "accepted_conditions": 0,
  "rejected_conditions": 0,
  "tasks_completed": 3,
  "error": null
}
```

Create `tests/fixtures/auto-run/gate-blocked.json`:

```json
{
  "schema_version": 1,
  "auto_started_at": "2026-04-19T10:00:00Z",
  "auto_finished_at": "2026-04-19T10:20:00Z",
  "status": "magi_gate_blocked",
  "verdict": "GO_WITH_CAVEATS",
  "degraded": false,
  "accepted_conditions": 2,
  "rejected_conditions": 1,
  "tasks_completed": 3,
  "error": "MAGI iter 1 produced 2 accepted condition(s); apply them via `sbtdd close-phase`."
}
```

- [ ] **Step 3: Verify fixture load round-trip**

```bash
python -c "import json; d=json.load(open('tests/fixtures/auto-run/happy-path.json')); assert d['status']=='success'; print('OK')"
python -c "p=open('tests/fixtures/junit-xml/empty.xml','rb').read(); assert len(p)==0; print('OK')"
```

Expected: `OK` printed twice.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/junit-xml/ tests/fixtures/auto-run/
git commit -m "chore: add junit-xml and auto-run fixtures for Milestone D tests"
```

---

## Phase 1: Auto-mode hardening (Tasks 1-4 — scope items 1, 2, 3, 12)

Foundation for Fase 3 (exit 8 UX). Orden: AutoRunAudit schema primero (Task 1), luego los dos tests de regresion INV (Tasks 2-3), finalmente el enriquecimiento de exit 8 con counts (Task 4).

### Task 1: `AutoRunAudit` dataclass + schema validation (scope item 1)

**Files:**
- Modify: `skills/sbtdd/scripts/auto_cmd.py`
- Create: `tests/test_auto_run_audit.py`

Objetivo: codificar un schema frozen para `.claude/auto-run.json`. Hoy `_write_auto_run_audit` acepta `dict[str, object]` — cualquier typo produce silent corruption. Introducimos `AutoRunAudit` como `@dataclass(frozen=True)` con campos tipados + `from_dict`/`to_dict` + `validate_schema`. La firma de `_write_auto_run_audit` se mantiene hacia atras (dict) pero acepta tambien `AutoRunAudit`; internamente valida antes de escribir.

- [ ] **Step 1: Write failing test**

```python
# tests/test_auto_run_audit.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

import auto_cmd


def test_auto_run_audit_is_frozen_dataclass() -> None:
    audit = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at="2026-04-19T10:15:00Z",
        status="success",
        verdict="GO",
        degraded=False,
        accepted_conditions=0,
        rejected_conditions=0,
        tasks_completed=3,
        error=None,
    )
    with pytest.raises((AttributeError, Exception)):
        audit.status = "magi_gate_blocked"  # type: ignore[misc]


def test_auto_run_audit_from_dict_round_trip(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/auto-run/happy-path.json").read_text("utf-8")
    payload = json.loads(fixture)
    audit = auto_cmd.AutoRunAudit.from_dict(payload)
    assert audit.schema_version == 1
    assert audit.status == "success"
    assert audit.tasks_completed == 3
    assert audit.to_dict() == payload


def test_auto_run_audit_rejects_unknown_status() -> None:
    with pytest.raises(auto_cmd.ValidationError) as exc:
        auto_cmd.AutoRunAudit(
            schema_version=1,
            auto_started_at="2026-04-19T10:00:00Z",
            auto_finished_at=None,
            status="something_else",
            verdict=None,
            degraded=None,
            accepted_conditions=0,
            rejected_conditions=0,
            tasks_completed=0,
            error=None,
        ).validate_schema()
    assert "status" in str(exc.value)


def test_auto_run_audit_rejects_negative_counts() -> None:
    audit = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at=None,
        status="success",
        verdict="GO",
        degraded=False,
        accepted_conditions=-1,
        rejected_conditions=0,
        tasks_completed=0,
        error=None,
    )
    with pytest.raises(auto_cmd.ValidationError):
        audit.validate_schema()


def test_write_auto_run_audit_accepts_audit_object(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "auto-run.json"
    audit = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at="2026-04-19T10:05:00Z",
        status="success",
        verdict="GO",
        degraded=False,
        accepted_conditions=0,
        rejected_conditions=0,
        tasks_completed=2,
        error=None,
    )
    auto_cmd._write_auto_run_audit(target, audit)
    data = json.loads(target.read_text("utf-8"))
    assert data["schema_version"] == 1
    assert data["status"] == "success"


def test_write_auto_run_audit_validates_before_write(tmp_path: Path) -> None:
    target = tmp_path / ".claude" / "auto-run.json"
    bad = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at=None,
        status="bogus",
        verdict=None,
        degraded=None,
        accepted_conditions=0,
        rejected_conditions=0,
        tasks_completed=0,
        error=None,
    )
    with pytest.raises(auto_cmd.ValidationError):
        auto_cmd._write_auto_run_audit(target, bad)
    assert not target.exists()


def test_write_auto_run_audit_back_compat_dict(tmp_path: Path) -> None:
    # Regression: existing call sites still pass dicts. Dict writes MUST
    # succeed identically to pre-Milestone-D behavior (validation is best-
    # effort for dicts; strict validation kicks in only when AutoRunAudit
    # is explicitly passed).
    target = tmp_path / ".claude" / "auto-run.json"
    auto_cmd._write_auto_run_audit(target, {"auto_started_at": "2026-04-19T10:00:00Z"})
    data = json.loads(target.read_text("utf-8"))
    assert data["auto_started_at"] == "2026-04-19T10:00:00Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_auto_run_audit.py -v`
Expected: FAIL — `AttributeError: module 'auto_cmd' has no attribute 'AutoRunAudit'`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_auto_run_audit.py
git commit -m "test: add AutoRunAudit schema contract tests"
```

- [ ] **Step 4: Write minimal implementation**

Modify `skills/sbtdd/scripts/auto_cmd.py`. Add imports (top of file, preserving ordering):

```python
from dataclasses import dataclass, asdict
from typing import Union
from errors import ValidationError
```

Add the allowed statuses tuple and dataclass (after the module docstring, before `_build_parser`):

```python
#: Allowed values for AutoRunAudit.status. Extending this set is a schema
#: change: bump ``_AUTO_RUN_SCHEMA_VERSION`` below and update tests.
_ALLOWED_AUTO_RUN_STATUSES: tuple[str, ...] = (
    "success",
    "magi_gate_blocked",
    "verification_irremediable",
    "loop1_divergent",
    "quota_exhausted",
    "checklist_failed",
    "drift_detected",
    "precondition_failed",
)

#: Current schema version for ``.claude/auto-run.json``. Bump when a
#: backwards-incompatible change lands (field removed, type changed,
#: status value removed). Additive changes (new status, new optional
#: field) keep the version.
_AUTO_RUN_SCHEMA_VERSION: int = 1


@dataclass(frozen=True)
class AutoRunAudit:
    """Frozen schema for ``.claude/auto-run.json`` (INV-26 audit trail).

    Formalises the opportunistic dict writes used in Milestone C. Every
    field is required; ``to_dict`` is symmetric with ``from_dict`` and
    the shape is asserted by ``validate_schema``. Bump
    ``schema_version`` via ``_AUTO_RUN_SCHEMA_VERSION`` for
    backwards-incompatible changes.

    Attributes:
        schema_version: Integer version (1 for v0.1 of the plugin).
        auto_started_at: ISO 8601 timestamp of ``main`` entry.
        auto_finished_at: ISO 8601 timestamp of ``main`` exit, or
            ``None`` when the run is still in progress / aborted mid-way.
        status: One of :data:`_ALLOWED_AUTO_RUN_STATUSES`.
        verdict: The gating MAGI verdict string (``GO`` / ``GO_WITH_CAVEATS``
            / ``STRONG_NO_GO`` / ...), or ``None`` if the run aborted
            before Phase 3 completed.
        degraded: ``True`` when MAGI returned degraded consensus; ``None``
            if no verdict was obtained.
        accepted_conditions: Count of MAGI conditions accepted by
            ``/receiving-code-review`` across all Loop 2 iterations.
        rejected_conditions: Count of MAGI conditions rejected by
            ``/receiving-code-review``.
        tasks_completed: Number of plan tasks that reached
            ``current_phase == 'done'`` during this auto run.
        error: Free-form error message when ``status != 'success'``,
            ``None`` on success.
    """

    schema_version: int
    auto_started_at: str
    auto_finished_at: str | None
    status: str
    verdict: str | None
    degraded: bool | None
    accepted_conditions: int
    rejected_conditions: int
    tasks_completed: int
    error: str | None

    def validate_schema(self) -> None:
        """Raise :class:`ValidationError` on any schema inconsistency."""
        if self.schema_version != _AUTO_RUN_SCHEMA_VERSION:
            raise ValidationError(
                f"AutoRunAudit.schema_version={self.schema_version} != "
                f"expected {_AUTO_RUN_SCHEMA_VERSION}"
            )
        if self.status not in _ALLOWED_AUTO_RUN_STATUSES:
            raise ValidationError(
                f"AutoRunAudit.status={self.status!r} not in "
                f"{sorted(_ALLOWED_AUTO_RUN_STATUSES)}"
            )
        if self.accepted_conditions < 0:
            raise ValidationError(
                f"AutoRunAudit.accepted_conditions={self.accepted_conditions} < 0"
            )
        if self.rejected_conditions < 0:
            raise ValidationError(
                f"AutoRunAudit.rejected_conditions={self.rejected_conditions} < 0"
            )
        if self.tasks_completed < 0:
            raise ValidationError(
                f"AutoRunAudit.tasks_completed={self.tasks_completed} < 0"
            )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable dict representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AutoRunAudit:
        """Build an :class:`AutoRunAudit` from a parsed JSON dict."""
        return cls(
            schema_version=int(data.get("schema_version", _AUTO_RUN_SCHEMA_VERSION)),
            auto_started_at=str(data["auto_started_at"]),
            auto_finished_at=(
                str(data["auto_finished_at"])
                if data.get("auto_finished_at") is not None
                else None
            ),
            status=str(data.get("status", "success")),
            verdict=(str(data["verdict"]) if data.get("verdict") is not None else None),
            degraded=(
                bool(data["degraded"]) if data.get("degraded") is not None else None
            ),
            accepted_conditions=int(data.get("accepted_conditions", 0)),
            rejected_conditions=int(data.get("rejected_conditions", 0)),
            tasks_completed=int(data.get("tasks_completed", 0)),
            error=(str(data["error"]) if data.get("error") is not None else None),
        )
```

Modify `_write_auto_run_audit` to accept the union type + validate:

```python
def _write_auto_run_audit(
    path: Path, payload: Union[AutoRunAudit, dict[str, object]]
) -> None:
    """Write ``.claude/auto-run.json`` with ``payload`` validated.

    Accepts either an :class:`AutoRunAudit` (fully validated) or a raw
    ``dict`` (back-compat for pre-Milestone-D call sites; written as-is
    without schema validation). All Milestone-D write sites pass
    ``AutoRunAudit``; legacy ``dict`` writes survive so the incremental
    migration inside ``main`` stays green between commits.
    """
    if isinstance(payload, AutoRunAudit):
        payload.validate_schema()
        data: dict[str, object] = payload.to_dict()
    else:
        data = dict(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

- [ ] **Step 5: Run test to verify it passes** — 7 tests green.

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/auto_cmd.py
git commit -m "feat: add AutoRunAudit dataclass with schema validation"
```

- [ ] **Step 7: Migrate internal call sites to AutoRunAudit**

Replace the two `_write_auto_run_audit(auto_run, {...})` inline dict writes in `main` and the one in `_phase5_report` with explicit `AutoRunAudit(...)` constructions. The MAGIGateError branch builds a `status="magi_gate_blocked"` audit. The happy-path `_phase5_report` builds a `status="success"` audit. Use `_now_iso()` for timestamps. Tasks_completed comes from reading the final state's position in the plan (count of `[x]` tasks); accepted/rejected conditions default to 0 for this migration (Task 4 fills them in).

Run: `python -m pytest tests/ -v` — all Milestone C tests MUST still pass (regression). If any fails, revert and re-analyze; the dict back-compat path exists precisely so this migration can be incremental.

- [ ] **Step 8: Commit refactor**

```bash
git add skills/sbtdd/scripts/auto_cmd.py
git commit -m "refactor: migrate auto_cmd call sites to AutoRunAudit"
```

---

### Task 2: INV-25 branch-scoped enforcement test (scope item 2)

**Files:**
- Create: `tests/test_auto_cmd_inv25.py`

Objetivo: regresion test asegurando que `auto_cmd` NUNCA invoca `git push`, `git merge`, `gh *`, ni subprocess con comando que contenga `pr` como primer argumento. Spy sobre `subprocess_utils.run_with_timeout` + cualquier otro dispatch.

- [ ] **Step 1: Write failing test**

```python
# tests/test_auto_cmd_inv25.py
from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import auto_cmd
import subprocess_utils
import superpowers_dispatch


_FORBIDDEN_FIRST_ARGS = ("push", "merge")
_FORBIDDEN_EXECUTABLES = ("gh",)


def _assert_no_remote_ops(calls: list[list[str]]) -> None:
    for argv in calls:
        if not argv:
            continue
        exe = argv[0]
        assert exe not in _FORBIDDEN_EXECUTABLES, (
            f"INV-25 violated: auto invoked {exe} (argv={argv})"
        )
        if exe == "git" and len(argv) >= 2:
            assert argv[1] not in _FORBIDDEN_FIRST_ARGS, (
                f"INV-25 violated: auto invoked `git {argv[1]}` (argv={argv})"
            )
        # Catch gh pr invocations routed via different launchers
        joined = " ".join(argv).lower()
        assert "gh pr" not in joined, (
            f"INV-25 violated: auto invoked `gh pr` via {argv}"
        )


@pytest.fixture()
def spy_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    recorded: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:  # noqa: ARG001
        recorded.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    return recorded


def test_auto_dry_run_records_zero_remote_ops(
    tmp_path: Path, spy_subprocess: list[list[str]]
) -> None:
    auto_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    _assert_no_remote_ops(spy_subprocess)
    assert spy_subprocess == []  # Dry-run MUST be side-effect-free (Finding 4)


def test_auto_cmd_no_finishing_branch_skill_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """INV-25 partner: /finishing-a-development-branch NEVER invoked by auto."""
    calls: list[tuple[str, object]] = []
    original = superpowers_dispatch.finishing_a_development_branch

    def fake_finish(*args: Any, **kwargs: Any) -> Any:
        calls.append(("finishing_a_development_branch", (args, kwargs)))
        return original(*args, **kwargs)

    monkeypatch.setattr(
        superpowers_dispatch, "finishing_a_development_branch", fake_finish
    )
    # Even if the main flow were to run all phases, the finishing skill
    # must NOT appear in the call log. We simulate via dry-run which
    # short-circuits — the assertion still holds.
    auto_cmd.main(["--project-root", ".", "--dry-run"])
    assert not any(
        name == "finishing_a_development_branch" for name, _ in calls
    ), "INV-25 violated: auto invoked /finishing-a-development-branch"
```

- [ ] **Step 2: Run test** — these tests PASS immediately because the current implementation already respects INV-25 (by design, it never calls push/merge/gh). This task is a **regression-pinning** test, not a failing-first test. Document this explicitly in the task and skip the Red commit; the commit message uses `test:` but represents a regression pin:

- [ ] **Step 3: Commit pinning test**

```bash
git add tests/test_auto_cmd_inv25.py
git commit -m "test: pin INV-25 branch-scoped enforcement in auto_cmd"
```

- [ ] **Step 4: Sanity sweep**

Run `python -m pytest tests/test_auto_cmd_inv25.py -v`. Expected: 2 green.

Run `python -m ruff check tests/test_auto_cmd_inv25.py` and `python -m mypy tests/test_auto_cmd_inv25.py` — both clean.

---

### Task 3: INV-26 audit trail completeness test (scope item 3)

**Files:**
- Create: `tests/test_auto_cmd_inv26.py`

Objetivo: regresion test asegurando que cada task commit, phase close, pre-merge verdict y exit-code emission quedan registrados en `auto-run.json` tras una corrida sintetica de 3 tareas. Usa `AutoRunAudit.from_dict` para validar el final.

- [ ] **Step 1: Write failing test**

```python
# tests/test_auto_cmd_inv26.py
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import auto_cmd


def test_auto_run_json_conforms_to_schema_on_dry_run(tmp_path: Path) -> None:
    # Dry-run short-circuits before Phase 1; no auto-run.json is
    # written. Pin that behavior: dry-run MUST not create the file
    # (Finding 4 regression).
    auto_cmd.main(["--project-root", str(tmp_path), "--dry-run"])
    assert not (tmp_path / ".claude" / "auto-run.json").exists()


def test_auto_run_audit_from_dict_on_happy_path_fixture() -> None:
    fixture_path = Path("tests/fixtures/auto-run/happy-path.json")
    data = json.loads(fixture_path.read_text("utf-8"))
    audit = auto_cmd.AutoRunAudit.from_dict(data)
    audit.validate_schema()
    assert audit.status == "success"
    assert audit.tasks_completed == 3


def test_auto_run_audit_from_dict_on_gate_blocked_fixture() -> None:
    fixture_path = Path("tests/fixtures/auto-run/gate-blocked.json")
    data = json.loads(fixture_path.read_text("utf-8"))
    audit = auto_cmd.AutoRunAudit.from_dict(data)
    audit.validate_schema()
    assert audit.status == "magi_gate_blocked"
    assert audit.accepted_conditions == 2
    assert audit.rejected_conditions == 1


def test_gate_blocked_write_records_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate the MAGIGateError branch: _write_auto_run_audit receives
    # an AutoRunAudit with status=magi_gate_blocked + non-zero counts.
    # Validate the file shape.
    target = tmp_path / ".claude" / "auto-run.json"
    audit = auto_cmd.AutoRunAudit(
        schema_version=1,
        auto_started_at="2026-04-19T10:00:00Z",
        auto_finished_at="2026-04-19T10:20:00Z",
        status="magi_gate_blocked",
        verdict="GO_WITH_CAVEATS",
        degraded=False,
        accepted_conditions=2,
        rejected_conditions=1,
        tasks_completed=3,
        error="MAGI iter 1 produced 2 accepted condition(s).",
    )
    auto_cmd._write_auto_run_audit(target, audit)
    data = json.loads(target.read_text("utf-8"))
    assert data["accepted_conditions"] == 2
    assert data["rejected_conditions"] == 1
    assert data["tasks_completed"] == 3
    assert data["status"] == "magi_gate_blocked"
```

- [ ] **Step 2: Run test**

First two fixture tests PASS immediately once Task 1 is in (the fixtures validate against the new schema). The dry-run and gate-blocked write tests depend on Task 1's migration — if step 7 of Task 1 was completed, the third test passes; otherwise it may fail because AutoRunAudit is not yet used at gate-block paths. Task 4 completes this migration; for Task 3 this test pins the contract.

- [ ] **Step 3: Commit pinning test**

```bash
git add tests/test_auto_cmd_inv26.py
git commit -m "test: pin INV-26 audit-trail schema conformance in auto_cmd"
```

- [ ] **Step 4: Sanity sweep**

Run `python -m pytest tests/test_auto_cmd_inv26.py -v`. Expected: 4 green.

---

### Task 4: Exit 8 enriched report with condition counts (scope item 12)

**Files:**
- Modify: `skills/sbtdd/scripts/auto_cmd.py`
- Create: `tests/test_auto_cmd_exit8.py`

Objetivo: cuando `auto_cmd` llega a exit 8 (MAGIGateError), el audit trail anadido en Task 1 debe registrar `accepted_conditions` y `rejected_conditions`. Hoy los unicos signals son `status + error`. Captamos los counts propagandolos desde `pre_merge_cmd._loop2` hasta `auto_cmd._phase3_pre_merge`.

Adicionalmente, el mensaje a stderr debe incluir estos counts en una linea concisa.

- [ ] **Step 1: Write failing test**

```python
# tests/test_auto_cmd_exit8.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import auto_cmd
from errors import MAGIGateError


def test_auto_cmd_exit8_records_condition_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Simulate _phase3_pre_merge raising MAGIGateError with a msg that
    # encodes accepted=2 rejected=1. The MAGIGateError handling branch
    # in main MUST include these counts in the AutoRunAudit written to
    # auto-run.json.
    state_dir = tmp_path / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "auto-run.json").unlink(missing_ok=True)

    def fake_phase1(ns: Any) -> tuple[Any, Any]:
        return (None, None)

    def fake_phase3(ns: Any, cfg: Any) -> Any:
        # Raise as pre_merge_cmd._loop2 would
        raise MAGIGateError(
            "MAGI iter 1 produced 2 accepted condition(s); "
            "apply them via `sbtdd close-phase` and re-run `sbtdd pre-merge`. "
            "See .claude/magi-conditions.md."
        )

    monkeypatch.setattr(auto_cmd, "_phase1_preflight", fake_phase1)
    monkeypatch.setattr(auto_cmd, "_phase3_pre_merge", fake_phase3)
    # Phase 2 also runs before 3 on non-done state; shim it.
    monkeypatch.setattr(
        auto_cmd,
        "_phase2_task_loop",
        lambda ns, state, cfg: state,
    )

    with pytest.raises(MAGIGateError):
        auto_cmd.main(["--project-root", str(tmp_path)])

    audit_file = tmp_path / ".claude" / "auto-run.json"
    assert audit_file.exists()
    data = json.loads(audit_file.read_text("utf-8"))
    assert data["status"] == "magi_gate_blocked"
    assert data["accepted_conditions"] == 2
    assert data["rejected_conditions"] >= 0
    # Task 1 schema: verdict is str|None, not required at this path.
    # tasks_completed defaults to 0 when Phase 2 is shimmed.


def test_parse_condition_counts_from_gate_error_msg() -> None:
    # Helper that extracts N accepted / M rejected from the standard
    # MAGIGateError string format. Not public API — internal to auto_cmd.
    msg = (
        "MAGI iter 1 produced 2 accepted condition(s); "
        "apply them via `sbtdd close-phase` and re-run `sbtdd pre-merge`."
    )
    accepted, rejected = auto_cmd._parse_condition_counts_from_msg(msg)
    assert accepted == 2
    assert rejected == 0  # Rejected count is tracked separately; default 0.


def test_parse_condition_counts_from_strong_no_go_msg() -> None:
    # STRONG_NO_GO has no conditions in the msg shape. Must degrade to (0, 0).
    msg = "MAGI STRONG_NO_GO at iter 1"
    accepted, rejected = auto_cmd._parse_condition_counts_from_msg(msg)
    assert accepted == 0
    assert rejected == 0
```

- [ ] **Step 2: Run test** — expected FAIL (new helper does not exist yet).

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_auto_cmd_exit8.py
git commit -m "test: fail for exit-8 enriched audit with condition counts"
```

- [ ] **Step 4: Implement Green**

Add to `auto_cmd.py` (top-level helper near `_now_iso`):

```python
import re

_CONDITIONS_ACCEPTED_RE = re.compile(r"(\d+)\s+accepted\s+condition", re.IGNORECASE)
_CONDITIONS_REJECTED_RE = re.compile(r"(\d+)\s+rejected\s+condition", re.IGNORECASE)


def _parse_condition_counts_from_msg(msg: str) -> tuple[int, int]:
    """Extract (accepted, rejected) from a MAGIGateError message.

    ``pre_merge_cmd._loop2`` formats gate-block messages as ``"MAGI iter
    {N} produced {K} accepted condition(s); ..."`` — parse this to
    enrich the auto-run.json audit with counts. STRONG_NO_GO messages
    carry no counts; both return 0.

    Args:
        msg: Exception message from :class:`MAGIGateError`.

    Returns:
        ``(accepted, rejected)`` counts; ``(0, 0)`` when no match.
    """
    accepted_m = _CONDITIONS_ACCEPTED_RE.search(msg)
    rejected_m = _CONDITIONS_REJECTED_RE.search(msg)
    accepted = int(accepted_m.group(1)) if accepted_m else 0
    rejected = int(rejected_m.group(1)) if rejected_m else 0
    return (accepted, rejected)
```

Modify the `MAGIGateError` except-clause in `main` to build an `AutoRunAudit` with the extracted counts:

```python
    except MAGIGateError as exc:
        accepted, rejected = _parse_condition_counts_from_msg(str(exc))
        audit = AutoRunAudit(
            schema_version=_AUTO_RUN_SCHEMA_VERSION,
            auto_started_at=started,
            auto_finished_at=_now_iso(),
            status="magi_gate_blocked",
            verdict=None,
            degraded=None,
            accepted_conditions=accepted,
            rejected_conditions=rejected,
            tasks_completed=getattr(state, "_tasks_completed_count", 0),
            error=str(exc),
        )
        _write_auto_run_audit(auto_run, audit)
        sys.stderr.write(
            f"/sbtdd auto: MAGI gate blocked "
            f"(accepted={accepted}, rejected={rejected}). See "
            f"{auto_run} and .claude/magi-conditions.md for next steps.\n"
        )
        raise
```

`state._tasks_completed_count` is a best-effort field added by `_phase2_task_loop` (extend it to track the count); if the shim fixture skips Phase 2, `getattr` defaults to 0.

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/auto_cmd.py
git commit -m "feat: enrich exit-8 audit in auto_cmd with condition counts"
```

---

## Phase 2: Dependency + reporter hardening (Tasks 5-8 — scope items 4, 5, 6, 7)

Tasks independientes. Cada uno es un mini-ciclo TDD aislado sobre un modulo A/B. Orden arbitrario; se listan como 5, 6, 7, 8 para referencia.

### Task 5: Python version floor enforcement (scope item 5)

**Files:**
- Modify: `skills/sbtdd/scripts/dependency_check.py`
- Create: `tests/test_dependency_check_python_floor.py`

`check_python()` ya compara `sys.version_info >= (3, 9)` — eso funciona para el proceso **actual**. Pero init corre bajo Python 3.9+ (cumplido por `~/.claude/plugins/` dispatching); sin embargo, si un usuario invoca el plugin con un `python3` externo (p.ej. para subshells), el check debe tambien parsear `python --version` de un binario externo.

La idea del hardening: anadir `_check_python_binary()` que corre `python --version`, parsea y valida >= 3.9 (ademas del check de `sys.version_info`). Se integra en `check_environment`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_dependency_check_python_floor.py
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import dependency_check
import subprocess_utils


def test_check_python_binary_accepts_3_9(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="Python 3.9.18\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_python_binary()
    assert result.status == "OK"


def test_check_python_binary_accepts_3_12(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="Python 3.12.3\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_python_binary()
    assert result.status == "OK"
    assert "3.12.3" in result.detail


def test_check_python_binary_rejects_3_8(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="Python 3.8.19\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_python_binary()
    assert result.status == "BROKEN"
    assert "3.8.19" in result.detail
    assert "3.9" in (result.remediation or "")


def test_check_python_binary_rejects_2_7(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="Python 2.7.18\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_python_binary()
    assert result.status == "BROKEN"


def test_check_python_binary_rejects_unparseable_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="Python\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_python_binary()
    assert result.status == "BROKEN"
    assert "parse" in result.detail.lower() or "unknown" in result.detail.lower()


def test_check_python_binary_handles_missing_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    result = dependency_check._check_python_binary()
    assert result.status == "MISSING"
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — `AttributeError: module 'dependency_check' has no attribute '_check_python_binary'`.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_dependency_check_python_floor.py
git commit -m "test: fail for python-binary version floor check"
```

- [ ] **Step 4: Implement Green**

Add to `dependency_check.py` after `check_python`:

```python
import re as _re

_PYTHON_VERSION_RE = _re.compile(r"^Python\s+(\d+)\.(\d+)(?:\.(\d+))?")


def _check_python_binary() -> DependencyCheck:
    """Verify ``python --version`` parses to >= 3.9 (INV-19 hardening).

    Complements :func:`check_python` which asserts
    ``sys.version_info >= (3, 9)``. This check runs the ``python``
    binary found on PATH and parses its reported version; it catches
    the case where the plugin process runs under a 3.9+ interpreter
    but the ``python`` on PATH (used to spawn subshells / reporter
    pipelines) is stale.
    """
    binary = shutil.which("python")
    if binary is None:
        return DependencyCheck(
            name="python binary",
            status="MISSING",
            detail="`python` not found on PATH",
            remediation="Install Python 3.9+ and ensure `python` is on PATH",
        )
    try:
        result = subprocess_utils.run_with_timeout(
            ["python", "--version"], timeout=5
        )
    except subprocess.TimeoutExpired:
        return DependencyCheck(
            name="python binary",
            status="BROKEN",
            detail="`python --version` timed out",
            remediation="Reinstall Python 3.9+",
        )
    output = (result.stdout + result.stderr).strip()
    m = _PYTHON_VERSION_RE.match(output)
    if not m:
        return DependencyCheck(
            name="python binary",
            status="BROKEN",
            detail=f"Cannot parse python --version output: {output!r}",
            remediation="Reinstall Python 3.9+",
        )
    major, minor = int(m.group(1)), int(m.group(2))
    version_str = f"{major}.{minor}" + (f".{m.group(3)}" if m.group(3) else "")
    if (major, minor) < (3, 9):
        return DependencyCheck(
            name="python binary",
            status="BROKEN",
            detail=f"python binary reports {version_str}, < 3.9 required",
            remediation="Install Python 3.9+ and ensure `python` is on PATH",
        )
    return DependencyCheck(
        name="python binary",
        status="OK",
        detail=f"python {version_str}",
        remediation=None,
    )
```

Wire `_check_python_binary()` into `check_environment` right after `check_python()`:

```python
    checks.append(check_python())
    checks.append(_check_python_binary())  # Floor-enforcement hardening
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/dependency_check.py
git commit -m "fix: enforce python binary version floor via regex parse"
```

---

### Task 6: cargo-clippy / cargo-fmt version-format validation (scope item 4)

**Files:**
- Modify: `skills/sbtdd/scripts/dependency_check.py`
- Create: `tests/test_dependency_check_rust_versions.py`

Objetivo: el check actual `_check_binary` asserts `returncode == 0`. Un shim roto podria imprimir `"clippy 0.1.0-nightly"` sin fallar exit code. Tomamos stdout, parseamos con regex `^(clippy|rustfmt|cargo-\w+)\s+\d+\.\d+`. Si no hace match, marcar BROKEN.

Solo aplica a `cargo-clippy` / `cargo-fmt` / `cargo-nextest` / `cargo-audit`: binarios rust con formato conocido. `cargo` mismo pasa el check plano.

- [ ] **Step 1: Write failing test**

```python
# tests/test_dependency_check_rust_versions.py
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import dependency_check
import subprocess_utils


_OK_CLIPPY = "clippy 0.1.79 (bbdc35d 2024-05-15)\n"
_OK_FMT = "rustfmt 1.7.0-stable (129f3b99 2024-05-23)\n"
_OK_NEXTEST = "cargo-nextest-nextest 0.9.70\n"
_OK_AUDIT = "cargo-audit-audit 0.20.0\n"


def test_rust_shim_cargo_clippy_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_CLIPPY, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "OK"


def test_rust_shim_cargo_fmt_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_FMT, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-fmt", "rust (cargo-fmt)")
    assert result.status == "OK"


def test_rust_shim_broken_output_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        # A shim that returns exit 0 with garbage — must still reject.
        return SimpleNamespace(returncode=0, stdout="banana\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "BROKEN"
    assert "unexpected" in result.detail.lower() or "parse" in result.detail.lower()


def test_rust_shim_cargo_nextest_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_NEXTEST, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary(
        "cargo-nextest", "rust (cargo-nextest)"
    )
    assert result.status == "OK"


def test_non_rust_binary_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regression: git and other non-rust binaries must not be gated by
    # the rust version regex. Stdout can be anything as long as exit 0.
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="git version 2.40.0\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("git", "git")
    assert result.status == "OK"
```

- [ ] **Step 2: Run test to verify it fails**

Expected: `test_rust_shim_broken_output_rejected` FAILS (current impl accepts any exit-0 shim); the other tests pass coincidentally.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_dependency_check_rust_versions.py
git commit -m "test: fail for rust shim version-format validation"
```

- [ ] **Step 4: Implement Green**

Add a version regex + targeted check in `dependency_check.py`:

```python
#: Per-binary expected output prefixes for Rust toolchain shims. When
#: the binary is on this list, ``_check_binary`` additionally asserts
#: stdout matches the corresponding regex — catches shims that return
#: exit 0 with garbage output (e.g. broken PATH entry shadowing a real
#: binary, or a placeholder script installed during incomplete setup).
_RUST_VERSION_REGEXES: Mapping[str, _re.Pattern[str]] = MappingProxyType(
    {
        "cargo-clippy": _re.compile(r"^clippy\s+\d+\.\d+"),
        "cargo-fmt": _re.compile(r"^rustfmt\s+\d+\.\d+"),
        "cargo-nextest": _re.compile(r"^cargo-nextest[-\w]*\s+\d+\.\d+"),
        "cargo-audit": _re.compile(r"^cargo-audit[-\w]*\s+\d+\.\d+"),
    }
)
```

Inside `_check_binary`, right after the `combined = (result.stdout or result.stderr).strip()` line and before the existing OK return, add:

```python
    expected_re = _RUST_VERSION_REGEXES.get(binary)
    if expected_re is not None and not expected_re.match(combined):
        return DependencyCheck(
            name=display,
            status="BROKEN",
            detail=(
                f"{label} --version output did not match expected format: "
                f"{combined.splitlines()[0] if combined else '(empty)'}"
            ),
            remediation=f"Reinstall {binary} (its `--version` output looks malformed)",
        )
```

Add the `import re as _re` + MappingProxyType/Mapping imports if not already present (MappingProxyType is already imported from Milestone B).

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/dependency_check.py
git commit -m "fix: validate rust shim --version output format"
```

---

### Task 7: rust_reporter NEXTEST_EXPERIMENTAL_LIBTEST_JSON env var detection (scope item 6)

**Files:**
- Modify: `skills/sbtdd/scripts/reporters/rust_reporter.py`
- Create: `tests/test_rust_reporter_nextest_env.py`

`--message-format libtest-json-plus` requires `NEXTEST_EXPERIMENTAL_LIBTEST_JSON=1`. Sin el env var, nextest emite "unknown format" y el pipeline falla silenciosamente (reporter trata el stream como json y falla al parsear). Detectar proactivamente y raise con remediation.

- [ ] **Step 1: Write failing test**

```python
# tests/test_rust_reporter_nextest_env.py
from __future__ import annotations

import os
from typing import Any

import pytest

from errors import ValidationError
from reporters import rust_reporter


def test_ensure_env_var_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXTEST_EXPERIMENTAL_LIBTEST_JSON", raising=False)
    with pytest.raises(ValidationError) as exc:
        rust_reporter.ensure_nextest_experimental_env()
    assert "NEXTEST_EXPERIMENTAL_LIBTEST_JSON" in str(exc.value)
    assert "1" in str(exc.value)


def test_ensure_env_var_raises_when_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXTEST_EXPERIMENTAL_LIBTEST_JSON", "0")
    with pytest.raises(ValidationError):
        rust_reporter.ensure_nextest_experimental_env()


def test_ensure_env_var_accepts_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXTEST_EXPERIMENTAL_LIBTEST_JSON", "1")
    rust_reporter.ensure_nextest_experimental_env()  # No raise.


def test_run_pipeline_checks_env_before_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEXTEST_EXPERIMENTAL_LIBTEST_JSON", raising=False)

    calls: list[Any] = []

    class _FakePopen:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            calls.append((args, kwargs))
            raise AssertionError("Popen called before env var check")

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    with pytest.raises(ValidationError):
        rust_reporter.run_pipeline()
    assert calls == []


def test_run_pipeline_opts_out_via_keyword(monkeypatch: pytest.MonkeyPatch) -> None:
    # Escape valve for tests: `check_env=False` skips the assertion.
    monkeypatch.delenv("NEXTEST_EXPERIMENTAL_LIBTEST_JSON", raising=False)
    calls: list[Any] = []

    class _FakePopen:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            calls.append((args, kwargs))
            self.stdout = None
            self.returncode = 0

        def communicate(self, timeout: Any = None) -> tuple[bytes, bytes]:
            return (b"", b"")

        def wait(self, timeout: Any = None) -> int:
            return 0

    import subprocess

    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    rc = rust_reporter.run_pipeline(check_env=False)
    assert rc == 0
    assert len(calls) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — `AttributeError: module has no attribute 'ensure_nextest_experimental_env'` and `run_pipeline` does not accept `check_env`.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_rust_reporter_nextest_env.py
git commit -m "test: fail for nextest experimental env var detection"
```

- [ ] **Step 4: Implement Green**

Modify `reporters/rust_reporter.py`. Add import at top:

```python
import os
from errors import ValidationError
```

Add constant:

```python
_NEXTEST_ENV_VAR: str = "NEXTEST_EXPERIMENTAL_LIBTEST_JSON"
```

Add function before `run_pipeline`:

```python
def ensure_nextest_experimental_env() -> None:
    """Raise :class:`ValidationError` unless the nextest env flag is set.

    ``cargo nextest run --message-format libtest-json-plus`` requires
    ``NEXTEST_EXPERIMENTAL_LIBTEST_JSON=1``. Without this env var, nextest
    silently emits a different (free-form) stream that ``tdd-guard-rust``
    cannot parse, resulting in confusing "unknown format" downstream
    errors. We fail loud up-front with an actionable remediation.

    Raises:
        ValidationError: Env var missing or set to something other than
            the literal string ``"1"``.
    """
    value = os.environ.get(_NEXTEST_ENV_VAR)
    if value != "1":
        raise ValidationError(
            f"{_NEXTEST_ENV_VAR} must be set to '1' for libtest-json-plus "
            f"output. Current value: {value!r}. "
            f"Export it before invoking `cargo nextest run` under SBTDD: "
            f"`{_NEXTEST_ENV_VAR}=1 sbtdd close-phase`."
        )
```

Modify `run_pipeline` signature:

```python
def run_pipeline(
    cwd: str | None = None,
    nextest_cmd: Iterable[str] = _NEXTEST_CMD,
    reporter_cmd: Iterable[str] = _TDD_GUARD_RUST_CMD,
    timeout: int = _DEFAULT_TIMEOUT_SEC,
    *,
    check_env: bool = True,
) -> int:
```

At the top of `run_pipeline` body:

```python
    if check_env:
        ensure_nextest_experimental_env()
```

Update the docstring to cover `check_env`.

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/reporters/rust_reporter.py
git commit -m "fix: detect NEXTEST_EXPERIMENTAL_LIBTEST_JSON env var before pipeline"
```

---

### Task 8: ctest_reporter empty JUnit XML handling (scope item 7)

**Files:**
- Modify: `skills/sbtdd/scripts/reporters/ctest_reporter.py`
- Create: `tests/test_ctest_reporter_empty_xml.py`

`parse_junit` actualmente catchea `ET.ParseError` y lo traduce a `ValidationError`. Pero `ET.parse` sobre archivo de 0 bytes raisea `ET.ParseError: no element found` — el catch ya existe, lo cual es bueno. El hardening: mensaje enriquecido que indique explicitamente `"file is empty (0 bytes)"`, + test regresion sobre la fixture.

- [ ] **Step 1: Write failing test**

```python
# tests/test_ctest_reporter_empty_xml.py
from __future__ import annotations

from pathlib import Path

import pytest

from errors import ValidationError
from reporters import ctest_reporter


_EMPTY_FIXTURE = Path("tests/fixtures/junit-xml/empty.xml")
_MALFORMED_FIXTURE = Path("tests/fixtures/junit-xml/malformed.xml")


def test_parse_junit_on_empty_file_raises_validation_error(tmp_path: Path) -> None:
    # Use the fixture directly — 0-byte file.
    with pytest.raises(ValidationError) as exc:
        ctest_reporter.parse_junit(_EMPTY_FIXTURE)
    # Message must make it obvious the file was empty, not generically
    # "malformed".
    assert "empty" in str(exc.value).lower() or "0 bytes" in str(exc.value)


def test_parse_junit_on_malformed_file_raises_validation_error() -> None:
    with pytest.raises(ValidationError) as exc:
        ctest_reporter.parse_junit(_MALFORMED_FIXTURE)
    # Malformed is distinguishable from empty — we want the caller to
    # see a different reason.
    assert "empty" not in str(exc.value).lower()
    assert "invalid" in str(exc.value).lower() or "parse" in str(exc.value).lower()


def test_parse_junit_on_nonexistent_file_raises_validation_error(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "nope.xml"
    with pytest.raises(ValidationError) as exc:
        ctest_reporter.parse_junit(missing)
    assert "not found" in str(exc.value).lower() or "does not exist" in str(
        exc.value
    ).lower()


def test_run_wraps_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "test.json"
    with pytest.raises(ValidationError):
        ctest_reporter.run(_EMPTY_FIXTURE, target)
    assert not target.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Expected: the `empty.xml` test FAILS because the current error message says `"invalid JUnit XML in ..."` — generic, not empty-specific. The other two tests (malformed, nonexistent) already pass coincidentally.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_ctest_reporter_empty_xml.py
git commit -m "test: fail for empty-junit-xml distinguishable error"
```

- [ ] **Step 4: Implement Green**

Modify `parse_junit` in `reporters/ctest_reporter.py`. Before the `ET.parse` call, add:

```python
    if path.stat().st_size == 0:
        raise ValidationError(
            f"JUnit XML file is empty (0 bytes): {path}. "
            f"Ensure `ctest --output-junit` ran successfully before invoking "
            f"the reporter."
        )
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/reporters/ctest_reporter.py
git commit -m "fix: handle 0-byte ctest junit XML with specific error"
```

---

## Phase 3: Resume hardening + exit 8 UX (Tasks 9-13 — scope items 8, 9, 10, 11, 12)

Tasks 9-11 modifican `resume_cmd`. Task 12 modifica `pre_merge_cmd`. Task 13 es un integration test que ata Tasks 11 + 12 (auto → exit 8 → resume detects → prompts conditions flow).

### Task 9: Resume mid-pre-merge conditions-pending detection (scope item 8)

**Files:**
- Modify: `skills/sbtdd/scripts/resume_cmd.py`
- Create: `tests/test_resume_cmd_magi_conditions.py`

Objetivo: cuando un usuario interrumpe mid-pre-merge despues de que `_loop2` escribio `.claude/magi-conditions.md` + raised exit 8, `resume` debe detectar este state y dirigir al usuario a `sbtdd close-phase` (aplicar conditions) — NO re-ejecutar `pre-merge` ciegamente.

Signal: `magi-conditions.md` presente en `.claude/` + state.current_phase == "done" + tree clean (o dirty con uncommitted fixes en progreso).

- [ ] **Step 1: Write failing test**

```python
# tests/test_resume_cmd_magi_conditions.py
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import resume_cmd


def _write_state(root: Path, phase: str) -> None:
    state_dir = root / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "session-state.json").write_text(
        json.dumps(
            {
                "plan_path": "planning/claude-plan-tdd.md",
                "current_task_id": None,
                "current_task_title": None,
                "current_phase": phase,
                "phase_started_at_commit": "abc1234",
                "last_verification_at": "2026-04-19T16:30:00Z",
                "last_verification_result": "passed",
                "plan_approved_at": "2026-04-19T10:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def test_decide_delegation_with_magi_conditions_pending(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path, "done")
    (tmp_path / ".claude" / "magi-conditions.md").write_text(
        "# MAGI conditions iter 1\n\n- Apply refactor X\n", encoding="utf-8"
    )
    state = SimpleNamespace(current_phase="done")
    runtime = {
        "auto-run.json": True,
        "magi-verdict.json": False,
        "magi-conditions.md": True,
    }
    module_name, extra = resume_cmd._decide_delegation(
        state, tree_dirty=False, runtime=runtime
    )
    assert module_name == "magi-conditions-pending"
    assert extra == []


def test_resume_stdout_when_conditions_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_state(tmp_path, "done")
    (tmp_path / ".claude" / "plugin.local.md").write_text(
        "---\nstack: python\n---\n", encoding="utf-8"
    )
    (tmp_path / ".claude" / "magi-conditions.md").write_text(
        "# MAGI conditions iter 1\n\n- Apply refactor X\n", encoding="utf-8"
    )
    # Shim subprocess so diagnostic / environment checks pass.
    monkeypatch.setattr(
        resume_cmd, "_recheck_environment", lambda root: None
    )
    monkeypatch.setattr(
        resume_cmd,
        "_report_diagnostic",
        lambda root: {
            "state": SimpleNamespace(current_phase="done"),
            "head_sha": "abc1234",
            "tree_dirty": False,
            "runtime": {
                "auto-run.json": True,
                "magi-verdict.json": False,
                "magi-conditions.md": True,
            },
        },
    )
    rc = resume_cmd.main(["--project-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "magi-conditions.md" in captured.out
    assert "sbtdd close-phase" in captured.out


def test_diagnostic_snapshot_includes_magi_conditions_md(tmp_path: Path) -> None:
    _write_state(tmp_path, "done")
    (tmp_path / ".claude" / "magi-conditions.md").write_text(
        "# MAGI conditions iter 1\n", encoding="utf-8"
    )
    # Initialise git so diagnostic runs.
    import subprocess

    subprocess.run(
        ["git", "init", "--initial-branch", "main"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    report = resume_cmd._report_diagnostic(tmp_path)
    assert report["runtime"].get("magi-conditions.md") is True
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL. `_decide_delegation` currently returns `("auto_cmd", [])` for `phase=done + auto-run.json=True`; doesn't consider `magi-conditions.md`. Also `_report_diagnostic` doesn't include `magi-conditions.md` in its `runtime` dict.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_resume_cmd_magi_conditions.py
git commit -m "test: fail for resume detection of magi-conditions.md pending"
```

- [ ] **Step 4: Implement Green**

Modify `resume_cmd._report_diagnostic`. Extend the `runtime` dict:

```python
    runtime = {
        "magi-verdict.json": (root / ".claude" / "magi-verdict.json").exists(),
        "auto-run.json": (root / ".claude" / "auto-run.json").exists(),
        "magi-conditions.md": (root / ".claude" / "magi-conditions.md").exists(),
    }
```

Update the stdout loop to print the new key (no change needed — the loop iterates `runtime.items()`).

Modify `_decide_delegation`. Before the existing `phase == "done"` branches, add:

```python
    # Scope item 8: mid-pre-merge interruption leaves magi-conditions.md
    # behind. Surface to the user before any delegation — running
    # `sbtdd pre-merge` again without applying conditions just produces
    # the same gate block.
    if runtime.get("magi-conditions.md"):
        return ("magi-conditions-pending", [])
```

Modify `main` to handle the new sentinel. After `module_name, extra = _decide_delegation(...)`:

```python
    if module_name == "magi-conditions-pending":
        sys.stdout.write(
            "\nPending MAGI conditions detected in .claude/magi-conditions.md.\n"
            "The previous `sbtdd pre-merge` produced accepted conditions that\n"
            "have not been applied yet. Next step:\n"
            "  1. Read .claude/magi-conditions.md.\n"
            "  2. For each condition, run `sbtdd close-phase` with a TDD\n"
            "     mini-cycle that addresses it.\n"
            "  3. Re-run `sbtdd pre-merge` once all conditions are applied.\n"
        )
        return 0
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/resume_cmd.py
git commit -m "feat: detect pending magi-conditions.md on resume"
```

---

### Task 10: Resume with concurrent state file writes (scope item 9)

**Files:**
- Modify: `skills/sbtdd/scripts/resume_cmd.py`
- Create: `tests/test_resume_cmd_concurrent_state.py`

Objetivo: si otra sesion (u otra shell corriendo `sbtdd status`) modifica `session-state.json` mientras `resume` lee, debe fallar loud con `StateFileError`, NO retornar datos inconsistentes silenciosamente. Simulamos con monkeypatch que muta el archivo entre las dos reads implicitas de resume (diagnostic + recheck).

Implementacion: en `_recheck_environment`, leer el archivo dos veces consecutivas (una en diagnostic, otra en recheck) y, si el mtime cambio, raise `StateFileError`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_resume_cmd_concurrent_state.py
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import resume_cmd
from errors import StateFileError


def _write_state(root: Path, phase: str) -> None:
    state_dir = root / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "session-state.json").write_text(
        json.dumps(
            {
                "plan_path": "planning/claude-plan-tdd.md",
                "current_task_id": "1",
                "current_task_title": "T1",
                "current_phase": phase,
                "phase_started_at_commit": "abc1234",
                "last_verification_at": None,
                "last_verification_result": None,
                "plan_approved_at": "2026-04-19T10:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def test_concurrent_state_write_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / ".claude" / "session-state.json"
    _write_state(tmp_path, "red")
    (tmp_path / ".claude" / "plugin.local.md").write_text(
        "---\nstack: python\n---\n", encoding="utf-8"
    )

    # Simulate concurrent rewrite between the two snapshots. We install
    # a shim on `load_state` that on second call overwrites the file.
    original_load = resume_cmd.load_state
    call_count = {"n": 0}

    def racey_load(path: Path) -> Any:
        call_count["n"] += 1
        if call_count["n"] == 2:
            # Rewrite between reads so the mtime check trips.
            time.sleep(0.02)
            state_path.write_text(
                state_path.read_text("utf-8").replace("red", "green"),
                encoding="utf-8",
            )
        return original_load(path)

    monkeypatch.setattr(resume_cmd, "load_state", racey_load)

    with pytest.raises(StateFileError) as exc:
        resume_cmd._assert_state_stable_between_reads(state_path)
    assert "concurrent" in str(exc.value).lower() or "mtime" in str(exc.value).lower()


def test_stable_state_does_not_raise(tmp_path: Path) -> None:
    state_path = tmp_path / ".claude" / "session-state.json"
    _write_state(tmp_path, "red")
    # Two reads in sequence without concurrent mutation — must not raise.
    resume_cmd._assert_state_stable_between_reads(state_path)
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — `_assert_state_stable_between_reads` does not exist.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_resume_cmd_concurrent_state.py
git commit -m "test: fail for resume concurrent state-file write detection"
```

- [ ] **Step 4: Implement Green**

Add to `resume_cmd.py`:

```python
from errors import StateFileError


def _assert_state_stable_between_reads(state_path: Path) -> None:
    """Guard against concurrent modification of the state file.

    Reads the file's mtime + content once, waits briefly, then re-reads.
    If either differs, raises :class:`StateFileError`. Intended to be
    called at the start of ``_recheck_environment`` so delegations
    downstream operate on a consistent snapshot (INV-17 spirit: drift
    surfaced, never silenced).
    """
    if not state_path.exists():
        return
    first_mtime = state_path.stat().st_mtime_ns
    first_content = state_path.read_bytes()
    # Very small sleep enough to catch racing writers in tests and in
    # practice; smaller than any human interaction latency.
    _time.sleep(0.01)
    second_mtime = state_path.stat().st_mtime_ns
    second_content = state_path.read_bytes()
    if first_mtime != second_mtime or first_content != second_content:
        raise StateFileError(
            f"concurrent modification detected on {state_path} "
            f"(mtime or content changed between reads). "
            f"Abort to avoid acting on stale state; re-run /sbtdd resume "
            f"once writers have stopped."
        )
```

Import `import time as _time` at top of file.

Wire into `_recheck_environment`:

```python
def _recheck_environment(root: Path) -> None:
    ...
    state_path = root / ".claude" / "session-state.json"
    _assert_state_stable_between_reads(state_path)
    ...
```

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/resume_cmd.py
git commit -m "fix: detect concurrent state-file writes in resume"
```

---

### Task 11: Resume --dry-run end-to-end integration test (scope item 10)

**Files:**
- Create: `tests/test_resume_cmd_dry_run_integration.py`

Objetivo: full end-to-end test donde se prepara un estado sintetico de auto interrumpido (state file con `current_phase="green"`, auto-run.json presente, sin magi-verdict, arbol dirty) y se invoca `resume --dry-run`. Assertion: zero side effects (no files created / modified / deleted) y stdout contiene la delegacion esperada (`auto_cmd`).

- [ ] **Step 1: Write test**

```python
# tests/test_resume_cmd_dry_run_integration.py
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import resume_cmd


def _snapshot_dir(root: Path) -> dict[str, str]:
    """Return {relpath: sha256} for every file under root."""
    result: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            result[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


@pytest.fixture()
def interrupted_auto_project(tmp_path: Path) -> Path:
    subprocess.run(
        ["git", "init", "--initial-branch", "main"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t.io", "-c", "user.name=t",
         "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "plugin.local.md").write_text(
        "---\nstack: python\n---\n", encoding="utf-8"
    )
    (tmp_path / ".claude" / "session-state.json").write_text(
        json.dumps(
            {
                "plan_path": "planning/claude-plan-tdd.md",
                "current_task_id": "2",
                "current_task_title": "T2",
                "current_phase": "green",
                "phase_started_at_commit": "abc1234",
                "last_verification_at": "2026-04-19T16:30:00Z",
                "last_verification_result": "passed",
                "plan_approved_at": "2026-04-19T10:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".claude" / "auto-run.json").write_text(
        json.dumps({"auto_started_at": "2026-04-19T10:00:00Z"}),
        encoding="utf-8",
    )
    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "claude-plan-tdd.md").write_text(
        "### Task 1: first\n- [x] step\n\n### Task 2: second\n- [ ] step\n",
        encoding="utf-8",
    )
    # Dirty tree: create an untracked file.
    (tmp_path / "scratch.txt").write_text("wip\n", encoding="utf-8")
    return tmp_path


def test_dry_run_has_zero_side_effects(
    interrupted_auto_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = interrupted_auto_project
    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)
    pre = _snapshot_dir(root)
    rc = resume_cmd.main(["--project-root", str(root), "--dry-run"])
    post = _snapshot_dir(root)
    assert rc == 0
    assert pre == post, f"dry-run mutated filesystem: {set(pre) ^ set(post)}"


def test_dry_run_prints_delegation_target(
    interrupted_auto_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)
    resume_cmd.main(
        ["--project-root", str(interrupted_auto_project), "--dry-run"]
    )
    captured = capsys.readouterr()
    # With phase=green + tree_dirty=True, decision tree returns
    # uncommitted-resolution. --dry-run prints "Would delegate to:
    # uncommitted-resolution" and returns without acting.
    assert "uncommitted-resolution" in captured.out or "CONTINUE" in captured.out


def test_dry_run_clean_tree_delegates_to_auto(
    interrupted_auto_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Remove the scratch.txt to make tree clean.
    (interrupted_auto_project / "scratch.txt").unlink()
    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)
    rc = resume_cmd.main(
        ["--project-root", str(interrupted_auto_project), "--dry-run"]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "auto_cmd" in captured.out
    assert "Would delegate" in captured.out
```

- [ ] **Step 2: Run test**

Tests depend on Task 9 + 10 being in. If `_recheck_environment` fails locally (missing pytest/ruff/mypy on PATH), the monkeypatch stubs it. Run:

```bash
python -m pytest tests/test_resume_cmd_dry_run_integration.py -v
```

Expected: 3 green.

- [ ] **Step 3: Commit**

```bash
git add tests/test_resume_cmd_dry_run_integration.py
git commit -m "test: pin resume --dry-run end-to-end zero-side-effects"
```

---

### Task 12: pre_merge_cmd exit 8 stderr summary (scope item 11)

**Files:**
- Modify: `skills/sbtdd/scripts/pre_merge_cmd.py`
- Create: `tests/test_pre_merge_cmd_exit8.py`

Objetivo: cuando `_loop2` escribe `.claude/magi-conditions.md` y raisea `MAGIGateError`, imprimir tambien a stderr una linea concisa de resumen con `N accepted + M rejected` + next-step hint. Hoy el mensaje de la excepcion menciona solo accepted count.

- [ ] **Step 1: Write failing test**

```python
# tests/test_pre_merge_cmd_exit8.py
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import pre_merge_cmd
from errors import MAGIGateError


class _FakeVerdict:
    conditions = ("Refactor X", "Rename Y")
    verdict = "GO_WITH_CAVEATS"
    degraded = False


def _make_cfg() -> Any:
    return type(
        "Cfg",
        (),
        {
            "plan_path": "planning/claude-plan-tdd.md",
            "magi_threshold": "GO_WITH_CAVEATS",
            "magi_max_iterations": 3,
        },
    )()


def test_loop2_writes_conditions_and_emits_stderr_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = _make_cfg()
    root = tmp_path
    (root / ".claude").mkdir()
    (root / "planning").mkdir()
    (root / "planning" / "claude-plan-tdd.md").write_text("### Task 1:\n- [x]\n")

    # magi returns verdict with conditions; receiving-review accepts 2, rejects 0.
    monkeypatch.setattr(
        pre_merge_cmd.magi_dispatch, "invoke_magi",
        lambda context_paths, cwd: _FakeVerdict(),
    )
    monkeypatch.setattr(
        pre_merge_cmd.magi_dispatch, "verdict_is_strong_no_go", lambda v: False
    )
    monkeypatch.setattr(
        pre_merge_cmd.superpowers_dispatch, "receiving_code_review",
        lambda args, cwd: {"accepted": list(_FakeVerdict.conditions), "rejected": []},
    )
    monkeypatch.setattr(
        pre_merge_cmd, "_parse_receiving_review",
        lambda r: (list(_FakeVerdict.conditions), []),
    )
    monkeypatch.setattr(
        pre_merge_cmd, "_conditions_to_skill_args", lambda cs: list(cs),
    )

    with pytest.raises(MAGIGateError):
        pre_merge_cmd._loop2(root, cfg, threshold_override=None)
    captured = capsys.readouterr()
    # magi-conditions.md written
    assert (root / ".claude" / "magi-conditions.md").exists()
    # Stderr summary
    assert "accepted=2" in captured.err or "2 accepted" in captured.err
    assert "rejected=0" in captured.err or "0 rejected" in captured.err
    assert "magi-conditions.md" in captured.err
    assert "close-phase" in captured.err
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — nothing currently writes to stderr in the exit-8 branch.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_pre_merge_cmd_exit8.py
git commit -m "test: fail for pre_merge exit-8 stderr summary"
```

- [ ] **Step 4: Implement Green**

Modify `pre_merge_cmd._loop2`. In the `if accepted:` branch, after `conditions_path = _write_magi_conditions_file(...)` and before `raise MAGIGateError(...)`, add:

```python
                sys.stderr.write(
                    f"pre-merge exit 8: accepted={len(accepted)}, "
                    f"rejected={len(rejected)}. Applied conditions not yet "
                    f"in diff. See {conditions_path} and run `sbtdd close-phase` "
                    f"for each, then re-run `sbtdd pre-merge`.\n"
                )
```

Ensure `import sys` is at top of file (already present in pre_merge_cmd).

- [ ] **Step 5: Run test to verify it passes**

- [ ] **Step 6: Commit Green**

```bash
git add skills/sbtdd/scripts/pre_merge_cmd.py
git commit -m "feat: emit stderr summary on pre-merge exit 8"
```

---

### Task 13: Cross-subcommand exit 8 integration test

**Files:**
- Create: `tests/test_pre_merge_resume_integration.py`

Objetivo: pin the happy-path user journey across `pre-merge` (produces exit 8 + conditions file) and `resume` (detects and instructs). Test is fully self-contained with monkeypatched skill invocations.

- [ ] **Step 1: Write test**

```python
# tests/test_pre_merge_resume_integration.py
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

import pre_merge_cmd
import resume_cmd
from errors import MAGIGateError


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    subprocess.run(
        ["git", "init", "--initial-branch", "main"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t.io", "-c", "user.name=t",
         "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "plugin.local.md").write_text(
        "---\nstack: python\nmagi_threshold: GO_WITH_CAVEATS\n"
        "magi_max_iterations: 3\nplan_path: planning/claude-plan-tdd.md\n---\n",
    )
    (tmp_path / "planning").mkdir()
    (tmp_path / "planning" / "claude-plan-tdd.md").write_text(
        "### Task 1:\n- [x]\n"
    )
    (tmp_path / ".claude" / "session-state.json").write_text(
        json.dumps(
            {
                "plan_path": "planning/claude-plan-tdd.md",
                "current_task_id": None,
                "current_task_title": None,
                "current_phase": "done",
                "phase_started_at_commit": "abc1234",
                "last_verification_at": "2026-04-19T16:30:00Z",
                "last_verification_result": "passed",
                "plan_approved_at": "2026-04-19T10:00:00Z",
            }
        )
    )
    return tmp_path


def test_pre_merge_exit8_then_resume_directs_to_close_phase(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Step 1: pre-merge hits exit 8 → writes magi-conditions.md.
    monkeypatch.setattr(pre_merge_cmd, "_loop1", lambda root: None)
    monkeypatch.setattr(pre_merge_cmd, "_preflight", lambda root: None)

    class V:
        conditions = ("Refactor X",)
        verdict = "GO_WITH_CAVEATS"
        degraded = False

    monkeypatch.setattr(
        pre_merge_cmd.magi_dispatch, "invoke_magi",
        lambda context_paths, cwd: V(),
    )
    monkeypatch.setattr(
        pre_merge_cmd.magi_dispatch, "verdict_is_strong_no_go", lambda v: False
    )
    monkeypatch.setattr(
        pre_merge_cmd, "_parse_receiving_review",
        lambda r: (["Refactor X"], []),
    )
    monkeypatch.setattr(
        pre_merge_cmd.superpowers_dispatch, "receiving_code_review",
        lambda args, cwd: {},
    )
    monkeypatch.setattr(
        pre_merge_cmd, "_conditions_to_skill_args", lambda cs: list(cs),
    )
    with pytest.raises(MAGIGateError):
        pre_merge_cmd.main(["--project-root", str(project)])
    assert (project / ".claude" / "magi-conditions.md").exists()

    # Step 2: resume detects magi-conditions.md → exit 0 with instructions.
    monkeypatch.setattr(resume_cmd, "_recheck_environment", lambda root: None)
    rc = resume_cmd.main(["--project-root", str(project)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "magi-conditions.md" in captured.out
    assert "close-phase" in captured.out
```

- [ ] **Step 2: Run test**

Expected: PASS (depends on Tasks 9 + 12 being green). Run:

```bash
python -m pytest tests/test_pre_merge_resume_integration.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_pre_merge_resume_integration.py
git commit -m "test: pin pre-merge exit-8 -> resume user journey"
```

---

## Phase 4: Documentation consolidation (Tasks 14-16 — scope items 13, 14, 15)

Pure docstring / comment updates. No new behavior. `docs:` commits.

### Task 14: auto_cmd INV-24 documentation

**Files:**
- Modify: `skills/sbtdd/scripts/auto_cmd.py`
- Modify: `skills/sbtdd/scripts/resume_cmd.py` (cross-reference)
- Create/append: `tests/test_inv_documentation.py` (shared with Tasks 15-16)

Objetivo: add a docstring cross-reference in `auto_cmd.py`'s module docstring (and in `_phase3_pre_merge` or equivalent verification-retry path) explaining CONTINUE default for uncommitted work lives in `resume_cmd._resolve_uncommitted` — not in `auto` itself. `auto` never leaves uncommitted work because each phase commits atomically; it's the `resume` path that honors INV-24 when the user restarts.

- [ ] **Step 1: Write failing test**

```python
# tests/test_inv_documentation.py
from __future__ import annotations

import inspect

import auto_cmd
import resume_cmd
import pre_merge_cmd
import init_cmd


def test_auto_cmd_docstring_references_inv24_semantics() -> None:
    doc = auto_cmd.__doc__ or ""
    assert "INV-24" in doc
    # Must explain that uncommitted-work CONTINUE default is in resume.
    assert "resume" in doc.lower() and "continue" in doc.lower()


def test_resume_resolve_uncommitted_docstring_mentions_inv24() -> None:
    doc = resume_cmd._resolve_uncommitted.__doc__ or ""
    assert "INV-24" in doc
    assert "CONTINUE" in doc


def test_pre_merge_loop2_docstring_mentions_inv29() -> None:
    doc = pre_merge_cmd._loop2.__doc__ or ""
    assert "INV-29" in doc
    assert (
        "feedback" in doc.lower()
        or "rejection" in doc.lower()
        or "rejected" in doc.lower()
    )


def test_init_cmd_mkdir_tracked_documents_toctou() -> None:
    doc = init_cmd._mkdir_tracked.__doc__ or ""
    # TOCTOU acknowledgement comment is acceptable inside docstring or
    # immediately below the function. Inspect source for the keyword.
    source = inspect.getsource(init_cmd._mkdir_tracked)
    assert "TOCTOU" in source or "race" in source.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — current `auto_cmd.__doc__` does not mention INV-24; `pre_merge_cmd._loop2.__doc__` does not mention INV-29 explicitly; `init_cmd._mkdir_tracked.__doc__` does not mention TOCTOU.

- [ ] **Step 3: Commit Red**

```bash
git add tests/test_inv_documentation.py
git commit -m "test: fail for INV-24 / INV-29 / TOCTOU docstring contract"
```

- [ ] **Step 4: Implement Green — auto_cmd INV-24 doc**

Append to the module docstring of `auto_cmd.py` (before the closing `"""`):

```
INV-24 (conservative defaults) does NOT apply inside ``auto`` itself —
auto commits atomically at every phase boundary, so no uncommitted work
is ever left behind mid-run. The CONTINUE-by-default contract for
uncommitted work lives in :mod:`resume_cmd` (see
``resume_cmd._resolve_uncommitted``) and engages only when the user
re-enters via ``/sbtdd resume`` after an externally-caused interruption
(crash, quota, Ctrl+C). This cross-reference exists to forestall the
common reader question "where is INV-24 enforced in auto?" — the answer
is "in resume; auto never needs it".
```

- [ ] **Step 5: Commit**

```bash
git add skills/sbtdd/scripts/auto_cmd.py
git commit -m "docs: document INV-24 cross-reference in auto_cmd"
```

---

### Task 15: pre_merge INV-29 docstring

**Files:**
- Modify: `skills/sbtdd/scripts/pre_merge_cmd.py`

Objetivo: docstring formalizing the feedback-loop contract (INV-29: rejected conditions feed next MAGI iteration context to break sterile loops).

- [ ] **Step 1: Reuse test from Task 14**

`test_pre_merge_loop2_docstring_mentions_inv29` is already in `test_inv_documentation.py`. After Task 14 commits the test, this task makes it green.

- [ ] **Step 2: Implement Green — pre_merge INV-29 doc**

Prepend a paragraph to the `_loop2` docstring in `pre_merge_cmd.py`:

```
**INV-29 contract (feedback loop).** Rejected MAGI conditions are not
silently discarded: every ``/receiving-code-review`` rejection is
appended to ``rejections`` and written as a feedback file that is
passed as an extra context path on the next MAGI iteration. This
breaks the "sterile loop" where MAGI keeps re-emitting the same
technically-wrong condition because it has no visibility into why the
previous iteration rejected it. The rationale is preserved across
iterations until the gate is passed or iterations are exhausted. See
:func:`_write_magi_feedback_file` for the on-disk format.
```

- [ ] **Step 3: Commit**

```bash
git add skills/sbtdd/scripts/pre_merge_cmd.py
git commit -m "docs: document INV-29 feedback-loop contract in pre_merge._loop2"
```

---

### Task 16: `_mkdir_tracked` TOCTOU comment

**Files:**
- Modify: `skills/sbtdd/scripts/init_cmd.py`

Objetivo: add an inline comment in `_mkdir_tracked` documenting the `os.rmdir`-based rollback contract and why the TOCTOU race between `_collect_created_dirs` and `path.mkdir(exist_ok=False)` is acceptable (init is single-user, window is microseconds, `mkdir(exist_ok=False)` raises FileExistsError loudly if another process created the dir concurrently, rollback sees `os.rmdir` fail on non-empty dirs which is the intended safety guard).

- [ ] **Step 1: Reuse test from Task 14**

`test_init_cmd_mkdir_tracked_documents_toctou` already exists.

- [ ] **Step 2: Implement Green — _mkdir_tracked TOCTOU comment**

Modify `_mkdir_tracked` in `init_cmd.py`:

```python
def _mkdir_tracked(directory: Path, dest_root: Path, created_dirs: list[Path]) -> None:
    """Create ``directory`` recording ancestors freshly made under dest_root.

    Acts like ``directory.mkdir(parents=True, exist_ok=True)`` but also
    appends to ``created_dirs`` every ancestor this call actually
    created. Ordering: parents-first (descendants after their parents),
    so the rollback handler can walk ``created_dirs`` in reverse and
    call ``os.rmdir`` leaf-to-root without violating the "only empty
    dirs can be removed" contract enforced by ``os.rmdir``.

    **Acceptable TOCTOU window.** Between ``_collect_created_dirs``
    (which reads the filesystem to decide which ancestors are missing)
    and ``path.mkdir(exist_ok=False)`` (which actually creates them)
    there is a race. In the single-user invocation pattern of
    ``/sbtdd init`` this window is ~microseconds and only matters when
    another process — typically an editor file watcher or a parallel
    shell — materializes an ancestor in the same instant. The
    ``exist_ok=False`` is deliberate: if a peer created the directory
    first, ``mkdir`` raises ``FileExistsError`` and the whole init
    rolls back loudly. ``os.rmdir`` in the rollback path refuses to
    remove non-empty dirs, so nothing a concurrent process placed
    inside the ancestor is ever deleted by this code. The tradeoff is
    acceptable because the alternative — an advisory file lock — costs
    complexity for a failure mode that is both rare and harmless
    (``init`` is idempotent and the user re-runs with ``--force``).
    """
    for path in _collect_created_dirs(directory, dest_root):
        path.mkdir(exist_ok=False)
        created_dirs.append(path)
```

- [ ] **Step 3: Commit**

```bash
git add skills/sbtdd/scripts/init_cmd.py
git commit -m "docs: document TOCTOU contract in init_cmd._mkdir_tracked"
```

---

## Phase 5: Milestone sweep (Task 17)

### Task 17: Milestone D acceptance sweep

**Files:** None modified.

- [ ] **Step 1: Run full test suite + time budget check**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: all Milestones A+B+C tests remain green; all Milestone D tests green. 0 failures.

On Windows (bash): `time python -m pytest tests/`. Target: `make verify` `<= 75 seconds` (raised from C's 60s; expected growth from +~30-40 tests). If exceeded, mark slowest 20% with `@pytest.mark.slow` and extend the Makefile split to `verify-all`.

- [ ] **Step 2: Run lint + format + types**

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy .
```

Expected: 0 warnings, clean format, 0 mypy errors (strict mode).

- [ ] **Step 3: Scope coverage audit**

Cross-check scope items 1-15 from this plan's Goal:

| Scope item | Covered by tasks |
|------------|------------------|
| 1 (AutoRunAudit schema) | 1 |
| 2 (INV-25 enforcement test) | 2 |
| 3 (INV-26 audit completeness) | 3 |
| 4 (cargo-clippy/fmt version regex) | 6 |
| 5 (Python version floor) | 5 |
| 6 (rust_reporter NEXTEST env var) | 7 |
| 7 (ctest_reporter empty XML) | 8 |
| 8 (resume mid-pre-merge conditions) | 9 + 13 |
| 9 (resume concurrent state writes) | 10 |
| 10 (resume --dry-run integration) | 11 |
| 11 (pre-merge exit 8 stderr) | 12 + 13 |
| 12 (auto exit 8 counts) | 4 |
| 13 (auto INV-24 docstring) | 14 |
| 14 (pre_merge INV-29 docstring) | 15 |
| 15 (_mkdir_tracked TOCTOU) | 16 |

- [ ] **Step 4: INV scan**

Grep for INV tokens added in this milestone:

- INV-24: `tests/test_inv_documentation.py::test_resume_resolve_uncommitted_docstring_mentions_inv24`
- INV-25: `tests/test_auto_cmd_inv25.py` (2 tests)
- INV-26: `tests/test_auto_cmd_inv26.py` (4 tests)
- INV-29: `tests/test_inv_documentation.py::test_pre_merge_loop2_docstring_mentions_inv29`

Run:

```bash
python -m pytest tests/test_auto_cmd_inv25.py tests/test_auto_cmd_inv26.py tests/test_inv_documentation.py -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: milestone D acceptance sweep with all tests green"
```

---

## Milestone D — Acceptance

Tras completar las 18 tareas (Task 0 + Tasks 1-17):

- **7 modulos existentes endurecidos** en `skills/sbtdd/scripts/` (auto_cmd, dependency_check, reporters/rust_reporter, reporters/ctest_reporter, pre_merge_cmd, resume_cmd, init_cmd). Ningun modulo nuevo.
- **1 nueva clase public** (`AutoRunAudit` en `auto_cmd.py`) — unica superficie de API nueva del milestone. Todo el resto son funciones privadas (prefijo `_`).
- **13 test files nuevos** bajo `tests/`:
  - `test_auto_run_audit.py` (7 tests — Task 1)
  - `test_auto_cmd_inv25.py` (2 tests — Task 2)
  - `test_auto_cmd_inv26.py` (4 tests — Task 3)
  - `test_auto_cmd_exit8.py` (3 tests — Task 4)
  - `test_dependency_check_python_floor.py` (6 tests — Task 5)
  - `test_dependency_check_rust_versions.py` (5 tests — Task 6)
  - `test_rust_reporter_nextest_env.py` (5 tests — Task 7)
  - `test_ctest_reporter_empty_xml.py` (4 tests — Task 8)
  - `test_resume_cmd_magi_conditions.py` (3 tests — Task 9)
  - `test_resume_cmd_concurrent_state.py` (2 tests — Task 10)
  - `test_resume_cmd_dry_run_integration.py` (3 tests — Task 11)
  - `test_pre_merge_cmd_exit8.py` (1 test — Task 12)
  - `test_inv_documentation.py` (4 tests — Tasks 14-16)
  - `test_pre_merge_resume_integration.py` (1 test — Task 13)
- **4 fixtures nuevos** bajo `tests/fixtures/` (2 junit-xml + 2 auto-run JSON).
- `make verify` limpio: pytest + ruff check + ruff format --check + mypy (strict).
- `make verify` runtime budget: `<= 75 segundos` (expected increment from Milestone C's 60s budget; marker `@pytest.mark.slow` permitido para outliers).
- ~30 commits atomicos con prefijos sec.M.5:
  - Task 0: `chore:` (fixtures bookkeeping).
  - Tasks 1, 4, 5, 6, 7, 8, 9, 10, 12, 17: multi-commit `test:` → `feat:`/`fix:` → opcional `refactor:`.
  - Tasks 2, 3, 11, 13: `test:` (regression-pinning tests).
  - Tasks 14, 15, 16: `test:` (Task 14) + `docs:` (Tasks 14, 15, 16 impl commits).
  - Task 17: `chore:` (acceptance sweep).

Productos habilitados para Milestone E:

- `.claude/auto-run.json` tiene un schema autoritativo que SKILL.md puede documentar sin ambiguedad.
- Pre-flight reports + reporter error messages son friendlier; README (Milestone E) puede reusar estos mensajes como troubleshooting reference.
- Resume user journey (`pre-merge exit 8 → resume`) esta pinned; SKILL.md puede referirla sin riesgo de regresion silenciosa.

No implementados en Milestone D (se difieren a Milestone E):

- `skills/sbtdd/SKILL.md` (orchestrator skill con reglas embebidas).
- `.claude-plugin/plugin.json` + `marketplace.json` manifests.
- `README.md` profesional (shields, arquitectura, contributing).
- Pulido adicional de documentacion cross-archivo fuera de los 3 INFOs consolidados aqui.

---

## Self-Review (pre-MAGI Checkpoint 2)

**1. Scope coverage (items 1-15 del Goal):**

- Item 1 (AutoRunAudit) → Task 1.
- Item 2 (INV-25) → Task 2.
- Item 3 (INV-26) → Tasks 3 + 4 (4 enriches the audit with counts).
- Item 4 (cargo-clippy/fmt regex) → Task 6.
- Item 5 (Python floor) → Task 5.
- Item 6 (NEXTEST env) → Task 7.
- Item 7 (empty JUnit XML) → Task 8.
- Item 8 (resume magi-conditions.md) → Task 9 + integration in Task 13.
- Item 9 (concurrent state file) → Task 10.
- Item 10 (resume --dry-run) → Task 11.
- Item 11 (pre-merge exit 8 stderr) → Task 12 + integration in Task 13.
- Item 12 (auto exit 8 counts) → Task 4.
- Item 13 (INV-24 docstring) → Task 14.
- Item 14 (INV-29 docstring) → Task 15.
- Item 15 (TOCTOU comment) → Task 16.

**2. Invariant enforcement audit:**

| INV | Covered by Milestone D tasks | Status |
|-----|------------------------------|--------|
| INV-24 | Task 14 (docstring) + Task 10 (concurrent guard is INV-17 adjacent) | Documented |
| INV-25 | Task 2 (regression test) | Pinned |
| INV-26 | Tasks 1, 3, 4 (schema + audit completeness + counts) | Hardened |
| INV-29 | Task 15 (docstring) | Documented |
| INV-19 | Task 5 (Python floor hardening) | Hardened |
| INV-30 | Tasks 9, 10, 11, 13 (resume edge cases) | Hardened |

**3. Commit prefix audit:** see table in "Milestone D — Acceptance" above; every task's commit follows sec.M.5 precedence. `docs:` is introduced for pure documentation commits in Phase 4, consistent with `~/.claude/CLAUDE.md` §Git commit types.

**4. Placeholder scan:** grep `\bTODO\b|\bTODOS\b|\bTBD\b` on this plan → 0 matches (INV-27 self-enforced). Test-fixture strings contain no uppercase placeholders.

**5. Frozen-module impact audit:** every edit to a Milestone A/B/C module is accompanied by at least one explicit regression test in `tests/` added in Milestone D, and every `make verify` invocation MUST keep prior-milestone tests green. The "Frozen-module policy" table above lists the 1:1 mapping.

**6. Type consistency:**
- `AutoRunAudit` is `@dataclass(frozen=True)` — consistent with `PluginConfig`, `SessionState`, `DependencyCheck`, `DependencyReport`, `MAGIVerdict`.
- `_parse_condition_counts_from_msg` returns `tuple[int, int]` — consistent with `_count_plan_tasks` in `status_cmd`.
- `_check_python_binary` / `_check_binary` both return `DependencyCheck` — symmetric with existing checks.
- `ensure_nextest_experimental_env` raises `ValidationError` — consistent with other pre-flight failures in reporters.
- `_assert_state_stable_between_reads` raises `StateFileError` — the canonical exception type from Milestone A for any `session-state.json` issue.

**7. Back-compat guarantee:**
- `_write_auto_run_audit` keeps accepting `dict` to preserve any Milestone C call-site survival during the Task-1 migration window.
- `run_pipeline` keyword-only `check_env=True` default preserves existing behavior; tests can opt out with `check_env=False`.
- No public API removed; no public API signature narrowed.

---

## Execution Handoff

Plan listo para MAGI Checkpoint 2. Al aprobarse con veredicto >= `GO_WITH_CAVEATS` full non-degraded, se guarda como `planning/claude-plan-tdd-D.md` (incorporando las *Conditions for Approval* que MAGI reporte) y se inicia ejecucion via `/subagent-driven-development` (sesion actual, tareas independientes, recommended) o `/executing-plans` (sesion separada con checkpoints).
