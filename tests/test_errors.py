"""Tests for the WsvParserError exception."""

from __future__ import annotations

import pytest
from whitespacesv import WsvDocument, WsvParserError


def test_constructs_with_one_indexed_position_in_message() -> None:
    exc = WsvParserError(0, 0, 0, "test")
    assert str(exc) == "test (1, 1)"
    assert exc.ix == 0
    assert exc.line_ix == 0
    assert exc.line_position == 0


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('a"', "Invalid double quote in value"),
        ('"heg', "String not closed"),
        ('"heg"/d"', "Invalid string line break"),
        ('"heg"f', "Invalid character after string"),
        ("#\n", "Invalid value"),
    ],
)
def test_parse_raises_on_malformed_input(text: str, message: str) -> None:
    with pytest.raises(WsvParserError, match=message):
        WsvDocument.parse(text)


def test_position_is_one_indexed_and_char_based() -> None:
    with pytest.raises(WsvParserError, match=r"Invalid double quote in value \(1, 2\)") as exc_info:
        WsvDocument.parse('a"')
    assert exc_info.value.ix == 1
    assert exc_info.value.line_ix == 0
    assert exc_info.value.line_position == 1


def test_position_counts_lines() -> None:
    with pytest.raises(WsvParserError, match=r"Invalid double quote in value \(2, 2\)"):
        WsvDocument.parse('a b\nc"\n')
