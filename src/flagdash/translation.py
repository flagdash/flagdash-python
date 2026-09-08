"""Small ICU message formatter shared by the Python clients."""

from __future__ import annotations

import re
from typing import Any


def format_translation(pattern: str, variables: dict[str, Any] | None = None) -> str:
    values = variables or {}
    complex_pattern = re.compile(
        r"\{([\w.]+),\s*(plural|selectordinal|select),\s*((?:[^{}]|\{[^{}]*\})*)\}"
    )

    def complex_value(match: re.Match[str]) -> str:
        name, kind, body = match.groups()
        choices = dict(re.findall(r"(=?[\w-]+)\s*\{([^{}]*)\}", body))
        value = values.get(name)
        if kind == "select":
            choice = str(value)
        else:
            number = float(value or 0)
            exact = f"={int(number)}"
            choice = exact if exact in choices else ("one" if number == 1 else "other")
        return choices.get(choice, choices.get("other", "")).replace("#", str(value or 0))

    result = complex_pattern.sub(complex_value, pattern)
    return re.sub(
        r"\{([\w.]+)\}",
        lambda match: str(values.get(match.group(1), match.group(0))),
        result,
    )
