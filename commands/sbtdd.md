---
description: Drive or resume the SBTDD workflow — routes by project state to the next phase
---

Use the `sbtdd` skill (via the Skill tool) to inspect the current project state
(`sbtdd/`, `planning/`, `.claude/session-state.json`) and execute the next SBTDD
phase. Do not duplicate the skill's logic here — invoke it.

Note: the skill may be exposed by the harness under a namespaced identifier
(e.g. `sbtdd:sbtdd`). Invoke whichever `sbtdd` skill the harness exposes.
