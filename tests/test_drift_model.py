"""Executable spec mirror of the SBTDD routing drift rules (routing.md §3).

This module is an executable spec mirror of the drift-classification rules
documented in ``skills/sbtdd/references/routing.md`` §3 and
``templates/CLAUDE.local.md.tmpl`` §2.1.  It documents and guards the
*intended* classification behaviour; it does NOT execute the agent's runtime
behaviour.  Any change to the routing rules must be reflected here first
(Red step of TDD).
"""

PHASE_AFTER = {"test": "green", "feat": "refactor", "fix": "refactor",
               "refactor": "red", "chore": "red"}      # red also covers 'done'
PHASE_CLOSED_BY = {"test": "red", "feat": "green", "fix": "green",
                   "refactor": "refactor", "chore": "task"}


def classify(current_phase, last_prefix, *, chore_is_task_close: bool = True):
    """Classify the drift state between the session state and the last commit.

    Args:
        current_phase: Value of ``current_phase`` from session-state.json.
            One of ``"red"``, ``"green"``, ``"refactor"``, ``"done"``.
        last_prefix: Prefix of the last git commit (e.g. ``"test"``,
            ``"feat"``, ``"fix"``, ``"refactor"``, ``"chore"``).
            Any unrecognised or absent value returns ``"escalate"``.
        chore_is_task_close: When ``True`` (default), a ``chore:`` commit is
            treated as a task-close signal only when its message matches
            ``mark task <id> complete``.  When ``False``, any ``chore:`` commit
            that is NOT a task-close (i.e. a maintenance chore) is treated as
            an unrecognised prefix and returns ``"escalate"``.

    Returns:
        One of:
        - ``"na"``         — plan complete; post-done review commits expected.
        - ``"consistent"`` — state matches phase implied by last commit.
        - ``"lag"``        — commit landed but state update was interrupted.
        - ``"drift"``      — unrecoverable mismatch; abort and escalate.
        - ``"escalate"``   — last_prefix is unrecognised or absent, or is a
                             non-task-close ``chore:``; stop and ask the user
                             before assuming any phase.
    """
    if current_phase == "done":
        return "na"                       # plan complete; review commits expected
    if last_prefix == "chore" and not chore_is_task_close:
        return "escalate"                 # maintenance chore — not a task-close signal
    phase_next = PHASE_AFTER.get(last_prefix)
    if phase_next is None:
        return "escalate"                 # unknown prefix — stop and ask
    if current_phase in (phase_next, "done"):
        return "consistent"
    if current_phase == PHASE_CLOSED_BY.get(last_prefix):
        return "lag"                      # commit landed, state update interrupted
    return "drift"


def test_consistent_pairs():
    assert classify("green", "test") == "consistent"
    assert classify("refactor", "feat") == "consistent"
    assert classify("refactor", "fix") == "consistent"
    assert classify("red", "chore") == "consistent"


def test_drift_pairs():
    assert classify("green", "refactor") == "drift"
    assert classify("refactor", "test") == "drift"


def test_lag_is_recoverable_not_drift():
    assert classify("red", "test") == "lag"     # red closed, not yet advanced to green
    assert classify("green", "feat") == "lag"   # green closed, not yet advanced to refactor


def test_done_is_na_under_review_commits():
    for p in ("test", "fix", "refactor"):
        assert classify("done", p) == "na"


def test_unknown_prefix_returns_escalate_without_raising():
    """Unrecognised or absent last-commit prefix must escalate, never crash."""
    unknown_prefixes = ("docs", "ci", "build", "merge", "", "wip", None)
    for prefix in unknown_prefixes:
        result = classify("green", prefix)
        assert result == "escalate", (
            f"Expected 'escalate' for prefix={prefix!r}, got {result!r}"
        )


def test_generic_chore_escalates_when_not_task_close():
    """A maintenance chore: (not 'mark task <id> complete') must escalate."""
    result = classify("red", "chore", chore_is_task_close=False)
    assert result == "escalate", (
        f"Expected 'escalate' for generic chore, got {result!r}"
    )


def test_task_close_chore_classifies_as_before():
    """A task-close chore: still classifies normally (consistent or lag)."""
    # chore_is_task_close=True is the default; explicit here for clarity
    assert classify("red", "chore", chore_is_task_close=True) == "consistent"
    assert classify("red", "chore") == "consistent"
