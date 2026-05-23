---
description: Read-only SBTDD setup verifier — diagnoses the full configuration and reports pass/fail per item
---

# /sbtdd-check — SBTDD Setup Verifier

**This command is read-only. It diagnoses; it does not fix.**
For any failing item, the remediation is to run `/sbtdd-init`.

Run all seven checks below in order. For each check report `PASS`,
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

## Check 2 — Three TDD-Guard hooks active

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

Verify that **all three** of the following hook events are present and
each has a `tdd-guard` command entry:

- `PreToolUse`
- `SessionStart`
- `UserPromptSubmit`

**FAIL remediation:** run `/sbtdd-init` — it will merge the missing hooks
into `.claude/settings.json` (backing up the existing file first).

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
Get-Command sbtdd-reporter -ErrorAction SilentlyContinue
```

POSIX fallback:

```sh
command -v tdd-guard
command -v sbtdd-reporter
```

Report whether each binary is found or missing.

**FAIL remediation:** install `tdd-guard` for your platform and the
stack-specific `sbtdd-reporter` (see `/sbtdd-init` output for install
commands).

---

## Check 6 — State-file consistency / drift check

If `.claude/session-state.json` is absent, report `N/A (no session state
yet)` — this is not a failure.

If the file is present, perform a light drift check inline:

- Read `current_phase` from `.claude/session-state.json`.
- Read the prefix of the last git commit message (e.g. `test:`, `feat:`,
  `fix:`, `refactor:`).
- If the phase implied by the commit prefix does not match `current_phase`
  (for example, the state file says `green` but the last commit is
  `refactor:`), report `FAIL — drift detected: state=<phase>,
  last_commit=<prefix>`.
- If they are consistent, report `PASS`.

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

If **any check fails**, end with:

> One or more checks failed. Run `/sbtdd-init` to repair the setup,
> then re-run `/sbtdd-check`.

If **all pass**, end with:

> All checks passed. Run `/sbtdd` to start or resume the workflow.
