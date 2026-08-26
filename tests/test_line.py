"""Tests for the WsvLine class."""

from __future__ import annotations

import pytest
from whitespacesv import WsvLine


@pytest.mark.parametrize(
    ("whitespaces", "expected"), [([" ", None], False), (None, False), (["te"], True)]
)
def test_validate_whitespaces(whitespaces: list[str | None] | None, expected: bool) -> None:
    if expected:
        with pytest.raises(
            ValueError, match="Whitespace value contains non whitespace character/line feed"
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


def test_init_rejects_invalid_whitespace() -> None:
    with pytest.raises(
        ValueError, match="Whitespace value contains non whitespace character/line feed"
    ):
        WsvLine(["a"], ["te"])


def test_init_rejects_invalid_comment() -> None:
    with pytest.raises(ValueError, match="Line feed in comment is not allowed"):
        WsvLine(["a"], None, "line\nfeed")


def test_init_defaults_to_empty_values() -> None:
    line = WsvLine()
    assert line.values == []
    assert line.whitespaces is None
    assert line.comment is None


def test_eq() -> None:
    a = WsvLine(["a", "b", "c"], [" ", None], "comment")
    b = WsvLine(["a", "b", "c"], [" ", None], "comment")
    assert a == b
    assert a != WsvLine(["a", "b"], [" ", None], "comment")
    assert a != "not a line"


def test_repr() -> None:
    line = WsvLine(["a", "b", "c"], [" ", None], "comment")
    assert repr(line) == "Line(['a', 'b', 'c'], [' ', None], comment)"


def test_repr_without_whitespaces_or_comment() -> None:
    line = WsvLine(["a", None])
    assert repr(line) == "Line(['a', None], None, None)"
