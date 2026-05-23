from conftest import ROOT

VDIR = ROOT / "templates/verification"


def test_three_stacks_present():
    for stack in ("rust", "python", "cpp"):
        assert (VDIR / f"{stack}.md").is_file()


def test_rust_has_core_commands():
    t = (VDIR / "rust.md").read_text(encoding="utf-8")
    for cmd in ("cargo nextest run", "cargo clippy", "cargo fmt", "cargo audit"):
        assert cmd in t


def test_python_has_core_commands():
    t = (VDIR / "python.md").read_text(encoding="utf-8")
    for cmd in ("pytest", "ruff check", "ruff format", "mypy"):
        assert cmd in t


def test_cpp_has_core_commands():
    t = (VDIR / "cpp.md").read_text(encoding="utf-8")
    for cmd in ("cmake --build", "ctest"):
        assert cmd in t
