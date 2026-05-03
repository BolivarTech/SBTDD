# Especificacion base — sbtdd-workflow v1.0.1 (post-v1.0.0)

> Raw input para `/brainstorming` (primera fase del ciclo SBTDD para v1.0.1).
> `/brainstorming` consumira este archivo y generara `sbtdd/spec-behavior.md`
> (BDD overlay con escenarios Given/When/Then testables).
>
> Generado 2026-05-03 post-v1.0.0 ship (commit `0992407`, tag `v1.0.0`).
> v1.0.0 shipped Pillar 1 (Feature G cross-check meta-reviewer + F44.3
> retried_agents propagation + J2 ResolvedModels preflight) + Pillar 2
> (Feature I schema_version + Group B options 2 spec-snapshot + 5 auto-gen
> stubs) + v0.5.1 fold-in. Bundle accepted at-threshold tras Loop 2 3-iter
> convergence (3C -> 2C -> 0C). G1 binding ahora cierra INV-0 path para
> v1.1.0+ (cap=3 HARD).
>
> Source of truth autoritativo para v0.1+v0.2+v0.3+v0.4+v0.5+v1.0 frozen
> se mantiene en `sbtdd/sbtdd-workflow-plugin-spec-base.md`; este documento
> NO lo reemplaza — agrega el delta v1.0.1 a la base.
>
> Archivo cumple INV-27: cero matches uppercase placeholder (verificable con grep).
>
> **v1.0.1 es ciclo single-pillar** per CHANGELOG `[1.0.0]` Process notes
> binding commitment ("v1.1.0 defaults to single-pillar releases unless
> explicit user authorization for multi-pillar bundle"). Aplica a v1.0.x
> tambien por consistencia. Cuatro items LOCKED, todos del CHANGELOG
> `[1.0.0]` Deferred section.

---

## 1. Objetivo

**v1.0.1 = "Cross-check completion + dogfood"**: completa el camino del
default-flip de `magi_cross_check: true` y ejerce empíricamente Feature G
(shipped v1.0.0) por primera vez en su propio ciclo de desarrollo via
`/sbtdd pre-merge`.

Cuatro items LOCKED, todos enumerados en CHANGELOG `[1.0.0]` Deferred:

1. **Own-cycle cross-check dogfood** (CHANGELOG sec.G3-vacuous-by-construction
   note + LOCKED v1.0.1 commitment): el ciclo v1.0.1 es el primero que invoca
   `/sbtdd pre-merge` (no `python run_magi.py` directo) en su propio ciclo
   de desarrollo. Esto exercita `pre_merge_cmd._loop2_cross_check` sobre el
   diff real v1.0.0->v1.0.1 y genera `.claude/magi-cross-check/iter*.json`
   audit artifacts. Item operational + verification-only; cero codigo nuevo.
2. **Cross-check telemetry script** (CHANGELOG `[1.0.0]` Deferred bullet):
   nuevo `scripts/cross_check_telemetry.py` que agrega audits cross-cycle
   en reporte para soportar el default-flip criteria (a)/(b)/(c).
3. **Cross-check prompt diff threading** (CHANGELOG W-NEW1 bullet): conectar
   el diff real (ya computado por `_compute_loop2_diff`, cap raised to 1MB
   en v1.0.0) al template del prompt de `_build_cross_check_prompt`. Cierra
   el misleading-API smell.
4. **H5-2 spec_lint enforcement** (CHANGELOG `[1.0.0]` Deferred bullet):
   nuevo `scripts/spec_lint.py` (o equivalente) wired desde `spec_cmd.main`
   antes del Checkpoint 2 dispatch para que verifique 1:1 scenario-to-test
   stub mapping en el plan. Cierra el plan-time enforcement gap del H5
   ship parcial (v1.0.0 = solo H5-1 auto-generation).

Criterio de exito v1.0.1:
- Plugin instalable desde `BolivarTech/sbtdd-workflow` (marketplace
  `bolivartech-sbtdd`); version bumpea 1.0.0 -> 1.0.1.
- Tests baseline 1033 + 1 skipped preservados sin regresion + ~15-25 nuevos
  (telemetry script + spec_lint + diff threading tests). Spec sec.10.4
  NF-B target reasonable: +15-25 nuevos = 1048-1058 final.
- `make verify` runtime <= 150s (NF-A budget se mantiene).
- Cross-check audit artifacts presentes post pre-merge para el primer
  ciclo (Item 1 dogfood verificado empiricamente).
- v1.0.0 LOCKED commitments del CHANGELOG `[1.0.0]` Deferred section
  shipped (los cuatro items completos).
- G1 binding respetado: cap=3 HARD para Checkpoint 2; sin INV-0 path.
- G2 binding respetado: si Loop 2 iter 3 no converge clean, scope-trim
  default per CHANGELOG `[0.5.0]` process commitment.

Out of scope v1.0.1 (defer a v1.1.0):
- INV-31 default flip dedicated cycle.
- GitHub Actions CI workflow.
- Group B options 1, 3, 4, 6, 7 (opt-in flags).
- Migration tool real test (cuando v3 migration sea necesaria).
- AST-based dead-helper detector (R11 sweep methodology como tooling).
- W8 Windows file-system retry-loop (accepted-risk per spec sec.4.4.5).
- `_read_auto_run_audit` skeleton wiring (cuando un status renderer real
  necesite consumir el audit JSON).

---

## 2. Alcance v1.0.1 — items LOCKED post-v1.0.0

### 2.1 Item 1 — Own-cycle cross-check dogfood

**Problema empirico**: v1.0.0 ciclo dispatcho MAGI Loop 2 directamente via
`python skills/magi/scripts/run_magi.py code-review <payload>` (el unico
entrypoint disponible para arbitrary loop runs). El cross-check
(`pre_merge_cmd._loop2_cross_check`) solo dispara dentro de
`pre_merge_cmd._loop2`, que se invoca via `/sbtdd pre-merge` o `/sbtdd auto`
phase 3. Por lo tanto v1.0.0 NO ejercito Feature G en su propio ciclo —
G3 sign-off vacuous-by-construction (ningun audit artifact generado).

**Entrega v1.0.1**:

- Ciclo v1.0.1 invoca `/sbtdd pre-merge` (no `run_magi.py` direct) para
  Loop 1 + Loop 2 post-implementacion.
- `magi_cross_check: true` flipped en `.claude/plugin.local.md`
  (gitignored, operator-side; ya hecho en v1.0.0 iter 3 fix).
- Audit artifacts `.claude/magi-cross-check/iter*-<timestamp>.json`
  generados durante Loop 2; verificados manualmente contra el G6 schema
  (spec sec.2.1 Feature G escenario G6 fields: iter, timestamp,
  magi_verdict, original_findings, cross_check_decisions,
  annotated_findings).
- G3 manual sign-off recorded en CHANGELOG `[1.0.1]` Process notes
  con timestamp + iter audit JSON paths + criterion (a)/(b)/(c)
  evidence summary.
- Si meta-reviewer cataches false-positive CRITICALs (KEEP -> DOWNGRADE
  o REJECT decisions), recordar en CHANGELOG como inicio del trail
  empirico para el eventual default-flip.

**Cero codigo nuevo**. Item es operational + verification.

**Invariantes obligatorios**: ninguno nuevo. Honra INV-35 (cross-check
obligatorio antes de INV-29 gate cuando `magi_cross_check: true`) que
ya esta documentado.

### 2.2 Item 2 — Cross-check telemetry aggregation script

**Problema**: balthasar Loop 2 iter 3 WARNING. Sin tooling, el operator
manual-tally del default-flip criteria (a)/(b)/(c) en CHANGELOG `[0.5.0]`
sec.8.2 es prohibitively expensive — cada release que ejercita Feature G
requiere walk individual JSON audit files, contar KEEP/DOWNGRADE/REJECT,
identificar false-negatives. Este overhead defiere el flip
perpetuamente.

**Entrega v1.0.1**:

- Nuevo `scripts/cross_check_telemetry.py` (Python 3.9+, stdlib-only).
- API: `python scripts/cross_check_telemetry.py [--since-tag <vX.Y.Z>]`
  con default reading entire `.claude/magi-cross-check/` directory.
- Output: structured report (markdown o JSON, default markdown) con:
  - Total cross-check invocations en window.
  - KEEP/DOWNGRADE/REJECT decisions counts + percentages.
  - Dispatch-failure / json-parse-failure counts (vs successful runs).
  - Findings rejected al INV-29 stage (operator-ratified) vs not-ratified.
  - Qualitative section template para criterion (c) zero false-negative
    annotations: operator marca casos donde KEEP fue post-hoc detectado
    como deberia-haber-sido REJECT.
- Tests: ~10-15 new tests covering parsing, aggregation, ventana filtering,
  malformed JSON tolerancia, empty-dir caso, multi-cycle aggregation.
- Cross-reference: invocable desde post-pre-merge gate como observability
  hook (out-of-scope v1.0.1 para auto-invocation; manual operator runs OK).

**Invariantes obligatorios**: ninguno nuevo. Script es read-only sobre
audit files; no toca state file ni commits.

### 2.3 Item 3 — Cross-check prompt diff threading (W-NEW1)

**Problema**: v1.0.0 commit `9dd25fa` shipea `_compute_loop2_diff` (cap
raised to 1MB en iter 2->3 fix) pero `_build_cross_check_prompt` template
NO embebe el diff content en el prompt body — solo lista verdict +
findings text. El prompt header verbalmente menciona "diff context" pero
no entrega; misleading-API smell. Loop 1 iter 2 W-NEW1 documented as
v1.0.1 deferral.

**Entrega v1.0.1**:

- Modificar `_build_cross_check_prompt(verdict, findings, diff)` template
  para incluir nueva seccion `## Cumulative diff under review` con el
  diff content (truncated to cap with marker if > cap).
- Si `diff == ""` o falla (subprocess error capturado por
  `_compute_loop2_diff`), embed placeholder text:
  `[Empty diff: meta-review based on findings text + spec/plan context]`
  para que el reviewer entienda explicitamente que no hay grounding diff
  disponible.
- Tests: `test_build_cross_check_prompt_embeds_diff_when_present`,
  `test_build_cross_check_prompt_handles_empty_diff_gracefully`,
  `test_build_cross_check_prompt_truncated_diff_marker_shown` (3-5 tests
  total nuevos).
- Validar que el prompt resultante no excede el skill input limit razonable
  (e.g., 1MB diff + ~5KB findings text = ~1MB prompt; verificar contra
  observed skill limits).

**Invariantes obligatorios**: ninguno nuevo.

### 2.4 Item 4 — H5-2 spec_lint enforcement

**Problema**: caspar Checkpoint 2 iter 3 WARNING. v1.0.0 shipea H5-1
(superpowers_dispatch.invoke_writing_plans extiende prompt con
auto-generation directive de scenario stub tests) PERO sin enforcement.
Los planners pueden silently delete stubs auto-generados, skipear el
contract de "1:1 scenario-to-test mapping at plan time", y el missing
test solo se cataches eventualmente al pre-merge — meses despues, en
el peor caso. La friction-by-design es DURANTE Checkpoint 2
(pre-implementation), no DESPUES de implementar el codigo entero.

**Entrega v1.0.1**:

- Nuevo `scripts/spec_lint.py` (o agregar a modulo existente como
  `spec_snapshot.py` reusando `_extract_scenarios`).
- API: `spec_lint.lint_plan_has_scenario_stubs(spec_path, plan_path) -> None`
  raises `ValidationError("Plan task X has no scenario stub for Escenario
  N: <title>")` si hay scenarios sin stub matching.
- Logica: para cada Escenario en spec sec.4, verificar que existe en el
  plan un test stub con nombre `test_scenario_<N>_<slug>()` con body
  `pytest.skip("Scenario stub: replace with real assertions")` o body
  con assertions reales (interpretado como already implemented). El
  enforcement es: scenario WITHOUT corresponding stub-or-implemented
  test = ValidationError.
- Wired into `spec_cmd.main` ANTES del MAGI Checkpoint 2 dispatch como
  precondition gate (raise antes de gastar Checkpoint 2 iters en un plan
  defectuoso).
- Tests: ~5-8 nuevos covering: missing stub -> fail, stub presente con
  assertions reales -> pass (no skip), stub con body modificado pero NO
  pytest.skip -> pass (already implemented), edge cases con titles
  especiales (acentos, spaces, caracteres unicode), empty sec.4 -> pass
  (no scenarios = vacuously satisfied).
- Backward compat: planes existentes sin scenario stubs (e.g., plans
  generados pre-v1.0.0) bypass el lint via flag explicit
  `--skip-spec-lint` o automatic detection por absence de v1.0.0+ marker
  en el plan. Documentar bypass en CHANGELOG.

**Invariantes obligatorios**: nuevo INV-37 propuesto (renumerar si
conflict): "Plan generado por `/sbtdd spec` post-v1.0.1 DEBE pasar
spec_lint scenario-to-stub coverage check antes del Checkpoint 2 MAGI
dispatch, salvo `--skip-spec-lint` flag set por el operator con razon
documented."

---

## 3. Restricciones y constraints duros

Todos los invariantes INV-0 a INV-36 preservados. Propuestas v1.0.1:

- **INV-37 (propuesta, contingent on Item 4)**: spec_lint scenario-to-stub
  enforcement obligatorio antes de Checkpoint 2 MAGI dispatch.

Critical durante implementacion v1.0.1:

- **G1 binding HARD** (CHANGELOG `[1.0.0]` Process notes): cap=3 sin
  INV-0 path en MAGI Checkpoint 2. v1.1.0+ aplica de forma binding;
  v1.0.1 honra como precedente cerrando 2-streak.
- **G2 binding** (spec sec.7.1.3): Loop 2 iter 3 verdict triggers
  scope-trim default OR exact phrase override. v1.0.1 single-pillar
  bundle deberia converger en <=3 iters limpio; si no, scope-trim
  inmediato per default.
- **Single-pillar default** (CHANGELOG `[1.0.0]` Process notes): v1.0.1
  honra commitment.
- **Invocation-site tripwires** (CHANGELOG `[1.0.0]` Process notes
  R11 lesson): cualquier helper nuevo (incluyendo en Item 2 telemetry
  script + Item 4 spec_lint) ships con invocation-site tripwire test
  ANTES de close-task. No "test in isolation, never wired" repeat.
- **`/receiving-code-review` sin excepcion** (CHANGELOG `[1.0.0]`
  Process notes): every Loop 2 iter MUST run skill on findings; no
  override flag.
- INV-22 (sequential auto) preservado.
- INV-26 (audit trail) preservado.
- INV-27 (spec-base placeholder): este documento cumple.

### Stack y runtime

Sin cambios vs v1.0.0:
- Python 3.9+, mypy --strict, cross-platform, stdlib-only en hot paths.
- Dependencias externas: git, tdd-guard, superpowers, magi (>= 2.2.x),
  claude CLI.
- Dependencias dev: pytest, pytest-asyncio, ruff, mypy, pyyaml.
- Licencia dual MIT OR Apache-2.0.

### Reglas duras no-eludibles (sin override)

- INV-0 autoridad global.
- INV-27 spec-base sin uppercase placeholder markers (este doc cumple).
- Commits en ingles + sin Co-Authored-By + sin IA refs.
- No force push a ramas compartidas (INV-13).
- No commitear archivos con patrones de secretos (INV-14).
- G1 binding cap=3 HARD para Checkpoint 2 (CHANGELOG `[1.0.0]`).

---

## 4. Funcionalidad requerida (SDD)

(F-series continua desde F76 v1.0.0; v1.0.1 starts at F80.)

**F80** (Item 1). v1.0.1 ciclo dispatcha Loop 1 + Loop 2 via
`/sbtdd pre-merge` (no `run_magi.py` direct). Cross-check audit artifacts
generated y verificados.

**F81** (Item 2). `scripts/cross_check_telemetry.py` exists with API:
- `--since-tag <vX.Y.Z>` flag (optional, default reads entire dir).
- Output markdown report con KEEP/DOWNGRADE/REJECT counts + dispatch
  failures + qualitative criterion (c) template.

**F82** (Item 2). `cross_check_telemetry.aggregate(audit_files: list[Path])
-> dict[str, Any]` returns structured aggregation dict.

**F83** (Item 2). Tolerance: malformed JSON files in audit dir produce
warning + skip, not crash; missing dir = empty report not error.

**F84** (Item 3). `_build_cross_check_prompt(verdict, findings, diff)`
template embeds diff content under `## Cumulative diff under review`
section. Empty/failed diff -> placeholder marker.

**F85** (Item 3). Diff truncation respected: marker `[... truncated for
prompt budget ...]` shown when diff > cap.

**F86** (Item 4). `spec_lint.lint_plan_has_scenario_stubs(spec_path,
plan_path)` exists; raises `ValidationError` on missing scenario stub.

**F87** (Item 4). `spec_cmd.main` invokes spec_lint BEFORE MAGI Checkpoint 2
dispatch as precondition gate.

**F88** (Item 4). `--skip-spec-lint` CLI flag bypasses gate with required
`--skip-reason` companion flag (not silent).

### Requerimientos no-funcionales (NF)

**NF23**. `make verify` runtime <= 150s budget (v1.0.0 baseline 117s; v1.0.1
expected slight increase from new tests; soft-target <= 130s post-Item 2+4).

**NF24**. v1.0.0 plans (without scenario stubs) load via spec_lint with
backward-compat path (skip flag or version detection). NO regression on
existing v1.0.0 ship workflow.

**NF25**. v1.0.0 cross-check audit JSON files (none exist for v1.0.0
because cycle didn't generate them; but v1.0.1 onwards) parse via
telemetry script.

---

## 5. Scope exclusions

Out-of-scope para v1.0.1:

- **INV-31 default flip dedicated cycle** (deferred a v1.1.0+; separate
  field-data doc requires its own cycle).
- **GitHub Actions CI workflow** (deferred v1.1).
- **Group B options 1, 3, 4, 6, 7** (opt-in flags only; not core deliverable).
- **Migration tool real test** (cuando v3 migration sea necesaria; no
  trigger en v1.0.1).
- **AST-based dead-helper detector** (caspar v1.0.0 iter 3 INFO; v1.x
  evaluation if R11 sweep methodology proves insufficient).
- **W8 Windows file-system retry-loop** (accepted-risk per spec sec.4.4.5;
  v1.x evaluation only if observed in field).
- **`_read_auto_run_audit` skeleton wiring** (intentional v1.0.1+ skeleton
  per CHANGELOG; wire when status renderer needs it, not preemptively).
- **R11 sweep methodology codification as `docs/process/r11-sweep.md`**
  (melchior v1.0.0 iter 3 INFO; v1.x docs cleanup).
- **Spec sec.7.1.3 G2 amendment defining "convergence cleanly"** (caspar
  v1.0.0 iter 3 W6/I6; v1.x spec cleanup pass).
- **`magi_cross_check` default-flip to `true`** (requires criterion
  (a)/(b)/(c) evidence per CHANGELOG `[0.5.0]` sec.8.2; v1.0.1 begins the
  evidence trail via Item 1 + Item 2 tooling, but the actual flip ships
  in a future v1.x cycle once 2+ non-self-referential dogfood cycles
  ratify).

---

## 6. Criterios de aceptacion finales

v1.0.1 ship-ready cuando:

### 6.1 Functional Item 1 — Own-cycle dogfood

- **F1**. Ciclo v1.0.1 Loop 1 + Loop 2 dispatcheados via `/sbtdd pre-merge`
  (verificable por presence of audit artifacts AND absence of `run_magi.py`
  direct invocations en este ciclo's command history).
- **F2**. `magi_cross_check: true` set en `.claude/plugin.local.md`
  durante el ciclo (operator-side, gitignored).
- **F3**. Al menos 1 audit artifact `.claude/magi-cross-check/iter*-*.json`
  generado durante el ciclo, parseable, schema-compliant per G6.
- **F4**. CHANGELOG `[1.0.1]` Process notes registra G3 manual sign-off
  con timestamp + audit paths + criterion (a)/(b)/(c) evidence summary
  (puede ser "first cycle: insufficient data for default-flip; trail
  initiated").

### 6.2 Functional Item 2 — Telemetry script

- **F5**. `scripts/cross_check_telemetry.py` exists.
- **F6**. CLI invocation `python scripts/cross_check_telemetry.py` produces
  markdown report.
- **F7**. `--since-tag <vX.Y.Z>` flag works (filters audit files by file
  mtime or by parsed iter timestamp >= tag's commit date).
- **F8**. Tests: 10-15 new tests cover happy path + edge cases + malformed
  JSON tolerance + empty dir.
- **F9**. Invocation-site tripwire: NOT applicable (script is operator-invoked
  CLI, not invoked from auto/pre-merge production path).

### 6.3 Functional Item 3 — Diff threading

- **F10**. `_build_cross_check_prompt` embeds diff in template body.
- **F11**. Empty/failed diff produces placeholder marker (not silent).
- **F12**. Truncation marker shown when diff > cap.
- **F13**. Tests: 3-5 new tests (embed when present, handle empty, truncation
  marker visibility).
- **F14**. Invocation-site tripwire: existing
  `test_c2_loop2_passes_real_diff_to_cross_check` (v1.0.0 iter 2->3 fix)
  continues passing, validates production path.

### 6.4 Functional Item 4 — spec_lint

- **F15**. `scripts/spec_lint.py` exists with public API.
- **F16**. `spec_cmd.main` invokes spec_lint before MAGI Checkpoint 2.
- **F17**. `--skip-spec-lint --skip-reason "<text>"` CLI flag bypasses gate;
  silent bypass NOT possible.
- **F18**. Tests: 5-8 new tests (missing stub, present stub, modified stub,
  unicode titles, empty sec.4).
- **F19**. Invocation-site tripwire: spec_lint MUST be referenced from
  `spec_cmd.main` body; spy or grep audit test confirms.
- **F20**. Backward compat: v1.0.0 plans (without v1.0.1 scenario stubs)
  parse correctly when bypass flag set; documented in CHANGELOG.

### 6.5 No-functional

- **NF-A**. `make verify` clean: pytest + ruff check + ruff format + mypy
  --strict, runtime <= 150s. Soft-target <= 130s.
- **NF-B**. Tests baseline 1033 + 1 skipped preservados + ~15-25 nuevos
  (15 telemetry + 5 spec_lint + 5 prompt threading approx) = ~1048-1058.
- **NF-C**. Cross-platform (POSIX + Windows). Windows-specific tests
  empirically pass.
- **NF-D**. Author/Version/Date headers en nuevos `.py` files
  (cross_check_telemetry.py, spec_lint.py).
- **NF-E**. Zero modificacion a modulos frozen excepto los enumerados
  explicitamente (auto_cmd, pre_merge_cmd, spec_cmd, plus new scripts).

### 6.6 Process

- **P1**. MAGI Checkpoint 2 verdict >= `GO_WITH_CAVEATS` full per INV-28.
  Iter cap=3 HARD per G1 binding (CHANGELOG `[1.0.0]`); NO INV-0 path.
- **P2**. Pre-merge Loop 1 clean-to-go + Loop 2 MAGI verdict >=
  `GO_WITH_CAVEATS` full no-degraded. Cross-check sub-fase fires (Item 1
  validation).
- **P3**. CHANGELOG `[1.0.1]` entry written con secciones Added /
  Changed / Process notes + G3 sign-off record + Item 2 telemetry baseline.
- **P4**. Version bump 1.0.0 -> 1.0.1 sync `plugin.json` +
  `marketplace.json`.
- **P5**. Tag `v1.0.1` + push (con autorizacion explicita user).
- **P6**. `/receiving-code-review` skill applied to every Loop 2 iter
  findings without exception (no v1.0.0 iter 1 bypass repeat).

### 6.7 Distribution

- **D1**. Plugin instalable via `/plugin marketplace add ...` +
  `/plugin install ...`.
- **D2**. Cross-artifact coherence tests actualizados.
- **D3**. Nuevos subcomandos / flags documentados en README + SKILL.md +
  CLAUDE.md.

---

## 7. Dependencias externas nuevas

Ninguna runtime nueva. Dev: ninguna nueva. Item 1 depende de
`/sbtdd pre-merge` operational which depends on the v1.0.0 ship; testing
uses MAGI 2.2.x+ goldens cached locally.

---

## 8. Risk register v1.0.1

- **R1**. Item 1 dogfood discovers bugs in `/sbtdd pre-merge` self-hosting
  path that were never exercised pre-v1.0.1. Mitigation: bugs caught are
  valid Loop 2 findings -> mini-cycle TDD fixes; if scope inflates, escape
  hatch is scope-trim items 2/3/4 to v1.0.2 leaving Item 1 + bug fixes
  as v1.0.1.
- **R2**. Item 2 telemetry script reads malformed audit JSON files (e.g.,
  partial writes from killed processes) and crashes. Mitigation: explicit
  tolerance per F83 + tests covering edge case.
- **R3**. Item 3 diff threading produces prompts that exceed skill input
  limits when v1.0.1 cumulative diff is large. Mitigation: cap mechanism
  already in `_compute_loop2_diff` (1MB) + truncation marker; v1.0.1
  bundle is small (4 items, single-pillar) so diff << cap empirically.
- **R4**. Item 4 spec_lint blocks legitimate plans that have already-
  implemented tests instead of stubs. Mitigation: F18 explicit test for
  this case + bypass flag F17.
- **R5**. Bundle scope creep: Item 1 dogfood reveals so many plugin bugs
  that v1.0.1 cycle never exits. Mitigation: G1 binding cap=3 Checkpoint 2
  + G2 binding scope-trim default; explicit escape hatch documented.
- **R6**. NF-A 150s budget exceeded by Item 2 telemetry tests (read-many-
  files pattern). Mitigation: mark long-running telemetry tests with
  `@pytest.mark.slow` per spec sec.10.4 convention.
- **R7**. Item 2 + 4 helpers ship as dead code (not invoked from production
  paths) — same pattern that bit v1.0.0. Mitigation: F19 invocation-site
  tripwire for Item 4; Item 2 is operator-CLI by design (not auto-invoked)
  so doesn't apply but documented in spec.

---

## 9. Referencias

- Contrato autoritativo: `sbtdd/sbtdd-workflow-plugin-spec-base.md`.
- v1.0.0 ship record: tag `v1.0.0` (commit `0992407` on `main`).
- v1.0.0 cycle decisions (brainstorming + 5-iter Checkpoint 2 + Loop 1 +
  3-iter Loop 2 at-threshold acceptance): see `CHANGELOG.md` `[1.0.0]`
  and `.claude/magi-runs/v100-*` artifacts.
- v1.0.0 LOCKED commitments rolled into v1.0.1 per CHANGELOG `[1.0.0]`
  Deferred section (4 items above).
- v1.0.1 deferred items roadmap (continuing to v1.1.0+):
  - INV-31 default flip dedicated cycle.
  - GitHub Actions CI workflow.
  - Group B options 1, 3, 4, 6, 7.
  - Migration tool real test.
  - AST-based dead-helper detector.
  - W8 Windows file-system retry-loop.
  - `_read_auto_run_audit` skeleton wiring.
  - R11 sweep methodology codification.
  - Spec sec.7.1.3 G2 amendment.
  - `magi_cross_check` default-flip to `true`.

---

## Nota sobre siguiente paso

Este archivo cumple INV-27. Listo como input para `/brainstorming`.
Decisiones pendientes clave para brainstorming:

1. **Subagent partition**: 4 items, single-pillar. Probable single-subagent
   suffice (sequential), o 2-subagent paralelo si surfaces 100% disjoint
   (Item 2 + Item 4 son scripts new files; Item 3 modifies pre_merge_cmd;
   Item 1 is operational verify-only). Brainstorming evalua.
2. **Item ordering within sequential subagent**: 4 -> 3 -> 2 -> 1 per
   prior recommendation (Item 1 ultimo porque depende de tener todo lo
   demas Y consume el v1.0.1 cycle como vehiculo).
3. **Backward compat strategy for spec_lint**: flag-based bypass vs
   automatic detection. Brainstorming refina.
4. **Item 2 telemetry script invocation policy**: operator-CLI only en
   v1.0.1 (manual run); auto-invocation post pre-merge gate diferida a
   v1.0.2 si demanda surge.

Brainstorming refinara estas decisiones basado en complejidad, risk, y
empirical findings de v1.0.0 cycle.
