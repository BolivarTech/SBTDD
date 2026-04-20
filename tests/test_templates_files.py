from __future__ import annotations

import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def test_settings_json_template_exists():
    assert (TEMPLATES_DIR / "settings.json.template").exists()


def test_settings_json_template_is_valid_json():
    data = json.loads((TEMPLATES_DIR / "settings.json.template").read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_settings_json_template_has_three_required_hooks():
    data = json.loads((TEMPLATES_DIR / "settings.json.template").read_text(encoding="utf-8"))
    hooks = data.get("hooks", {})
    assert set(hooks.keys()) == {"PreToolUse", "UserPromptSubmit", "SessionStart"}


def test_settings_json_template_pretool_has_write_matcher():
    data = json.loads((TEMPLATES_DIR / "settings.json.template").read_text(encoding="utf-8"))
    pretool = data["hooks"]["PreToolUse"]
    assert len(pretool) >= 1
    entry = pretool[0]
    assert entry["matcher"] == "Write|Edit|MultiEdit|TodoWrite"
    assert entry["hooks"][0]["command"] == "tdd-guard"


def test_settings_json_template_session_start_has_startup_matcher():
    data = json.loads((TEMPLATES_DIR / "settings.json.template").read_text(encoding="utf-8"))
    session = data["hooks"]["SessionStart"]
    assert session[0]["matcher"] == "startup|resume|clear"
    assert session[0]["hooks"][0]["command"] == "tdd-guard"


def test_settings_json_template_user_prompt_has_tdd_guard():
    data = json.loads((TEMPLATES_DIR / "settings.json.template").read_text(encoding="utf-8"))
    ups = data["hooks"]["UserPromptSubmit"]
    assert ups[0]["hooks"][0]["command"] == "tdd-guard"
