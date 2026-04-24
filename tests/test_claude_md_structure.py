# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-24
"""Structural tests for CLAUDE.md release-notes archival convention.

Tripwire: once v0.2 blockers shipped, the three
``## v0.2 requirement (LOCKED) -- ...`` sections are archived to
``CHANGELOG.md [0.2.0]`` and collapsed to a single ``## v0.2 release notes``
pointer. These tests pin that transition and flag regressions that
reintroduce a blocker heading under the archived label.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


def test_v02_locked_blocker_sections_stripped() -> None:
    """CLAUDE.md must contain zero ``## v0.2 requirement (LOCKED)`` headings
    once v0.2 ships -- the shipped blockers live in ``CHANGELOG.md [0.2.0]``
    after archival.
    """
    text = CLAUDE_MD.read_text(encoding="utf-8")
    matches = re.findall(
        r"^## v0\.2 requirement \(LOCKED\)",
        text,
        re.MULTILINE,
    )
    assert matches == [], (
        f"CLAUDE.md still contains {len(matches)} shipped v0.2 blocker "
        f"heading(s); expected zero after archival to CHANGELOG."
    )


def test_v02_release_notes_section_points_to_changelog() -> None:
    """CLAUDE.md must expose a ``## v0.2 release notes`` heading whose body
    references ``CHANGELOG.md`` (the archival target for shipped v0.2 blockers).
    """
    text = CLAUDE_MD.read_text(encoding="utf-8")
    anchor = "## v0.2 release notes"
    assert anchor in text, f"CLAUDE.md must contain '{anchor}' heading pointing at CHANGELOG"
    after_anchor = text.split(anchor, 1)[1]
    section_body = re.split(
        r"^## ",
        after_anchor,
        maxsplit=1,
        flags=re.MULTILINE,
    )[0]
    assert "CHANGELOG.md" in section_body, "v0.2 release notes section must reference CHANGELOG.md"
