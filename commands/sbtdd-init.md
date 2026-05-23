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
- §4 stack line → replace the placeholder with the detected stack name
- `{ErrorType}` → ask the user for their preferred error/exception type
  (or leave `TODO: set ErrorType` if the user skips)
- `{Author}` → ask the user for their name/handle
  (or leave `TODO: set Author` if the user skips)

If `CLAUDE.local.md` already exists: **skip it and report "skipped (already
present)"**. Do not overwrite.

---

## Step 3 — Write / merge `.claude/settings.json`

Source template: `${CLAUDE_PLUGIN_ROOT}/templates/settings.json.tmpl`

### If `.claude/settings.json` does not exist

Copy the template verbatim. Create `.claude/` first if absent.

### If `.claude/settings.json` already exists (merge strategy)

1. **Back it up** to `.claude/settings.json.bak` before any modification.
2. Parse the existing file (`ConvertFrom-Json` on PowerShell; `jq` as
   POSIX fallback).
3. Parse the template to obtain its `hooks` object.
4. For each hook event (`PreToolUse`, `SessionStart`, `UserPromptSubmit`):
   append only hook entries **not already present** in the existing file.
5. **Never modify any key other than `hooks`** — preserve all other
   settings exactly.
6. **Show the unified diff and the backup path** before writing. Wait for
   implicit approval (the agent writes after showing — no extra prompt
   unless the diff is destructive).

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

Append the following entries if not already present in `.gitignore`
(create `.gitignore` if absent):

```
# SBTDD local-only files
CLAUDE.local.md
CLAUDE.md
.claude/
sbtdd/
planning/
```

Check each line individually — add only the missing ones. Do not
duplicate existing entries.

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
| `.gitignore` entries          | added N / all present |

Then remind the user:

> **Next steps**
> 1. Install the `tdd-guard` binary and ensure it is on `PATH`.
> 2. Install the stack reporter for your stack
>    (`cargo install sbtdd-reporter` / `pip install sbtdd-reporter` /
>    build from source for C++).
> 3. Run `/sbtdd-check` to verify the full setup.
