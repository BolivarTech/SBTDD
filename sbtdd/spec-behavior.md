# BDD overlay — MAGI gate alignment + canonical template

> Generado por `/brainstorming` el 2026-05-01. Este spec NO corresponde a una
> version bump de SBTDD (v0.4.0 ya shipped, v0.5.0 brainstorming pausado en
> design-presented). Este es un side-track de **docs alignment cross-project**:
> sincroniza bidireccionalmente §6 de SBTDD's `CLAUDE.local.md` con §2 de
> MAGI plugin's `CLAUDE.local.md`, y extrae la version canonica como template
> copy-paste para futuros proyectos.
>
> Pure docs scope. Cero codigo, cero tests automatizados, cero version bump,
> cero CHANGELOG entry obligatoria. Verification = manual review + grep.
>
> Despues de aplicar este spec, retomar v0.5.0 brainstorming en task #2
> (design ya aprobado: split observability cycle, scope locked en 4
> deliverables + hotfixes, 2 parallel subagents disjoint).
>
> INV-27 compliant: cero matches uppercase placeholder en este archivo
> (los placeholders del template estan documentados como `{name}`-style
> identifiers en sus secciones designadas, NO como `TODO`/`TODOS`/`TBD`).

---

## 1. Resumen ejecutivo

**Objetivo:** sincronizar conocimiento sobre MAGI quality gate entre dos
proyectos siblings (SBTDD y MAGI plugin) cuyos `CLAUDE.local.md` evolucionaron
en paralelo y aprendieron deltas distintos sobre el mismo concepto. Producir
adicionalmente un canonical template parameterizable que cualquier proyecto
nuevo pueda adoptar via copy-paste sin tener que reconstruir el aprendizaje.

**Out-of-scope** v0.5.0+ semantic features (esos siguen su propio brainstorm
una vez este side-track cierre).

**Criterio de exito:**
- Tres archivos producidos / actualizados (1 nuevo template, 1 edit local,
  1 nuevo patch artifact).
- Template self-contained: un proyecto nuevo dropping la seccion + filling
  placeholders deberia obtener un MAGI gate operacional sin tener que leer
  ni §2 (MAGI) ni §6 (SBTDD) originales.
- Both `CLAUDE.local.md` llegan al mismo flujo operacional al final del
  alignment (modulo deltas project-specific genuinos).
- Cero contradicciones entre los tres docs.

---

## 2. Deliverable 1 — `docs/magi-gate-template.md` (canonical template)

### 2.1 Scope

Single markdown file at `docs/magi-gate-template.md`, committed al repo
(public artifact). Contiene UNA section principal `## MAGI Quality Gate`
(sin numero — el adopter elige donde encaja en su CLAUDE.local.md), mas
sub-sections cubriendo el superset de ambos proyectos.

### 2.2 Content layout (10 sub-sections)

| # | Sub-section | Source proveniente | Rol |
|---|-------------|--------------------|-----|
| 1 | Trigger criteria + skip rules | §2 §2.1+§2.2 | Cuando aplicar el gate (manual / hotfix / ad-hoc); plan-based work tiene su propio gate via SBTDD-style INV-29 |
| 2 | Two-loop sequencing | SBTDD §6 | Loop 1 `/requesting-code-review` clean-to-go ANTES de Loop 2 MAGI; rationale contaminacion de verdicts |
| 3 | Pass threshold + verdict action table | SBTDD §6 (tabla) + §2 §2.3 (high-impact keywords) | `GO_WITH_CAVEATS` full no-degraded; tabla con accion por cada veredicto + fork low-risk vs structural en GO_WITH_CAVEATS |
| 4 | Degraded MAGI handling | SBTDD §6 | STRONG_NO_GO degraded abort inmediato; otros consume iter + re-invoca esperando full 3-agent |
| 5 | Iteration cap + escalation | merge §2 §2.4 step 6 + SBTDD §6 root causes | Cap 3 iter, prompt al usuario; spec replan trigger entre las posibles causas |
| 6 | Triage via /receiving-code-review + mini-cycle TDD | SBTDD §6 (mini-ciclo) + §2 §2.4 step 4 (categorias) | fold-in / defer / reject; prefijos `test:` → `fix:` → `refactor:` |
| 7 | Carry-forward format | §2 §2.4.1 verbatim | Block prescriptivo con tabla iter/severity/title/decision/rationale + 4 reglas para agents |
| 8 | Review summary artifact | §2 §2.4 step 7 | `<feature>-review-summary.md` con tabla iter/severity/title/fix-commit; commit `docs(review):` |
| 9 | Cost awareness | §2 §2.5 verbatim | Opus default; smaller models truncan Caspar especificamente |
| 10 | Per-project setup placeholders | §2 §2.6 + extension | Lista checklist al final |

### 2.3 Placeholders documentados

Lista al final del template como checklist explicito:
- `{magi-script-path}` o `/magi:magi` slash — template documenta AMBAS opciones (subprocess directo y slash command); el adopter elige.
- `{review-summary-dir}` — e.g., `docs/reviews/`, `Docs/code-reviews/`, `.review/`.
- `{ErrorType}` o tipo de error del proyecto.
- `{test_command}` — `pytest`, `cargo test`, etc.
- `{language_specific_verification}` — comandos de §0.1 equivalentes.
- Lista de **domain risk surfaces** que el proyecto enumera (ejemplos por dominio: embedded, backend, frontend, distributed).
- Lista de **high-impact terms adicionales** (project-defined keywords que bloquean MAGI gate ademas del baseline).

### 2.4 Convencion de uso

Un proyecto que adopta el template:
1. Copy-paste la seccion entera a su `CLAUDE.local.md` con numero apropiado (e.g., `## 6. MAGI Quality Gate`).
2. Reemplaza placeholders con valores del proyecto.
3. Agrega cualquier delta propio (escapes, exceptions, integraciones particulares) en sub-sections nuevas debajo.

### 2.5 Escenarios Given/When/Then

**Escenario T1: nuevo proyecto adopta el template clean**

> **Given** un proyecto nuevo sin seccion MAGI en su `CLAUDE.local.md`.
> **When** el desarrollador copia el contenido entero de `docs/magi-gate-template.md` a su `CLAUDE.local.md` como `## N. MAGI Quality Gate` y reemplaza los placeholders documentados.
> **Then** el flujo operacional MAGI queda definido sin necesidad de consultar `§2` o `§6` originales; tiene Loop 1/Loop 2 sequencing, threshold, degraded handling, carry-forward, summary artifact, y cost awareness.

**Escenario T2: placeholder leakage detection**

> **Given** el template terminado.
> **When** se hace `grep -E '\{[a-z_]+\}' docs/magi-gate-template.md`.
> **Then** SOLO aparecen los placeholders documentados en seccion 2.3 — ningun `{ErrorType}` huerfano de §2 fuera de su contexto, ningun otro `{name}` no-listado.

**Escenario T3: internal consistency (no contradictions)**

> **Given** las 10 sub-sections del template.
> **When** se verifica cross-reference entre ellas.
> **Then** no hay reglas contradictorias (e.g., si sub-section 2 dice "Loop 1 first siempre", sub-section 5 escalation no dice "skip Loop 1 sometimes").

**Escenario T4: template equivalence with SBTDD §6**

> **Given** SBTDD's §6 actualizada con sus deltas (deliverable 2).
> **When** se compara mentalmente contra el template (modulo project-specific deltas).
> **Then** el flujo operacional descrito en §6 = flujo operacional descrito en template.

**Escenario T5: template equivalence with MAGI §2 patched**

> **Given** MAGI's §2 patched (deliverable 3 aplicado).
> **When** se compara mentalmente contra el template (modulo project-specific deltas).
> **Then** el flujo operacional descrito en §2 = flujo operacional descrito en template.

### 2.6 Acceptance criteria

- **T1**: walkthrough mental valida self-completeness.
- **T2**: grep produce solo placeholders documentados.
- **T3**: revision manual confirma cero contradicciones.
- **T4**, **T5**: cross-doc consistency verified manualmente.

---

## 3. Deliverable 2 — SBTDD `CLAUDE.local.md` updates

### 3.1 Scope

Edit local del archivo gitignored `CLAUDE.local.md` en raiz del proyecto SBTDD.
NO se commitea (per project policy `.gitignore` covers `CLAUDE.local.md`).
Cambios se aplican via Edit tool directamente.

### 3.2 5 nuevas sub-sections agregadas a §6

Agregadas al final de §6 "Code review", antes de §7 "Finalizacion":

- **§6.X Carry-forward format** (proveniente §2 §2.4.1 verbatim) — block prescriptivo con tabla iter/severity/title/decision/rationale + 4 reglas para agents (re-raise allowed, escalation permitted, match-by-exact-title, no retroactive blame). Customizado a SBTDD terminology: verdicts en `STRONG_NO_GO`-style (no `STRONG NO-GO`).
- **§6.X Review summary artifact** (proveniente §2 §2.4 step 7) — convencion `docs/reviews/<feature>-review-summary.md`, commit prefix `docs(review):`. Auto generado por `pre_merge_cmd`/`auto_cmd` en futuro (referenciado como follow-up backlog item; este spec NO implementa generacion automatica). Por ahora el operador lo escribe manualmente al cierre del MAGI gate.
- **§6.X Cost awareness** (proveniente §2 §2.5 verbatim) — opus default; smaller models truncan Caspar (adversarial verbose) → bias toward false-positive approval. Cross-reference con per-skill model selection (Feature E shipped en v0.3.0 — `auto_skill_models` en plugin.local.md).
- **§6.X Trigger criteria + skip rules para non-plan-based contexts** — para hotfixes, exploration, ad-hoc changes fuera del flow plan-based. Plan-based work sigue going through gate automaticamente (sin trigger criteria — INV-29 governs). Esta sub-section aplica a cuando NO existe `planning/claude-plan-tdd.md` aprobado (el "Flujo manual" de §3).
- **§6.X Domain-specific risk surfaces + high-impact terms** — slot extensible. Para SBTDD initial enumeration: subprocess kill-tree safety (Windows taskkill order), state-file corruption recovery patterns, INV-0 violation patterns en mensajes de commit (menciones a IA o Co-Authored-By).

### 3.3 Escenarios Given/When/Then

**Escenario S1: SBTDD §6 absorbe carry-forward format**

> **Given** SBTDD's `CLAUDE.local.md` §6 actual (sin sub-section "Carry-forward format").
> **When** spec se aplica.
> **Then** §6 contiene la sub-section verbatim adaptada al SBTDD verdict naming, ubicada despues de "Cuando se recibe feedback de code review" y antes de §7.

**Escenario S2: SBTDD §6 absorbe trigger criteria sin contradecir flow plan-based**

> **Given** SBTDD §6 invariant: "plan-based work atraviesa MAGI gate automaticamente" (INV-29).
> **When** se agrega sub-section "Trigger criteria + skip rules para non-plan-based".
> **Then** la nueva sub-section explicit-aplica SOLO a "Flujo manual" sin plan, no contradice INV-29. Cross-reference explicit a §3 "Flujo manual (fallback sin plan aprobado)".

**Escenario S3: SBTDD §6 mantiene su flow Loop 1 → Loop 2 unchanged**

> **Given** SBTDD §6 actual con sequencing Loop 1 → Loop 2 (INV-9).
> **When** sub-sections nuevas se agregan.
> **Then** sequencing actual preservado sin cambios; nuevas sub-sections complementan, no reemplazan.

### 3.4 Acceptance criteria

- **S1**, **S2**, **S3**: post-edit verification — re-leer §6 entera y confirmar fluidez sin contradicciones.

---

## 4. Deliverable 3 — MAGI patch artifact

### 4.1 Scope

Archivo nuevo `docs/cross-project/2026-05-01-magi-claude-local-patch.md`,
committed al repo SBTDD (audit trail del cross-project sync). Contiene
instrucciones explicitas para que el usuario aplique en proyecto MAGI session
siguiente. SBTDD repo NO modifica MAGI repo directamente (cross-project edits
no son automaticos).

### 4.2 Format del patch

Cada item del patch documenta:
- **Insert location**: e.g., "Insert NEW sub-section after MAGI §2.3 'Pass threshold' and before §2.4 'Procedure'".
- **Verbatim text to insert**: el contenido completo de la sub-section, listo para copy-paste.
- **Rationale**: una linea que explica por que este content viene de SBTDD's empirical learning.

### 4.3 5 sub-sections para insertar en MAGI's §2

- **Two-loop sequencing** — agregar `/requesting-code-review` Loop 1 clean-to-go antes de MAGI invocation. Rationale: filtra mechanical findings que contaminan verdicts MAGI individuales (Melchior/Balthasar/Caspar).
- **Degraded MAGI handling explicit** — STRONG_NO_GO degraded abort inmediato; otros consume iter + re-invoca esperando full 3-agent. Rationale: aceptar 2-agent verdict rompe el contrato "consenso 3 perspectivas".
- **Mini-ciclo TDD prefixes** — al aplicar findings categorizados como "fold in", seguir `test:` (reproduce) → `fix:` (resolve) → `refactor:` (polish) en commits separados. Rationale: atomic commits + audit trail uniforme.
- **Spec replan trigger** — al exhaust 3-iter cap, posibles root causes incluyen "spec defectuosa upstream del plan", no solo "implementacion divergio". Rationale: a veces el problema esta upstream y hay que volver a `/brainstorming`.
- **Tabla de veredictos completa** — accion explicit por cada uno de los 6 verdicts (STRONG_GO / GO / GO_WITH_CAVEATS / HOLD / HOLD_TIE / STRONG_NO_GO) con fork low-risk vs structural en GO_WITH_CAVEATS. Rationale: §2 §2.3 actualmente solo dice threshold; tabla enumera el pasaje exacto por cada veredicto.

### 4.4 Escenarios Given/When/Then

**Escenario M1: patch artifact es self-contained**

> **Given** un usuario abriendo proyecto MAGI session.
> **When** lee `docs/cross-project/2026-05-01-magi-claude-local-patch.md`.
> **Then** puede aplicar las 5 inserciones sin necesidad de cross-reference a SBTDD's §6 — el patch contiene todo el verbatim text + rationale + insertion location.

**Escenario M2: patch insertions no rompen MAGI's existing flow**

> **Given** MAGI's actual `CLAUDE.local.md` §2 (212 lineas).
> **When** las 5 inserciones se aplican en sus locations indicadas.
> **Then** la seccion §2 resultante es internally consistent: no hay sub-section que contradiga otra; el flow operacional resultante = template's flow operacional (modulo deltas project-specific MAGI).

### 4.5 Acceptance criteria

- **M1**: revision manual del patch confirma self-containment.
- **M2**: walkthrough mental aplica cada insertion sobre MAGI's §2 actual y confirma consistency.

---

## 5. Workflow / execution timeline

### 5.1 Layout (single agent, single session)

| Phase | Duracion estimada | Output |
|-------|-------------------|--------|
| 0. Spec written + self-review + user approval | DONE post-this-spec | esta seccion |
| 1. Write template (`docs/magi-gate-template.md`) | ~30-40min | source-of-truth canonico |
| 2. Diff template vs SBTDD §6 → apply edits to `CLAUDE.local.md` | ~15-20min | local edit applied |
| 3. Diff template vs MAGI §2 (cached at `/tmp/magi-claude-local.md`) → write patch artifact | ~20-30min | `docs/cross-project/2026-05-01-magi-claude-local-patch.md` |
| 4. Self-review (placeholder leakage, contradictions, completeness) | ~10-15min | inline fixes |
| 5. Commit (template + patch artifact) | ~5min | 2 atomic commits, mensajes en ingles per `~/.claude/CLAUDE.md` |
| 6. Push (con autorizacion explicita user) | optional | origin/main |
| **Total wall time** | **~1.5-2h** | -- |

### 5.2 Why single agent (no parallelism)

Deliverables son interdependientes (template = source of truth para los otros dos). Splitting genera mas overhead de coordinacion que ganancia de wall time. Lightweight pattern.

### 5.3 No final review loop

Pure docs scope. NO MAGI gate, NO `/requesting-code-review`, NO Loop 1/Loop 2.
Razon: el MAGI gate template ES el deliverable; correrlo sobre si mismo es
overhead sin senal. Verification es manual review (placeholder grep, internal
consistency, cross-doc walkthrough).

INV-29 NO aplica (no hay diff de codigo). INV-9 NO aplica (no hay pre-merge).
INV-22 NO aplica (no es auto run).

---

## 6. Acceptance criteria final

Spec ship-ready cuando:

### 6.1 Functional

- [ ] **Deliverable 1**: `docs/magi-gate-template.md` contiene 10 sub-sections per layout sec.2.2 + checklist de placeholders sec.2.3.
- [ ] **Deliverable 2**: SBTDD's `CLAUDE.local.md` §6 contiene las 5 nuevas sub-sections per sec.3.2.
- [ ] **Deliverable 3**: `docs/cross-project/2026-05-01-magi-claude-local-patch.md` contiene 5 patch entries per sec.4.3.

### 6.2 Quality

- [ ] **Template self-completeness** (T1): mental walkthrough valida que un proyecto nuevo + filling placeholders obtiene MAGI gate operacional.
- [ ] **Placeholder leakage** (T2): `grep -E '\{[a-z_]+\}' docs/magi-gate-template.md` produce solo placeholders en sec.2.3.
- [ ] **Internal consistency** (T3): cero contradicciones entre las 10 sub-sections del template.
- [ ] **SBTDD §6 absorbed** (S1, S2, S3): re-leer §6 confirma fluidez sin contradicciones; INV-29 / INV-9 preservados.
- [ ] **MAGI patch self-contained** (M1, M2): walkthrough mental confirma que el patch aplica clean sobre MAGI's §2 actual.

### 6.3 Process

- [ ] Commits atomicos siguiendo `~/.claude/CLAUDE.md` Git rules (English, no AI refs, no Co-Authored-By): commit 1 para template + patch artifact, o commits separados (atomicidad por archivo es tambien aceptable).
- [ ] CHANGELOG.md NO requiere entry (este es side-track docs; v0.4.0 sigue siendo last shipped version).
- [ ] `make verify` NO requiere correr (pure docs change; no Python files modified).
- [ ] Push a `origin/main` requiere autorizacion explicita user (per `~/.claude/CLAUDE.md` Git rules).

---

## 7. Risk register

- **R1**. **Template content leakage**: el template podria copiar inadvertidamente parrafo project-specific (e.g., menciones a `auto_cmd.py` o `INV-29`) que no aplica a otros proyectos. Mitigation: explicit grep + review pass para identificar terms project-specific antes de commit.
- **R2**. **Bidirectional sync drift**: si MAGI plugin actualiza su §2 antes de que el patch artifact se aplique, el patch puede quedar stale. Mitigation: aplicar el patch en proyecto MAGI lo antes posible (en proxima MAGI session). Audit trail del patch documenta el state de §2 al momento de generacion (cached en `/tmp/magi-claude-local.md`).
- **R3**. **`STRONG_NO_GO` vs `STRONG NO-GO` naming**: §2 usa space-separated; SBTDD usa underscore-separated (per `models.VERDICT_RANK`). Template y SBTDD's §6 deben usar SBTDD-style (verdict identifiers code-grade); MAGI's CLAUDE.local.md historicamente usa space-separated (human-readable). Mitigation: template documenta que ambas formas refieren al mismo verdict; cada proyecto preserva su convention.
- **R4**. **Carry-forward block syntax overhead**: §2.4.1 prescribe un block formal verbatim — agregar a SBTDD's §6 incrementa peso de la doc por ~80 lineas. Mitigation: aceptable cost — el formato es valioso (reduce loops esteriles MAGI), y SBTDD's §6 ya es larga (sec.6 + sec.7 son las mas grandes).
- **R5**. **Review summary artifact NO genera automaticamente**: spec dice "operador escribe manualmente al cierre del MAGI gate" para v0.5.0+. Risk: si no se genera consistentemente, el audit trail queda parcial. Mitigation: documenta como follow-up backlog item en CHANGELOG Future / v0.5.0+ scope. Adicionalmente, `auto-run.json` ya cubre la dimension machine-readable del audit; el summary artifact es the human-readable complement.

---

## 8. Referencias

- `CLAUDE.local.md` SBTDD §6 "Code review" — source para Loop 1/2 sequencing, degraded handling, mini-ciclo TDD, verdict table, spec replan trigger.
- `CLAUDE.local.md` MAGI plugin §2 (cached at `/tmp/magi-claude-local.md`) — source para trigger criteria, skip rules, threshold high-impact keywords, procedure, carry-forward format §2.4.1, cost awareness §2.5, per-project setup §2.6, review summary artifact.
- `~/.claude/CLAUDE.md` global — top authority per INV-0; commit rules (English, no AI refs, no Co-Authored-By) governing commits del este spec.
- v0.4.0 ship record (`memory/project_v040_shipped.md`) — empirical confirmation de Caspar fragility cronica que justifica cost awareness warning para smaller models.
- v0.5.0 brainstorming state (paused) — task #2 in TaskList; resume despues de este side-track.

---

## 9. Nota sobre siguiente paso

Spec listo. Next step:
1. User review de este spec.
2. Si aprueba: skip `/writing-plans` (pure docs scope no requiere plan TDD multi-agente; workflow sec.5.1 es directo). Proceder directamente a phases 1-5 de sec.5.1.
3. Si quiere `/writing-plans` formal: invocar el skill, pero dado el scope trivial el plan resultante sera basicamente lineal sin TDD cycles.

Mi recomendacion: skip `/writing-plans`, proceder a implementacion directa por simplicidad (4 phases secuenciales claras, single agent).
