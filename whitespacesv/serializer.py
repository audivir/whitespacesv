"""The serializer module contains the serialization functions."""

# ruff: noqa: PLR2004
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from whitespacesv.utils import chars_to_ords, contains_string_special_chars, ords_to_chars

if TYPE_CHECKING:
    from collections.abc import Iterator


class SerializationMode(Enum):
    """The serialization mode.

    Attributes:
        PRESERVE:
            The values are serialized with the original whitespaces and comments.
        COMPACT:
            The values are serialized without whitespaces and comments.
        PRETTY:
            The values are serialized with a minimum of whitespaces
            and the original comments.
    """

    PRESERVE = "preserve"
    COMPACT = "compact"
    PRETTY = "pretty"


def prettify_values(values: list[list[str]], comments: list[str | None]) -> list[str]:
    """Prettifies the values and adds comments if present."""
    # Get the maximum length of each column
    transposed_it: Iterator[tuple[str, ...]] = zip(*values, strict=False)
    col_sizes = [max(len(x) for x in col) for col in transposed_it]

    min_spacing = "\t"

    serialized: list[str] = []
    for serialized_values, comment in zip(values, comments, strict=False):
        expanded_cols = [f"{x:<{col_sizes[ix]}}" for ix, x in enumerate(serialized_values)]

        serialized_line = min_spacing.join(expanded_cols)

        if comment:
            serialized_line += min_spacing + f"#{comment}"

        serialized.append(serialized_line.strip())

    return serialized


def serialize_value(value: str | None) -> str:
    """Serializes the value."""
    # A none value is mapped to a single dash
    if value is None:
        return "-"

    # therefore we have to escape a single dash with double quotes
    if value == "-":
        return '"-"'

    # An empty string is mapped to a pair of double quotes
    if len(value) == 0:
        return '""'

    # If spaces, new lines, etc. are in the string,
    # we have to escape it with double quotes
    if contains_string_special_chars(value):
        result: list[int] = []
        ords = chars_to_ords(value)
        result.append(0x22)  # DOUBLE_QUOTE
        for c in ords:
            # New line is escaped with double quote, slash, double quote
            if c == 0x0A:  # NEW_LINE
                result.append(0x22)  # DOUBLE_QUOTE
                result.append(0x2F)  # SLASH
                result.append(0x22)  # DOUBLE_QUOTE

            # Double quote is escaped with double quote
            elif c == 0x22:  # DOUBLE_QUOTE
                result.append(0x22)  # DOUBLE_QUOTE
                result.append(0x22)  # DOUBLE_QUOTE
            else:
                result.append(c)

        result.append(0x22)  # DOUBLE_QUOTE
        return ords_to_chars(result)

    return value


def _serialize_whitespace(whitespace: str | None, is_required: bool) -> str:
    """The whitespace or a space if the whitespace is required but not set."""
    return whitespace or (" " if is_required else "")


def _get_whitespace(whitespaces: list[str | None], ix: int) -> str | None:
    """Returns the whitespace at the index or None if it does not exist."""
    return whitespaces[ix] if ix < len(whitespaces) else None


def serialize_values_with_whitespace(values: list[str], whitespaces: list[str | None]) -> str:
    """Serializes the values with the whitespaces."""
    if not values:
        return _serialize_whitespace(whitespaces[0], False)

    results: list[str] = []
    for ix, value in enumerate(values):
        # Get the whitespace before the value
        whitespace = _get_whitespace(whitespaces, ix)
        # Add the whitespace before the value, required for all but the first value
        elem = _serialize_whitespace(whitespace, ix != 0)
        # Add the value
        elem += value
        # Add the element to the results
        results.append(elem)

    if len(whitespaces) >= len(values) + 1:
        whitespace = whitespaces[len(values)]
        results.append(_serialize_whitespace(whitespace, False))

    return "".join(results)


def serialize_line(
    values: list[str], whitespaces: list[str | None] | None, comment: str | None
) -> str:
    """Serializes the line to a string with whitespaces and comment."""
    if not whitespaces:
        line = " ".join(values)

    else:
        line = serialize_values_with_whitespace(values, whitespaces)

    comment_suffix = f"#{comment}" if comment is not None else ""
    return line + comment_suffix
