"""Tests for whitespacesv.utils module."""

# ruff: noqa: PD901
from __future__ import annotations

import pandas as pd
import pytest

from whitespacesv.utils import (
    WsvCharIterator,
    WsvParserError,
    contains_string_special_chars,
    is_ord_whitespace,
    is_string_whitespace,
    reinfer_types,
)


def test_reinfer_types() -> None:
    raw_df = pd.DataFrame({"a": ["1", "2", "3"], "b": ["4", "5", "6"]})
    infered_df = reinfer_types(raw_df)
    assert infered_df.dtypes["a"] == "int64"
    assert infered_df.dtypes["b"] == "int64"


# test for is_ord_whitespace
WHITESPACES = {
    0x0009,
    0x000B,
    0x000C,
    0x000D,
    0x0020,
    0x0085,
    0x00A0,
    0x1680,
    0x2000,
    0x2001,
    0x2002,
    0x2003,
    0x2004,
    0x2005,
    0x2006,
    0x2007,
    0x2008,
    0x2009,
    0x200A,
    0x2028,
    0x2029,
    0x202F,
    0x205F,
    0x3000,
}


def test_is_ord_whitespace() -> None:
    for c in range(0xFFFF):
        supposed = c in WHITESPACES
        assert is_ord_whitespace(c) == supposed


def test_is_string_whitespace() -> None:
    assert not is_string_whitespace("")
    chars = [chr(ix) for ix in range(0xFFFF)]

    whitespaces = set(WHITESPACES)
    for ix, char in enumerate(chars):
        supposed = ix in whitespaces
        assert is_string_whitespace(char) == supposed
        if supposed:
            assert is_string_whitespace(char * 3) == supposed
            assert not is_string_whitespace(char + "a")


def test_contains_string_special_chars() -> None:
    # new_line, # double_quote , # hash
    chars = [chr(ix) for ix in range(0xFFFF)]
    specials_ls = [chr(w) for w in WHITESPACES] + ["\n", '"', "#"]
    specials = set(specials_ls)
    for char in chars:
        supposed = char in specials
        assert contains_string_special_chars(char) == supposed
        if supposed:
            assert contains_string_special_chars(char + "a")


def test_wsv_parser_exception() -> None:
    exc = WsvParserError(0, 0, 0, "test")
    with pytest.raises(WsvParserError, match=r"test \(1, 1\)"):
        raise exc
    assert str(exc) == "test (1, 1)"


@pytest.mark.parametrize(
    ("c", "eof", "ws"), [("a", False, False), ("", True, False), (" ", False, True)]
)
def test_is_whitespace(c: str, eof: bool, ws: bool) -> None:
    it = WsvCharIterator(c)
    assert it.is_whitespace() == ws
    assert it.is_eof() == eof


def test_get_string() -> None:
    it = WsvCharIterator("a b c")
    it.forward()
    it.forward()
    assert it.get_string(0) == "a "


@pytest.mark.parametrize(
    ("text", "eol", "expected"),
    [
        ("a b c", False, 2),
        ("a b c", True, 5),
        ("   ", False, 3),
        ("  \n", False, 2),
        ("  \n", True, 2),
    ],
)
def test_jump(text: str, eol: bool, expected: int) -> None:
    it = WsvCharIterator(text)
    it.forward()
    start_ix = it.jump(eol=eol)
    assert it.ix == expected
    assert start_ix == 1


def test_read_comment_text() -> None:
    it = WsvCharIterator("#comment")
    it.try_read_char(0x23)
    assert it.read_comment_text() == "comment"


def test_read_whitespace_or_null() -> None:
    it = WsvCharIterator(" a")
    assert it.read_whitespace_or_null() == " "
    assert it.read_whitespace_or_null() is None


def test_get_exc() -> None:
    it = WsvCharIterator("a b c")
    it.forward()
    exc = it.get_exc("test")
    assert exc.ix == 1
    assert exc.line_ix == 0
    assert exc.line_position == 1
    with pytest.raises(WsvParserError, match=r"test \(1, 2\)"):
        raise exc


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a", False), ("#", True), ("", True), (" ", True), ("\n", True)],
)
def test_stop_read(text: str, expected: bool) -> None:
    it = WsvCharIterator(text)
    assert it.stop_read() == expected


@pytest.mark.parametrize(
    ("text", "expected"), [("a", False), (" ", False), ("\n", True), ("", True)]
)
def test_is_end_of_section(text: str, expected: bool) -> None:
    it = WsvCharIterator(text)
    assert it.is_end_of_section() == expected


@pytest.mark.parametrize(
    ("text", "expected", "message"),
    [
        ('"hegd"', "hegd", None),
        ('"hegd"""', 'hegd"', None),
        ('"heg"/"d"', "heg\nd", None),
        ('"heg"/d"', None, "Invalid string line break"),
        ('"heg', None, "String not closed"),
        ('"heg"f', None, "Invalid character after string"),
    ],
)
def test_read_string(text: str, expected: str | None, message: str | None) -> None:
    it = WsvCharIterator(text)
    it.try_read_char(0x22)

    if expected:
        assert it.read_string() == expected

    if message:
        with pytest.raises(WsvParserError, match=message):
            it.read_string()


@pytest.mark.parametrize(
    ("text", "expected", "message"),
    [
        ("a", "a", None),
        ("a#", "a", None),
        ("a\n", "a", None),
        ("a ", "a", None),
        ('a"', None, "Invalid double quote in value"),
        ("", None, "Invalid value"),
    ],
)
def test_read_value(text: str, expected: str | None, message: str | None) -> None:
    it = WsvCharIterator(text)

    if expected:
        assert it.read_value() == expected

    if message:
        with pytest.raises(WsvParserError, match=message):
            it.read_value()


# %%
