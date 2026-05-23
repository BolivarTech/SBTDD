import json
from conftest import ROOT


def _manifest():
    return json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))


def test_manifest_is_valid_json_with_required_fields():
    m = _manifest()
    assert m["name"] == "sbtdd"
    assert m["version"]
    assert "SBTDD" in m["description"]


def test_manifest_lists_expected_keywords():
    m = _manifest()
    assert {"sbtdd", "tdd", "workflow"} <= set(m.get("keywords", []))
