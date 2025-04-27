"""Tests for the whitespacesv.serializer module."""

from __future__ import annotations

import pytest

from whitespacesv.line import WsvLine
from whitespacesv.serializer import (
    serialize_line,
    serialize_value,
    serialize_values_with_whitespace,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "-"),
        ("", '""'),
        ("a", "a"),
        ("-", '"-"'),
        ("a b", '"a b"'),
        ("a\nb", '"a"/"b"'),
        ('a"b', '"a""b"'),
    ],
)
def test_serialize_value(value: str | None, expected: str) -> None:
    assert serialize_value(value) == expected


@pytest.mark.parametrize(
    ("values", "whitespaces", "comment", "with_whitespace", "without_whitespace"),
    [
        (["a", "b", "c"], [None, " \t", " "], "comment", "a \tb c", "a b c"),
        (["a", "b", "c"], [None, " \t", " "], None, "a \tb c", "a b c"),
        (["a", "b", "c"], None, None, "a b c", "a b c"),
        ([], [None], "comment", "", ""),
        (["a", "b", "c"], [None, " \t", " "], "", "a \tb c", "a b c"),
        (["a", "b", "c"], [None, " \t", " ", " "], None, "a \tb c ", "a b c"),
    ],
)
def test_serialize_line(
    values: list[str],
    whitespaces: list[str | None] | None,
    comment: str | None,
    with_whitespace: str,
    without_whitespace: str,
) -> None:
    line = WsvLine(values, whitespaces, comment)
    values = [serialize_value(value) for value in values]
    hashed_comment = ("#" + comment) if comment is not None else ""

    if not line.whitespaces:
        assert serialize_line(values, whitespaces, comment) == without_whitespace + hashed_comment
    else:
        assert serialize_line(values, whitespaces, comment) == with_whitespace + hashed_comment
        assert serialize_values_with_whitespace(values, line.whitespaces) == with_whitespace
