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


def test_expand_preserves_trailing_newline():
    from templates import expand

    template = "{X}\n"
    assert expand(template, {"X": "a"}) == "a\n"


def test_expand_placeholder_with_special_chars_in_value():
    """Value containing braces should not be re-expanded (single pass)."""
    from templates import expand

    template = "{X}"
    result = expand(template, {"X": "{Y}"})
    assert result == "{Y}"  # not recursive; {Y} stays literal.
