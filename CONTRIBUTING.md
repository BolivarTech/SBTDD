# Contributing to SBTDD Workflow

Thank you for your interest in contributing. This plugin implements a strict methodology (SBTDD) and applies it to its own development -- dogfooding is the point.

## Prerequisites

- Read `~/.claude/CLAUDE.md` first. Its Code Standards have absolute precedence (INV-0) over everything in this repository.
- Read `CLAUDE.md` (project-level) and `CLAUDE.local.md` (project-level local rules).
- Read `sbtdd/sbtdd-workflow-plugin-spec-base.md` -- the authoritative functional contract.

## Branching model

- `main` is the integration branch. Always green (`make verify` clean).
- Feature branches follow `feature/<short-description>` or `fix/<short-description>`.
- No direct commits to `main`. All changes land via PR after `/sbtdd pre-merge` passes.

## Workflow

Every feature is implemented via the full SBTDD cycle:

1. **Spec (sec.1 of `CLAUDE.local.md`).** Draft `sbtdd/spec-behavior-base.md` for the feature. No uppercase placeholder markers (INV-27 -- enumerated in `CLAUDE.local.md`).
2. **Plan.** Run `/sbtdd spec` to drive `/brainstorming` -> `/writing-plans` -> MAGI Checkpoint 2. Iterate until MAGI returns a full (non-degraded) verdict `>= GO_WITH_CAVEATS`.
3. **Execute.** Run `/sbtdd close-phase` at the end of each TDD phase (Red, Green, Refactor), or `/sbtdd auto` for shoot-and-forget execution of the whole plan.
4. **Pre-merge.** Run `/sbtdd pre-merge` -- Loop 1 (automated review) then Loop 2 (MAGI). Both must converge.
5. **Finalize.** Run `/sbtdd finalize` -- the sec.M.7 checklist gate + `/finishing-a-development-branch`.
6. **Open PR.** Link to the approved plan, include the final MAGI verdict summary.

## Commit discipline (sec.M.5 of `CLAUDE.local.md`)

All commits:

- English prose only.
- No `Co-Authored-By` lines.
- No references to Claude, AI, or assistants.
- Atomic -- one commit, one concern, one prefix.

Allowed prefixes:

| Context | Prefix |
|---------|--------|
| Red phase close (test added) | `test:` |
| Green phase close (new feature) | `feat:` |
| Green phase close (bug fix / hardening) | `fix:` |
| Refactor phase close | `refactor:` |
| Task close (mark `[x]` in plan) | `chore:` |
| Documentation-only change | `docs:` |

Mini-cycle fixes during pre-merge Loop 1 or Loop 2 produce three commits each (`test:` -> `fix:` -> `refactor:`), one per finding.

## PR checklist

Before opening a PR:

- [ ] `make verify` clean on the latest commit.
- [ ] `/sbtdd status` reports `current_phase: "done"`.
- [ ] All plan tasks marked `[x]`.
- [ ] `CHANGELOG.md` updated under `## Unreleased` (BREAKING / Added / Changed / Fixed).
- [ ] `/sbtdd pre-merge` converged to a full (non-degraded) verdict `>= GO_WITH_CAVEATS`.
- [ ] No `Co-Authored-By` in any commit.
- [ ] No references to Claude, AI, or assistants in any commit.

## Adding a new invariant

Invariants are numbered `INV-N` and live in `sbtdd/sbtdd-workflow-plugin-spec-base.md sec.S.10`. Adding one:

1. Append the invariant to sec.S.10 with a unique N.
2. Enforce it in the plugin (test-first).
3. Document it in `CLAUDE.md` invariants summary.
4. Reference it in the affected subcommand docstrings.

## Reporting issues

Open a GitHub issue at <https://github.com/BolivarTech/sbtdd-workflow/issues> with:

- Plugin version (`cat .claude-plugin/plugin.json | jq .version`).
- `/sbtdd status` output.
- Relevant lines from `.claude/auto-run.json` (if reproducing an `auto` failure).

## License

By contributing, you agree that your contribution is dual licensed under [MIT](LICENSE) OR [Apache-2.0](LICENSE-APACHE), at the user's option.
