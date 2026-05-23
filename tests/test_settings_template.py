import json
from conftest import ROOT


def _settings():
    raw = (ROOT / "templates/settings.json.tmpl").read_text(encoding="utf-8")
    return json.loads(raw)


def test_settings_template_is_valid_json():
    assert "hooks" in _settings()


def test_settings_template_has_three_tdd_guard_hooks():
    hooks = _settings()["hooks"]
    assert {"PreToolUse", "SessionStart", "UserPromptSubmit"} <= set(hooks)
    cmds = [
        h["command"]
        for event in hooks.values()
        for group in event
        for h in group["hooks"]
    ]
    assert cmds and all(c == "tdd-guard" for c in cmds)


def test_pretooluse_matcher_covers_write_edit():
    matcher = _settings()["hooks"]["PreToolUse"][0]["matcher"]
    for tool in ("Write", "Edit", "MultiEdit", "TodoWrite"):
        assert tool in matcher
