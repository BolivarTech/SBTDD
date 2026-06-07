---
description: Scaffold a project for the SBTDD workflow — multi-stack, idempotent setup
---

# /sbtdd-init — SBTDD Project Scaffolding

This command initialises a project for the SBTDD workflow. It is **idempotent:
do not overwrite** files that already exist; always report what was
created and what was skipped.

---

## Step 1 — Detect the build stack

Scan the project root for these manifest files:

| File            | Stack  |
|-----------------|--------|
| `Cargo.toml`    | rust   |
| `pyproject.toml` or `setup.py` | python |
| `CMakeLists.txt` | cpp    |

- If exactly one match: proceed with that stack.
- If more than one match or none: **pause and ask the user** which stack
  to configure (AskUserQuestion). Do not guess.

---

## Step 2 — Write `CLAUDE.local.md`

Source template: `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.local.md.tmpl`

Substitutions:
- `{StackVerification}` → contents of
  `${CLAUDE_PLUGIN_ROOT}/templates/verification/<stack>.md`
  (where `<stack>` is `rust`, `python`, or `cpp`)
- §4 stack line → replace the literal `(filled by /sbtdd-init)` on the §4 Stack line with the detected stack (language, test runner, test command).
- `{ErrorType}` → ask the user for their preferred error/exception type
  (or leave `TODO: set ErrorType` if the user skips)
- `{Author}` → ask the user for their name/handle
  (or leave `TODO: set Author` if the user skips)

If `CLAUDE.local.md` already exists: **skip it and report "skipped (already
present)"**. Do not overwrite.

---

## Step 3 — Write / merge `.claude/settings.json`

Source template: `${CLAUDE_PLUGIN_ROOT}/templates/settings.json.tmpl`

### tdd-guard binary pre-check

**Before writing or merging any hooks**, check whether the `tdd-guard` binary
is on PATH:

```powershell
# PowerShell-first
Get-Command tdd-guard -ErrorAction SilentlyContinue
```

```sh
# POSIX fallback
command -v tdd-guard
```

**If `tdd-guard` is NOT found — do NOT write or merge the hooks.** Instead,
stop and tell the user:

> `tdd-guard` is not on PATH. The TDD-Guard hooks have NOT been written.
> Installing a PreToolUse hook that calls a missing binary would lock you out
> of your own project — every Write/Edit would fail closed.
>
> **Install `tdd-guard` first**, then re-run `/sbtdd-init`. The command is
> idempotent and will add the hooks once the binary is present.
>
> See the `tdd-guard` upstream docs for platform-specific install instructions.

Skip the rest of Step 3 (neither writing a new file nor merging into an
existing one). Continue with Step 4.

**If `tdd-guard` IS found**, proceed normally with the steps below.

### If `.claude/settings.json` does not exist

Copy the template verbatim. Create `.claude/` first if absent.

### If `.claude/settings.json` already exists (merge strategy)

1. **Back it up with a non-clobbering filename:**
   - Attempt `.claude/settings.json.bak`.
   - If that file **already exists**, use a timestamped name instead:
     `.claude/settings.json.<timestamp>.bak` (e.g.
     `.claude/settings.json.20260523T143022.bak`).
   - Never overwrite an existing backup.
2. Parse the existing file (`ConvertFrom-Json` on PowerShell; `jq` as
   POSIX fallback).
3. Parse the template to obtain its `hooks` object.
4. **Hook-entry equality rule:** A hook entry is considered already present
   if, under the same event key, an existing entry has the same `matcher`
   value (treat an absent matcher as equal only to another absent matcher)
   AND the same `command` value(s). Append an entry only when no equal
   entry exists; if the event key itself is absent, create it. Never
   duplicate an existing matcher+command pair.
5. For each hook event (`PreToolUse`, `SessionStart`, `UserPromptSubmit`):
   append only hook entries not already present (per rule 4 above).
6. **Never modify any key other than `hooks`** — preserve all other
   settings exactly.
7. **Show the unified diff and the backup path before writing.** Apply
   this decision rule:
   - If the merge would add, modify, or remove **any** key or value other
     than appending new entries to the `hooks` arrays, **STOP** and
     require explicit user confirmation before writing.
   - If the change is purely appending missing hook entries (and nothing
     else), you may write after showing the diff — no additional prompt
     needed.
8. **PowerShell JSON depth:** When re-serializing the merged settings with
   PowerShell, use `ConvertTo-Json -Depth 10` — the default depth of 2
   truncates the nested `hooks` structure and corrupts the file.
   (Alternatively, use `jq` to write.)
9. **Validate after writing:** after writing the file, re-read it and
   parse it (`ConvertFrom-Json` / `json.loads`) to confirm the result is
   valid JSON. If parsing fails, **immediately restore from the backup**
   and report the error — do not leave a corrupted settings file.

The merge is performed by the agent directly; backup + show-diff is the
safety net.

---

## Step 4 — Create working directories

```
sbtdd/
planning/
```

Create both if absent. If already present, skip silently.

---

## Step 5 — Seed `sbtdd/spec-behavior-base.md`

Source template:
`${CLAUDE_PLUGIN_ROOT}/templates/spec-behavior-base.tmpl.md`

Copy to `sbtdd/spec-behavior-base.md` **only if the file does not already
exist**. If it exists, skip and note it in the report.

---

## Step 6 — Update `.gitignore`

Append entries that are not already present in `.gitignore`
(create `.gitignore` if absent).

The checked set consists of these five content entries:

```
CLAUDE.local.md
CLAUDE.md
.claude/
sbtdd/
planning/
```

**Already-tracked warning:** before appending any entry, run
`git ls-files -- <path>` for each of the five entries in the target repo.
If any path is **already tracked** by git, emit a **PROMINENT WARNING**:

> ⚠ WARNING: the following paths are already tracked by git:
>   <list tracked paths>
> Adding them to `.gitignore` will NOT cause git to untrack them — git
> continues to track already-committed files regardless of `.gitignore`.
> Ignoring an already-tracked path is surprising and usually unintended.
> To untrack a path you must run: `git rm --cached <path>`
> **Do you still want to add these entries to `.gitignore`?** (Proceed / Skip
> the already-tracked entries / Abort)

Wait for the user's decision before writing those entries. Entries that are
NOT already tracked may be appended without waiting (subject to the checks
below). Do NOT change which entries are in the checked set.

**Exact-line matching:** when checking whether an entry already exists, match
the **full line exactly** (strip leading/trailing whitespace; also treat a
line with an optional trailing `/` as matching the bare form — e.g. `sbtdd/`
matches `sbtdd`). Do NOT use naive substring matching (e.g., `sbtdd` must
not be considered present just because the file contains `sbtdd-foo/`).
A distinct entry is added only when no full-line match exists for that
pattern.

The comment line `# SBTDD local-only files` is added once only if it is
not already present. Check each of the five content entries individually
and add only the missing ones. Do not duplicate existing entries.

> **If invoked as `/sbtdd-init --ollama-init`:** before the final report, also
> perform the **Optional flag: `--ollama-init`** section below (Ollama MAGI
> backend setup).

---

## Optional flag: `--ollama-init`

When `/sbtdd-init` is invoked as `/sbtdd-init --ollama-init`, then after the
steps above, delegate to MAGI's `--ollama-init` (`/magi --ollama-init`) to
scaffold `./.claude/magi-ollama.toml`. Its presence selects the Ollama backend
for every MAGI invocation in the SBTDD flow — see `review-gates.md §8` (MAGI
Backend Selection).

- **Idempotent:** if `./.claude/magi-ollama.toml` already exists, skip it and
  report "skipped (already present)"; never overwrite.
- `.claude/` is gitignored (Step 6), so the toml (and any API key) is not tracked.
- Requires **MAGI 4.0.1 or newer**; if the installed MAGI is older, report that
  the Ollama backend is unavailable and skip this step.
- Without `--ollama-init`, `/sbtdd-init` does NOT create the toml and the flow
  uses the default Claude backend.

---

## Step 7 — Final report

Print a summary table:

| Item                          | Status          |
|-------------------------------|-----------------|
| `CLAUDE.local.md`             | created / skipped |
| `.claude/settings.json`       | created / merged / skipped |
| `.claude/settings.json.bak`   | created / n/a   |
| `sbtdd/`                      | created / skipped |
| `planning/`                   | created / skipped |
| `sbtdd/spec-behavior-base.md` | created / skipped |
| `.claude/magi-ollama.toml` (with `--ollama-init`) | created / skipped / n/a |
| `.gitignore` entries          | added N / all present |

Then remind the user:

> **Next steps**
> 1. Install the `tdd-guard` binary and ensure it is on `PATH`
>    (see `tdd-guard` upstream docs for platform-specific instructions).
> 2. *(Optional)* Install the stack reporter if you need on-demand
>    test-result sync — the PreToolUse hook enforces the TDD cycle without it:
>    - **Rust:** `cargo install tdd-guard-rust`
>    - **Python:** `pip install tdd-guard-pytest`
>    - **C/C++:** no official reporter; test-result sync is manual.
> 3. Run `/sbtdd-check` to verify the full setup.
