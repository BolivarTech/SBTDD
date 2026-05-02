#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-05-02
"""Unit tests for v1.0.0 Feature H option 2 spec-snapshot (sec.3.2)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_h2_1_emit_snapshot_extracts_scenario_hashes(tmp_path: Path) -> None:
    """H2-1: emit_snapshot returns {scenario_title: hash} per scenario."""
    from spec_snapshot import emit_snapshot

    spec = tmp_path / "spec-behavior.md"
    spec.write_text(
        """# BDD overlay

## §4 Escenarios BDD

**Escenario S1: parser handles empty input**

> **Given** empty input
> **When** parse() is called
> **Then** returns []

**Escenario S2: parser handles whitespace**

> **Given** whitespace input
> **When** parse() is called
> **Then** returns []
""",
        encoding="utf-8",
    )

    snapshot = emit_snapshot(spec)
    assert isinstance(snapshot, dict)
    assert len(snapshot) >= 2
    titles = list(snapshot.keys())
    # Title extraction tolerates any of the three forms allowed by the regex.
    assert any("S1" in t for t in titles)
    assert any("S2" in t for t in titles)


def test_h2_1_hash_deterministic_for_same_content(tmp_path: Path) -> None:
    """H2-1: same scenario content yields same hash on multiple emits."""
    from spec_snapshot import emit_snapshot

    spec_text = """# BDD overlay

## §4 Escenarios BDD

**Escenario S1: empty input**

> **Given** x
> **When** y
> **Then** z
"""
    spec1 = tmp_path / "s1.md"
    spec1.write_text(spec_text, encoding="utf-8")
    spec2 = tmp_path / "s2.md"
    spec2.write_text(spec_text, encoding="utf-8")

    snap1 = emit_snapshot(spec1)
    snap2 = emit_snapshot(spec2)
    assert snap1 == snap2


def test_h2_1_hash_different_when_body_changes(tmp_path: Path) -> None:
    """H2-1: changing Given/When/Then text changes the hash."""
    from spec_snapshot import emit_snapshot

    spec_a = tmp_path / "a.md"
    spec_a.write_text(
        """# spec

## §4 Escenarios BDD

**Escenario S1: empty input**

> **Given** x
> **When** y
> **Then** z
""",
        encoding="utf-8",
    )
    spec_b = tmp_path / "b.md"
    spec_b.write_text(
        """# spec

## §4 Escenarios BDD

**Escenario S1: empty input**

> **Given** DIFFERENT
> **When** y
> **Then** z
""",
        encoding="utf-8",
    )

    snap_a = emit_snapshot(spec_a)
    snap_b = emit_snapshot(spec_b)
    assert snap_a != snap_b
    # Same title key on both sides: the hash difference is the only delta.
    assert set(snap_a.keys()) == set(snap_b.keys())


def test_h2_1_whitespace_normalization_preserves_hash(tmp_path: Path) -> None:
    """H2-1: trivial whitespace changes don't perturb the hash."""
    from spec_snapshot import emit_snapshot

    spec_a = tmp_path / "a.md"
    spec_a.write_text(
        """# spec

## §4 Escenarios BDD

**Escenario S1: input**

> **Given** x
> **When** y
> **Then** z
""",
        encoding="utf-8",
    )
    spec_b = tmp_path / "b.md"
    # Same content with extra spaces and blank lines; normalization strips it.
    spec_b.write_text(
        """# spec

## §4 Escenarios BDD

**Escenario S1: input**


>    **Given**     x
>    **When**    y
>    **Then**     z
""",
        encoding="utf-8",
    )

    snap_a = emit_snapshot(spec_a)
    snap_b = emit_snapshot(spec_b)
    assert snap_a == snap_b


@pytest.mark.parametrize(
    "scenario_header, expected_title_substring",
    [
        ("**Escenario S1: bold form**", "S1"),
        ("### Escenario S1: triple-hash form", "S1"),
        ("## Escenario S1: double-hash form", "S1"),
    ],
)
def test_h2_1_scenario_header_form_tolerance(
    tmp_path: Path, scenario_header: str, expected_title_substring: str
) -> None:
    """H2-1 impl note: regex tolerates **Escenario, ### Escenario, ## Escenario."""
    from spec_snapshot import emit_snapshot

    spec = tmp_path / "spec.md"
    spec.write_text(
        f"""# spec

## §4 Escenarios BDD

{scenario_header}

> **Given** x
> **When** y
> **Then** z
""",
        encoding="utf-8",
    )

    snapshot = emit_snapshot(spec)
    assert snapshot, f"no scenarios extracted from {scenario_header!r} form"
    assert any(expected_title_substring in t for t in snapshot.keys())


def test_emit_snapshot_raises_when_no_escenarios_section(tmp_path: Path) -> None:
    """WARNING melchior zero-match guard: missing §4 section raises ValueError."""
    from spec_snapshot import emit_snapshot

    spec = tmp_path / "spec.md"
    spec.write_text("# spec without scenarios section", encoding="utf-8")
    with pytest.raises(ValueError, match=r"No.*Escenarios section"):
        emit_snapshot(spec)


def test_emit_snapshot_raises_when_section_empty(tmp_path: Path) -> None:
    """WARNING melchior zero-match guard: empty §4 section raises ValueError.

    Silent {} would compare equal to another empty {} from a similarly
    broken spec, masking real drift.
    """
    from spec_snapshot import emit_snapshot

    spec = tmp_path / "spec.md"
    spec.write_text(
        """# spec

## §4 Escenarios BDD

(no scenario blocks)

## §5 next section
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="zero scenarios"):
        emit_snapshot(spec)
