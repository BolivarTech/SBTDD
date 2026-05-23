"""Behavioral test of the SBTDD drift classifier (executable spec of routing §3)."""

PHASE_AFTER = {"test": "green", "feat": "refactor", "fix": "refactor",
               "refactor": "red", "chore": "red"}      # red also covers 'done'
PHASE_CLOSED_BY = {"test": "red", "feat": "green", "fix": "green",
                   "refactor": "refactor", "chore": "task"}


def classify(current_phase, last_prefix):
    if current_phase == "done":
        return "na"                       # plan complete; review commits expected
    if current_phase in (PHASE_AFTER[last_prefix], "done"):
        return "consistent"
    if current_phase == PHASE_CLOSED_BY[last_prefix]:
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
