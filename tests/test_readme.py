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


def test_readme_points_to_magi_interactive_only_contract():
    """README.md must carry an 'interactive-only' pointer next to any MAGI
    mention so a maintainer reading the entry-level README (not just
    SKILL.md) encounters the invocation contract before building a
    headless dispatcher. The pointer must reference review-gates.md so
    the reader can locate §7."""
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    low = t.lower()
    assert "interactive-only" in low, \
        "README.md must mention 'interactive-only'"
    assert "review-gates.md" in t, \
        "README.md must reference review-gates.md"


def test_readme_documents_ollama_backend():
    """README.md must document the Ollama MAGI backend feature: both flags,
    the toml-presence selection signal, and the §8 contract pointer."""
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "--ollama-init" in t, "README must document /sbtdd-init --ollama-init"
    assert "--ollama" in t, "README must document /sbtdd --ollama"
    assert "magi-ollama.toml" in t, "README must name the backend-selection file"
    low = t.lower()
    assert "ollama" in low and "§8" in t, "README must point to review-gates §8 for the backend"


def test_readme_documents_sbtdd_check_reports_backend():
    """README.md must document that /sbtdd-check reports/verifies the active MAGI
    backend (Check 8) — including the Ollama smoke test — so the verifier's new
    capability is discoverable from the entry-level README."""
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "/sbtdd-check" in t
    low = t.lower()
    assert "smoke" in low, "README must mention the /sbtdd-check Ollama smoke test (Check 8)"
