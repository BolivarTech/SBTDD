"""Shared paths and helpers for the plugin structural-validation suite."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    """Return the text of a repo-relative file (UTF-8)."""
    return (ROOT / rel).read_text(encoding="utf-8")


def frontmatter(text: str) -> str:
    """Return the YAML frontmatter block (between the first two '---' lines).

    Args:
        text: Full file contents, must begin with '---'.

    Returns:
        The YAML content between the opening and closing '---' fences.

    Raises:
        AssertionError: If the text does not start with a frontmatter fence.
        ValueError: If there is no closing '---' fence.
    """
    assert text.startswith("---"), "file must start with YAML frontmatter"
    try:
        end = text.index("\n---", 3)
    except ValueError:
        raise ValueError("no closing frontmatter fence")
    return text[3:end]
