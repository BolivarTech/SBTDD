import pytest


def test_validate_prefix_accepts_known():
    from commits import validate_prefix

    for prefix in ("test", "feat", "fix", "refactor", "chore"):
        validate_prefix(prefix)  # no raise


def test_validate_prefix_rejects_unknown():
    from commits import validate_prefix
    from errors import ValidationError

    with pytest.raises(ValidationError):
        validate_prefix("wip")
