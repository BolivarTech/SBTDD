from conftest import ROOT

T = ROOT / "templates/spec-behavior-base.tmpl.md"


def test_spec_base_has_required_sections():
    t = T.read_text(encoding="utf-8")
    for section in ("Objective", "Requirements", "Given", "When", "Then", "Constraints", "Non-goals"):
        assert section in t
