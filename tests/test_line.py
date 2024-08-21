"""Tests for the WsvLine class."""

from __future__ import annotations

import pytest

from whitespacesv.line import WsvLine


@pytest.mark.parametrize(
    ("whitespaces", "expected"), [([" ", None], False), (None, False), (["te"], True)]
)
def test_validate_whitespaces(
    whitespaces: list[str | None] | None, expected: bool
) -> None:
    if expected:
        with pytest.raises(
            ValueError,
            match="Whitespace value contains non whitespace character/line feed",
        ):
            WsvLine.validate_whitespaces(whitespaces)
    else:
        assert WsvLine.validate_whitespaces(whitespaces) is None


@pytest.mark.parametrize(
    ("comment", "expected"), [("", False), ("test", False), (" ", False), ("\n", True)]
)
def test_validate_comment(comment: str | None, expected: bool) -> None:
    if expected:
        with pytest.raises(ValueError, match="Line feed in comment is not allowed"):
            WsvLine.validate_comment(comment)
    else:
        assert WsvLine.validate_comment(comment) is None


def test_eq() -> None:
    a = WsvLine(["a", "b", "c"], [" ", None], "#comment")
    b = WsvLine(["a", "b", "c"], [" ", None], "#comment")

    assert a == b
    a_ = type(
        "WsvLine",
        (),
        {"values": ["a", "b", "c"], "whitespaces": [" ", None], "comment": "#comment"},
    )
    assert a != a_


def test_repr() -> None:
    line = WsvLine(["a", "b", "c"], [" ", None], "comment")
    assert repr(line) == "Line(['a', 'b', 'c'], [' ', None], comment)"
