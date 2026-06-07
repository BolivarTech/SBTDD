---
description: Drive or resume the SBTDD workflow — routes by project state to the next phase
---

Use the `sbtdd` skill (via the Skill tool) to inspect the current project state
(`sbtdd/`, `planning/`, `.claude/session-state.json`) and execute the next SBTDD
phase. Do not duplicate the skill's logic here — invoke it.

Note: the skill may be exposed by the harness under a namespaced identifier
(e.g. `sbtdd:sbtdd`). Invoke whichever `sbtdd` skill the harness exposes.

## Flag: `--ollama`

`/sbtdd --ollama` runs or resumes the flow on the Ollama MAGI backend. The
backend is resolved by the presence of `./.claude/magi-ollama.toml` (see
`review-gates.md §8` — MAGI Backend Selection); `--ollama` is the explicit,
**fail-closed** form: if that file does not exist, the orchestrator stops and
tells you to run `/sbtdd-init --ollama-init` first — it does not fall back to the
Claude backend silently. `/sbtdd` without the flag still uses Ollama when the
toml exists.
