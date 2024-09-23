"""Tests for the whitespacesv.parser module."""

from __future__ import annotations

import pytest

from whitespacesv.parser import _parse_value_wrapper, _try_parse_comment, check_for_end
from whitespacesv.utils import WsvCharIterator, WsvParserError


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", None),
        ("\n", "Multiple WSV lines not allowed"),
        ("a", "Unexpected parser error"),
    ],
)
def test_check_for_end(text: str, expected: str | None) -> None:
    it = WsvCharIterator(text)
    if expected is None:
        check_for_end(it)
    else:
        with pytest.raises(WsvParserError, match=expected + ".*"):
            check_for_end(it)


@pytest.mark.parametrize(
    "text, expected",
    [("-", None), ('"test"', "test"), ('"test test"', "test test"), ("a", "a")],
)
def test_parse_value_wrapper(text: str, expected: str | None) -> None:
    it = WsvCharIterator(text)
    assert _parse_value_wrapper(it) == expected


@pytest.mark.parametrize(
    "text, whitespace, expected",
    [("#hello", " ", "hello"), ("hello", None, None), ("#hello", None, "hello")],
)
def test_parse_comment(text: str, whitespace: str, expected: str) -> None:
    it = WsvCharIterator(text)
    assert _try_parse_comment(it, whitespace, []) == expected
