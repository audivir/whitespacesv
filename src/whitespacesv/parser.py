"""This module contains the WsvParser class."""

from __future__ import annotations

from whitespacesv.line import WsvLine
from whitespacesv.utils import WsvCharIterator


def _parse_value_wrapper(iterator: WsvCharIterator) -> str | None:
    if iterator.try_read_char(0x22):  # DOUBLE_QUOTE
        return iterator.read_string()

    value = iterator.read_value()
    if value == "-":
        return None

    return value


def _try_parse_comment(
    iterator: WsvCharIterator, whitespace: str | None, whitespaces: list[str | None]
) -> str | None:
    """Parses the comment text."""
    if not iterator.try_read_char(0x23):  # HASH
        return None

    comment = iterator.read_comment_text()
    if whitespace is None:
        whitespaces.append(None)

    return comment


def _parse_line(iterator: WsvCharIterator) -> WsvLine:
    """Parses a WSV line."""
    values: list[str | None] = []
    whitespaces: list[str | None] = []

    whitespace = iterator.read_whitespace_or_null()
    whitespaces.append(whitespace)

    comment: str | None = None

    while not iterator.is_end_of_section():
        value = None

        if comment := _try_parse_comment(iterator, whitespace, whitespaces):
            break

        value = _parse_value_wrapper(iterator)

        values.append(value)

        if comment := _try_parse_comment(iterator, whitespace, whitespaces):
            break

        whitespace = iterator.read_whitespace_or_null()

        if whitespace is None:
            break

        whitespaces.append(whitespace)

    return WsvLine(values, whitespaces, comment)


def parse_lines(text: str) -> list[WsvLine]:
    """Parses the WSV lines."""
    lines: list[WsvLine] = []

    iterator = WsvCharIterator(text)

    while not iterator.is_eof():
        line = _parse_line(iterator)
        lines.append(line)

        iterator.forward()

    return lines
