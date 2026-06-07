from conftest import ROOT, frontmatter

CMD = ROOT / "commands"


def test_sbtdd_command_invokes_skill():
    t = (CMD / "sbtdd.md").read_text(encoding="utf-8")
    assert "description:" in frontmatter(t)
    assert "sbtdd" in t.lower() and "skill" in t.lower()


def test_sbtdd_init_covers_all_scaffolding_steps():
    t = (CMD / "sbtdd-init.md").read_text(encoding="utf-8")
    for sig in ("Cargo.toml", "pyproject.toml", "CMakeLists.txt"):
        assert sig in t
    for entry in ("CLAUDE.local.md", "CLAUDE.md", ".claude/", "sbtdd/", "planning/"):
        assert entry in t
    for tmpl in ("CLAUDE.local.md.tmpl", "settings.json.tmpl",
                 "spec-behavior-base.tmpl.md", "verification/"):
        assert tmpl in t
    assert "idempotent" in t.lower() or "do not overwrite" in t.lower()
    assert "merge" in t.lower()
    assert "description:" in frontmatter(t)


def test_sbtdd_check_covers_seven_items():
    t = (CMD / "sbtdd-check.md").read_text(encoding="utf-8")
    assert "CLAUDE.local.md" in t
    assert "PreToolUse" in t and "SessionStart" in t and "UserPromptSubmit" in t
    assert "sbtdd/" in t and "planning/" in t
    assert ".gitignore" in t
    assert "tdd-guard" in t
    assert "drift" in t.lower()
    assert "magi:magi" in t
    assert "superpowers" in t.lower()
    assert "Get-Command" in t
    assert "read-only" in t.lower() or "does not fix" in t.lower()
    assert "sbtdd-init" in t
    assert "description:" in frontmatter(t)


def test_sbtdd_init_documents_ollama_init_flag():
    """--ollama-init must be documented: delegate to MAGI's --ollama-init to
    scaffold ./.claude/magi-ollama.toml (idempotent), point to review-gates §8
    (contiguous literal), and state the MAGI 4.0.1 floor."""
    t = (CMD / "sbtdd-init.md").read_text(encoding="utf-8")
    assert "--ollama-init" in t
    assert "magi-ollama.toml" in t
    assert "/magi --ollama-init" in t
    assert "review-gates.md §8" in t
    assert "4.0.1" in t
    low = t.lower()
    assert "skip" in low or "do not overwrite" in low or "idempotent" in low


def test_sbtdd_command_documents_ollama_flag():
    """/sbtdd --ollama must be documented as the explicit fail-closed Ollama
    form, pointing to review-gates §8 (contiguous literal)."""
    t = (CMD / "sbtdd.md").read_text(encoding="utf-8")
    assert "--ollama" in t
    assert "review-gates.md §8" in t
    low = t.lower()
    assert "fail-closed" in low or "magi-ollama.toml" in low
