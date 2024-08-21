"""Tests for the whitespacesv.parser module."""

from __future__ import annotations

import pytest

from whitespacesv.line import WsvLine
from whitespacesv.parser import _parse_line, _parse_value_wrapper, _try_parse_comment
from whitespacesv.utils import WsvCharIterator


@pytest.mark.parametrize(
    ("text", "expected"),
    [("-", None), ('"test"', "test"), ('"test test"', "test test"), ("a", "a")],
)
def test_parse_value_wrapper(text: str, expected: str | None) -> None:
    it = WsvCharIterator(text)
    assert _parse_value_wrapper(it) == expected


@pytest.mark.parametrize(
    ("text", "whitespace", "expected"),
    [("#hello", " ", "hello"), ("hello", None, None), ("#hello", None, "hello")],
)
def test_parse_comment(text: str, whitespace: str, expected: str) -> None:
    it = WsvCharIterator(text)
    assert _try_parse_comment(it, whitespace, []) == expected


def test_parse_line() -> None:
    it = WsvCharIterator("")
    line = _parse_line(it)
    assert line == WsvLine([], [None], None)
