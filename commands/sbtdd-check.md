---
description: Read-only SBTDD setup verifier — diagnoses the full configuration and reports pass/fail per item
---

# /sbtdd-check — SBTDD Setup Verifier

**This command is read-only. It diagnoses; it does not fix.**
For any failing item, the remediation is to run `/sbtdd-init`.

Run all eight checks below in order. For each check report `PASS`,
`FAIL <reason>`, or `N/A <reason>` (where applicable) with a one-line
remediation hint. Check 6 may legitimately report `N/A` when no session
state file exists yet.

---

## Check 1 — `CLAUDE.local.md` present with rule sections

- Verify that `CLAUDE.local.md` exists in the project root.
- Open it and confirm it contains at least the headings for the
  mandatory rule sections (TDD cycle, verification, stack).

**FAIL remediation:** run `/sbtdd-init` to generate it from the template.

---

## Check 2 — TDD-Guard hooks consistent with binary availability

Parse `.claude/settings.json` (run from the project root, or resolve the
path relative to the project root):

```powershell
# PowerShell-first
$cfg = Get-Content .claude/settings.json | ConvertFrom-Json
$cfg.hooks
```

POSIX fallback (no hard dependency on `jq`/`which`, but use if available):

```sh
# fallback
jq '.hooks' .claude/settings.json
```

Evaluate the combination of hook presence and binary availability:

| Hooks present | `tdd-guard` on PATH | Result |
|---------------|---------------------|--------|
| Yes (all 3)   | Yes                 | **PASS** |
| No hooks      | No binary           | **NOTE** — not yet enabled (consistent). Run `/sbtdd-init` after installing `tdd-guard`. |
| No hooks      | Binary present      | **FAIL** — hooks missing; run `/sbtdd-init` to add them. |
| Hooks present | Binary absent       | **FAIL** — fail-closed risk: every Write/Edit will be blocked. Remove the hooks or install `tdd-guard`. |

The three required hook events (when hooks are present) are:

- `PreToolUse`
- `SessionStart`
- `UserPromptSubmit`

**FAIL remediation (missing hooks, binary present):** run `/sbtdd-init` — it
will merge the missing hooks into `.claude/settings.json` (backing up the
existing file first).

**FAIL remediation (hooks present, binary absent):** install `tdd-guard` per
its upstream docs, then run `/sbtdd-check` again to confirm PASS.

---

## Check 3 — Working directories exist

Verify that both `sbtdd/` and `planning/` exist in the project root.

**FAIL remediation:** run `/sbtdd-init` to create them.

---

## Check 4 — `.gitignore` contains the five local-only entries

Check that `.gitignore` includes all five of:

```
CLAUDE.local.md
CLAUDE.md
.claude/
sbtdd/
planning/
```

Report which specific entries are missing.

**FAIL remediation:** run `/sbtdd-init` to append the missing lines.

---

## Check 5 — `tdd-guard` binary and stack reporter on PATH

```powershell
# PowerShell-first
Get-Command tdd-guard -ErrorAction SilentlyContinue
```

POSIX fallback:

```sh
command -v tdd-guard
```

Check whether `tdd-guard` is on PATH and report found or missing.

**Stack reporter (optional, on-demand):** the reporter only syncs test output
on demand — the `tdd-guard` PreToolUse hook enforces the TDD cycle directly
via the `tdd-guard` binary without a reporter. The reporter is NOT required for
enforcement. If you want to sync test results, install the appropriate reporter:

- **Rust:** `cargo install tdd-guard-rust`
- **Python:** `pip install tdd-guard-pytest`
- **C/C++:** no official C/C++ reporter; the PreToolUse hook still enforces;
  test-result sync is manual.

**FAIL remediation:** install the `tdd-guard` binary per its upstream docs
(external to this plugin). The stack reporter is optional — install only if
you need on-demand test-result sync.

---

## Check 6 — State-file consistency / drift check

If `.claude/session-state.json` is absent, report `N/A (no session state
yet)` — this is not a failure.

If the file is present, perform a light drift check inline using the
canonical mapping (`current_phase` is set to the phase to work on NEXT
after a phase closes):

| Last phase-closing commit prefix | `current_phase` SHOULD be |
|----------------------------------|---------------------------|
| `test:`                          | `green`                   |
| `feat:` or `fix:`                | `refactor`                |
| `refactor:`                      | `red` or `done`           |
| `chore:` matching `mark task <id> complete` | `red` or `done` |

Steps:
- Read `current_phase` from `.claude/session-state.json`.
- If `current_phase == "done"`: report `N/A — plan complete; pre-merge review
  commits (test:/fix:/refactor:) are expected and not drift`. Stop here.
- Read the prefix of the last git commit message (e.g. `test:`, `feat:`,
  `fix:`, `refactor:`).
- Classify the (current_phase, last_commit) pair in order:
  1. **Consistent** — `current_phase` matches the phase implied by the last
     phase-closing commit per the table (e.g., state `green` + last commit
     `test:`). Report `PASS`.
  2. **Recoverable lag** — `current_phase` matches the phase that was *closed
     by* the last commit (e.g., state `red` + last commit `test:` — the commit
     landed but the state was not advanced yet). Report
     `NOTE — recoverable lag: state=<phase>, last_commit=<prefix>. Complete
     the state update and confirm with the user before resuming.` This is NOT
     a hard failure.
  3. **DRIFT** — neither of the above (e.g., state says `green` but last
     commit is `refactor:`, or state says `refactor` but last commit is
     `test:`). Report `FAIL — drift detected: state=<phase>,
     last_commit=<prefix>`.
  4. **Unrecognised prefix — escalate** — the last commit prefix is not one
     of `test:` / `feat:` / `fix:` / `refactor:` / `chore:` (e.g. `docs:`,
     a merge commit, or no commits yet in the repo), OR the prefix is
     `chore:` but the message does NOT match `mark task <id> complete`
     (i.e. it is a maintenance chore, not a task-close). Report
     `NOTE — unrecognised or absent last-commit prefix (<prefix>); stop and
     ask the user before assuming any phase. Do not attempt to classify.`
     Never assume a phase from an unrecognised prefix.

For deeper drift analysis, refer to
`${CLAUDE_PLUGIN_ROOT}/skills/sbtdd/references/routing.md` (this file
lives in the plugin, not the target project; it may be absent in older
installs — treat a missing file as N/A for the deep check only).

**FAIL remediation:** review `.claude/session-state.json` manually or
run `/sbtdd` to let the orchestrator re-evaluate the phase.

---

## Check 7 — Delegated skills and plugins available

Verify that the following skills/plugins are installed and reachable by
the harness:

**superpowers suite** (check that `superpowers` skills are available):
- `superpowers:test-driven-development`
- `superpowers:systematic-debugging`
- `superpowers:verification-before-completion`
- `superpowers:writing-plans`
- `superpowers:requesting-code-review`

**magi plugin**:
- `magi:magi`

**Fail loud** — list every missing skill/plugin explicitly. Example
failure output:

```
FAIL Check 7 — missing skills:
  - magi:magi  (install the magi plugin)
  - superpowers:test-driven-development  (install the superpowers plugin)
```

**FAIL remediation:** install the missing plugins via your Claude Code
plugin manager and restart the harness.

---

## Check 8 — Active MAGI backend (and Ollama smoke test)

Report which MAGI backend the SBTDD flow will use, and — when the Ollama
backend is selected — verify it actually works end-to-end. The backend is
resolved by the presence of `./.claude/magi-ollama.toml`; the normative rule
lives in `${CLAUDE_PLUGIN_ROOT}/skills/sbtdd/references/review-gates.md §8`
(MAGI Backend Selection). **This check points there; it does not restate the rule.**

| `./.claude/magi-ollama.toml` | Active backend | Check 8 action |
|------------------------------|----------------|----------------|
| **absent** | **Claude** (default) | Report `PASS` — "Claude backend (default); no Ollama config to verify." No smoke test runs. (To use Ollama instead, run `/sbtdd-init --ollama-init`.) |
| **present** | **Ollama** | Run the smoke test below. |

### Ollama smoke test (only when the toml exists)

Verify the Ollama backend is operational by running the **real** MAGI pipeline
once on a throwaway input. Invoke the **interactive** `magi:magi` skill with the
`--ollama` flag, the **positional** mode `analysis`, and a one-line trivial
input — i.e. `/magi --ollama analysis "Reply OK."` (the mode is a positional
argument, not a `--mode` flag). This is the interactive skill, **not** a
`claude -p` subprocess and **not** a direct `run_magi.py` subprocess — it
satisfies the interactive-only contract (`review-gates.md §7`). It delegates all
deep validation (daemon reachability, `ollama signin`, trio-model presence, and
the MAGI ≥ 4.0.1 floor) to MAGI's own `--ollama` preflight.

**Non-interactive contexts:** the smoke test needs an interactive session to
invoke the `magi:magi` skill. In a headless / CI context where the skill cannot
be invoked, Check 8 reports the smoke test **cannot run** (the
`magi:magi`-unavailable branch below) — it never falls back to a headless
`claude -p` or `run_magi.py` subprocess. To run the verifier there without that
result, remove `./.claude/magi-ollama.toml` (Check 8 then reports the Claude
backend and runs no smoke test).

**Time-bounded:** the smoke test cannot hang indefinitely — MAGI's preflight
applies a short reachability timeout (~10s) and each mage runs under a per-agent
timeout, so an unreachable or wedged backend surfaces as a **preflight FAIL**
within seconds rather than blocking the verifier.

**Privacy:** by design the smoke test's input is the literal throwaway string
(e.g. `Reply OK.`), sent to the configured Ollama backend — which may be a
**cloud** endpoint. Check 8 passes no project files or repository contents to the
smoke test; the trio sees only that throwaway string. (MAGI's and Ollama's own
logging of that request is outside this plugin's control.)

**Cost:** the smoke test runs the MAGI trio on every `/sbtdd-check`. If the
configured Ollama backend is a **cloud-billed** endpoint, each run incurs that
cost. To disable the smoke test, remove `./.claude/magi-ollama.toml` — Check 8
then reports the Claude backend and runs no smoke test.

**Classify the result (explicit, reviewable):**

- **`magi:magi` unavailable** (Check 7 failed) → `FAIL` — "cannot smoke-test:
  `magi:magi` unavailable (see Check 7)." The smoke test cannot run.
- **The run aborts in MAGI's `--ollama` preflight** — the output names a
  reachability / auth / model-presence failure (e.g. "Cannot reach Ollama",
  "Auth failed", "Missing models", `OllamaPreflightError`), or `magi:magi`
  reports `--ollama` is unknown (MAGI older than 4.0.1) → `FAIL`. Surface MAGI's
  exact message plus the remediation hint: start the daemon / `ollama signin` /
  `ollama pull <model>` / upgrade MAGI to 4.0.1+.
- **MAGI renders its VERDICT banner / the trio completes** → `PASS` — "Ollama
  backend active and operational." The GO/NO-GO verdict on the throwaway prompt
  is irrelevant; Check 8 only cares that the pipeline ran (config resolved →
  preflight passed → trio executed).

The MAGI ≥ 4.0.1 floor is **subsumed** by the smoke test: an older MAGI has no
`--ollama` flag, so the run fails with that error — no separate version probe.
The smoke test **always runs** when the toml exists (no skip flag); the verifier
authoritatively confirms the backend on every run.

**FAIL remediation:** fix the Ollama backend per MAGI's reported error (start the
daemon, `ollama signin`, pull the configured trio, or upgrade MAGI), then re-run
`/sbtdd-check`. To switch to the Claude backend instead, remove
`./.claude/magi-ollama.toml` (its absence resolves to Claude).

---

## Summary output

After all checks, print a summary table:

| # | Check                              | Result |
|---|------------------------------------|--------|
| 1 | `CLAUDE.local.md` present          | PASS / FAIL |
| 2 | TDD-Guard hooks (PreToolUse, SessionStart, UserPromptSubmit) | PASS / FAIL |
| 3 | `sbtdd/` and `planning/` exist     | PASS / FAIL |
| 4 | `.gitignore` entries               | PASS / FAIL |
| 5 | `tdd-guard` + stack reporter on PATH | PASS / FAIL |
| 6 | State-file drift check             | PASS / FAIL / N/A |
| 7 | superpowers + magi:magi available  | PASS / FAIL |
| 8 | Active MAGI backend (Claude / Ollama + smoke test) | PASS / FAIL |

If **any check fails**, end with:

> One or more checks failed. Run `/sbtdd-init` to repair the setup,
> then re-run `/sbtdd-check`.

If **all pass**, end with:

> All checks passed. Run `/sbtdd` to start or resume the workflow.
