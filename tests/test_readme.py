from conftest import ROOT


def test_readme_documents_entrypoints():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    for cmd in ("/sbtdd", "/sbtdd-init", "/sbtdd-check"):
        assert cmd in t
    assert "SBTDD" in t
    # documents the install-then-init-then-run flow
    assert "install" in t.lower()
    # documents runtime dependencies + the gitignore trade-off (MAGI caveats)
    assert "superpowers" in t.lower() and "magi" in t.lower()
    assert "gitignore" in t.lower()
