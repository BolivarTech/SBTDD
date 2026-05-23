from conftest import ROOT


def test_repo_root_resolves():
    assert (ROOT / ".git").is_dir()


def test_design_doc_committed():
    spec = ROOT / "docs/superpowers/specs/2026-05-23-sbtdd-orchestrator-plugin-design.md"
    assert spec.is_file()
