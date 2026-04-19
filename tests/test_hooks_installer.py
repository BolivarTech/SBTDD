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


def test_merge_preserves_user_hooks_and_adds_plugin(tmp_path):
    from hooks_installer import merge

    user_settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Write", "hooks": [{"type": "command", "command": "eslint"}]}
            ]
        }
    }
    plugin_hooks = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit|TodoWrite",
                    "hooks": [{"type": "command", "command": "tdd-guard"}],
                }
            ],
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear",
                    "hooks": [{"type": "command", "command": "tdd-guard"}],
                }
            ],
        }
    }
    existing = tmp_path / "settings.json"
    existing.write_text(json.dumps(user_settings))
    target = tmp_path / "settings.json"
    merge(existing_path=existing, plugin_hooks=plugin_hooks, target_path=target)
    result = json.loads(target.read_text())
    # Both user and plugin hooks should be in PreToolUse.
    commands = [h["hooks"][0]["command"] for h in result["hooks"]["PreToolUse"]]
    assert "eslint" in commands
    assert "tdd-guard" in commands
    # SessionStart (plugin-only) should exist.
    assert "SessionStart" in result["hooks"]


def test_merge_cleans_up_tmp_on_os_replace_failure(tmp_path, monkeypatch):
    """tmp file must not leak when os.replace fails (MAGI Loop 2 Finding 6).

    Mirrors the state_file.save fix: on OSError from os.replace, the
    partially-written tmp must be unlinked before re-raising so the
    directory is left clean.
    """
    import os

    from hooks_installer import merge

    plugin_hooks = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Write", "hooks": [{"type": "command", "command": "tdd-guard"}]}
            ]
        }
    }
    target = tmp_path / "settings.json"

    def failing_replace(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", failing_replace)

    try:
        merge(existing_path=target, plugin_hooks=plugin_hooks, target_path=target)
    except OSError:
        pass
    else:
        raise AssertionError("merge should have re-raised the OSError")

    # No leftover *.tmp.* files in tmp_path
    leftovers = list(tmp_path.glob("*.tmp.*"))
    assert leftovers == [], f"merge leaked tmp files: {leftovers}"


def test_merge_is_idempotent(tmp_path):
    """Running merge twice with same inputs produces byte-identical output."""
    from hooks_installer import merge

    plugin_hooks = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Write", "hooks": [{"type": "command", "command": "tdd-guard"}]}
            ]
        }
    }
    target = tmp_path / "settings.json"
    merge(existing_path=target, plugin_hooks=plugin_hooks, target_path=target)
    first = target.read_bytes()
    merge(existing_path=target, plugin_hooks=plugin_hooks, target_path=target)
    second = target.read_bytes()
    assert first == second
