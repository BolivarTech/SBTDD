import json


def test_read_existing_settings_returns_dict(tmp_path):
    from hooks_installer import read_existing

    target = tmp_path / "settings.json"
    target.write_text(json.dumps({"hooks": {"PreToolUse": []}}))
    result = read_existing(target)
    assert result == {"hooks": {"PreToolUse": []}}


def test_read_missing_returns_empty_dict(tmp_path):
    from hooks_installer import read_existing

    missing = tmp_path / "missing.json"
    assert read_existing(missing) == {}
