"""Tests for the WsvDocument class."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

import pytest
from whitespacesv import WsvDocument, WsvLine


def test_init_defaults_to_empty_lines() -> None:
    assert WsvDocument().lines == []


def test_eq() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    a = WsvDocument([line])
    b = WsvDocument([line])
    assert a == b
    assert a != WsvDocument([])
    assert a != "not a document"


def test_repr() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    doc = WsvDocument([line])
    assert repr(doc) == f"Document(lines=[{line!r}])"


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("preserve", ["a \tb c #comment"]), ("compact", ["a b c"]), ("pretty", ["a\tb\tc\t#comment"])],
)
def test_serialize(mode: Literal["preserve", "compact", "pretty"], expected: list[str]) -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")
    doc = WsvDocument([line])
    assert doc.serialize(mode) == expected


def test_fail_serialize() -> None:
    with pytest.raises(ValueError, match="'invalid' is not a valid SerializationMode"):
        WsvDocument().serialize("invalid")


def test_pretty_pads_columns_across_lines() -> None:
    line = WsvLine(["ab", "b", "c"], [None, " \t", " "], "comment")
    line2 = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    doc = WsvDocument([line, line2])
    assert doc.serialize("pretty") == ["ab\tb\tc\t#comment", "a \tb\tc\t#comment"]


def test_parse() -> None:
    text = "a \tb c #comment\na \tb c #comment\n"
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")
    assert WsvDocument.parse(text) == WsvDocument([line, line])


def test_parse_empty_text_yields_no_lines() -> None:
    assert WsvDocument.parse("").lines == []


def test_save_rejects_empty_document() -> None:
    with pytest.raises(ValueError, match="Can't save empty document"):
        WsvDocument().save("unused.wsv")


@pytest.mark.parametrize("content", ["", "a b c"])
def test_load_rejects_missing_trailing_newline(content: str) -> None:
    with tempfile.NamedTemporaryFile() as file:
        Path(file.name).write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match="Empty file or no new line at the end"):
            WsvDocument.load(file.name)


def test_save_and_load_round_trip() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")
    doc = WsvDocument([line])
    with tempfile.NamedTemporaryFile() as file:
        doc.save(file.name)
        assert WsvDocument.load(file.name) == doc
