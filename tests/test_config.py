from pathlib import Path

import pytest
from dataclasses import FrozenInstanceError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "plugin-locals"


def test_plugin_config_is_frozen():
    from config import PluginConfig

    cfg = PluginConfig(
        stack="python",
        author="Test",
        error_type=None,
        verification_commands=("pytest", "ruff check ."),
        plan_path="planning/claude-plan-tdd.md",
        plan_org_path="planning/claude-plan-tdd-org.md",
        spec_base_path="sbtdd/spec-behavior-base.md",
        spec_path="sbtdd/spec-behavior.md",
        state_file_path=".claude/session-state.json",
        magi_threshold="GO_WITH_CAVEATS",
        magi_max_iterations=3,
        auto_magi_max_iterations=5,
        auto_verification_retries=1,
        tdd_guard_enabled=True,
        worktree_policy="optional",
    )
    with pytest.raises(FrozenInstanceError):
        cfg.stack = "rust"  # type: ignore[misc]


def test_plugin_config_verification_commands_is_tuple():
    from config import PluginConfig

    cfg = PluginConfig(
        stack="python",
        author="Test",
        error_type=None,
        verification_commands=("pytest",),
        plan_path="",
        plan_org_path="",
        spec_base_path="",
        spec_path="",
        state_file_path="",
        magi_threshold="GO_WITH_CAVEATS",
        magi_max_iterations=3,
        auto_magi_max_iterations=5,
        auto_verification_retries=1,
        tdd_guard_enabled=True,
        worktree_policy="optional",
    )
    assert isinstance(cfg.verification_commands, tuple)


def test_load_valid_python_config():
    from config import load_plugin_local, PluginConfig

    cfg = load_plugin_local(FIXTURES_DIR / "valid-python.md")
    assert isinstance(cfg, PluginConfig)
    assert cfg.stack == "python"
    assert cfg.author == "Julian Bolivar"
    assert cfg.magi_max_iterations == 3
    assert cfg.auto_magi_max_iterations == 5
    assert isinstance(cfg.verification_commands, tuple)
    assert "pytest" in cfg.verification_commands


def test_load_missing_file():
    from config import load_plugin_local
    from errors import ValidationError

    with pytest.raises(ValidationError):
        load_plugin_local(Path("/nonexistent/path.md"))
