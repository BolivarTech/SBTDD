from conftest import ROOT, frontmatter

CMD = ROOT / "commands"


def test_sbtdd_command_invokes_skill():
    t = (CMD / "sbtdd.md").read_text(encoding="utf-8")
    assert "description:" in frontmatter(t)
    assert "sbtdd" in t.lower() and "skill" in t.lower()
