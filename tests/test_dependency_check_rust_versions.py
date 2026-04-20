# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Tests for Rust shim version-format validation (Plan D Task 6)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import dependency_check
import subprocess_utils


_OK_CLIPPY = "clippy 0.1.79 (bbdc35d 2024-05-15)\n"
_OK_FMT = "rustfmt 1.7.0-stable (129f3b99 2024-05-23)\n"
_OK_NEXTEST = "cargo-nextest-nextest 0.9.70\n"
_OK_AUDIT = "cargo-audit-audit 0.20.0\n"


def test_rust_shim_cargo_clippy_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_CLIPPY, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "OK"


def test_rust_shim_cargo_fmt_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_FMT, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-fmt", "rust (cargo-fmt)")
    assert result.status == "OK"


def test_rust_shim_broken_output_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        # A shim that returns exit 0 with garbage -- must still reject.
        return SimpleNamespace(returncode=0, stdout="banana\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "BROKEN"
    assert "unexpected" in result.detail.lower() or "parse" in result.detail.lower()


def test_rust_shim_cargo_nextest_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout=_OK_NEXTEST, stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-nextest", "rust (cargo-nextest)")
    assert result.status == "OK"


def test_non_rust_binary_unaffected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regression: git and other non-rust binaries must not be gated by
    # the rust version regex. Stdout can be anything as long as exit 0.
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="git version 2.40.0\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("git", "git")
    assert result.status == "OK"


# MAGI Loop 2 D iter 1 Melchior: tighten per-shim regex so garbage-prefixed
# version-like strings are rejected. The iter-1 loose patterns
# (``^\w+\s+\d+\.\d+``) accepted banana 0.1 or nonsense 0.9 because the
# ``\w+`` prefix was not anchored to the expected shim name. New patterns
# must match the exact shim name and require a 3-part semver.


def test_rust_shim_clippy_rejects_wrong_name_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        # Loose regex accepted this; tightened one must not.
        return SimpleNamespace(returncode=0, stdout="banana 0.1.79\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "BROKEN"


def test_rust_shim_fmt_rejects_wrong_name_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="fakeformat 1.7.0\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-fmt", "rust (cargo-fmt)")
    assert result.status == "BROKEN"


def test_rust_shim_nextest_rejects_abbreviated_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loose pattern accepted ``cargo-nextest 0.9.70`` (missing
    ``-nextest`` suffix). Tightened pattern requires the full shim
    output prefix ``cargo-nextest-nextest``."""
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="cargo-nextest 0.9.70\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-nextest", "rust (cargo-nextest)")
    assert result.status == "BROKEN"


def test_rust_shim_audit_rejects_abbreviated_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="cargo-audit 0.20.0\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-audit", "rust (cargo-audit)")
    assert result.status == "BROKEN"


def test_rust_shim_clippy_requires_three_part_semver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``clippy 0.1`` with no patch version should be rejected. Real
    clippy emits full ``major.minor.patch`` with optional commit hash
    suffix; a 2-part version is a sentinel for a stub/placeholder."""
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="clippy 0.1\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-clippy", "rust (cargo-clippy)")
    assert result.status == "BROKEN"


def test_rust_shim_audit_requires_three_part_semver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd: list[str], **kwargs: Any) -> Any:
        return SimpleNamespace(returncode=0, stdout="cargo-audit-audit 0.20\n", stderr="")

    monkeypatch.setattr(subprocess_utils, "run_with_timeout", fake_run)
    result = dependency_check._check_binary("cargo-audit", "rust (cargo-audit)")
    assert result.status == "BROKEN"
