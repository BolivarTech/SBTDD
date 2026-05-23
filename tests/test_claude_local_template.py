from conftest import ROOT

T = ROOT / "templates/CLAUDE.local.md.tmpl"


def _txt():
    return T.read_text(encoding="utf-8")


def test_template_exists_and_is_english():
    t = _txt()
    assert "Mandatory Code Standards" in t  # §0 heading (English)
    assert "Commit" in t                    # §5


def test_keeps_rules_sections_only():
    t = _txt()
    assert "session-state.json" in t        # §2 state schema
    assert "tdd-guard" in t                  # §4 stack/hooks reference
    assert "Co-Authored-By" in t             # §5 commit prohibition


def test_tracking_override_applied():
    t = _txt()
    assert "planning/" in t and "gitignored" in t
    assert "team coordination" not in t.lower() or "developer-local" in t.lower()


def test_has_stack_and_errortype_placeholders():
    t = _txt()
    assert "{ErrorType}" in t
    assert "{Author}" in t
    assert "{StackVerification}" in t
