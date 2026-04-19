def test_expand_substitutes_known_placeholders():
    from templates import expand

    template = "# Author: {Author}\n# Version: {Version}\n"
    result = expand(template, {"Author": "Jane Doe", "Version": "1.0.0"})
    assert result == "# Author: Jane Doe\n# Version: 1.0.0\n"


def test_expand_leaves_unknown_placeholders_literal():
    """Unknown placeholders stay as-is (no KeyError, no silent error)."""
    from templates import expand

    template = "Hello {Known} and {Unknown}"
    result = expand(template, {"Known": "world"})
    assert result == "Hello world and {Unknown}"


def test_expand_empty_context():
    from templates import expand

    template = "no placeholders here"
    assert expand(template, {}) == "no placeholders here"
