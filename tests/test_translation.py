from flagdash.translation import format_translation


def test_formats_simple_variables_and_preserves_missing_variables() -> None:
    assert format_translation("Hello {name}", {"name": "Marta"}) == "Hello Marta"
    assert format_translation("Hello {name}") == "Hello {name}"


def test_formats_icu_plural_exact_and_select_branches() -> None:
    plural = "{count, plural, one {# item} other {# items}}"
    assert format_translation(plural, {"count": 1}) == "1 item"
    assert format_translation(plural, {"count": 3}) == "3 items"
    exact = "{count, plural, =0 {Empty} other {# items}}"
    assert format_translation(exact, {"count": 0}) == "Empty"
    assert format_translation(
        "{role, select, admin {Administrator} other {Member}}", {"role": "admin"}
    ) == "Administrator"
