"""Shared paths and helpers for the plugin structural-validation suite."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    """Return the text of a repo-relative file (UTF-8)."""
    return (ROOT / rel).read_text(encoding="utf-8")


def frontmatter(text: str) -> str:
    """Return the YAML frontmatter block (between the first two '---' lines)."""
    assert text.startswith("---"), "file must start with YAML frontmatter"
    end = text.index("\n---", 3)
    return text[3:end]
