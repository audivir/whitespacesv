"""Tests for whitespacesv.__init__ module."""

# ruff: noqa: PD901
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

import pandas as pd
import pytest

from whitespacesv.document import WsvDocument
from whitespacesv.line import WsvLine


def test_init() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    assert WsvDocument([line]) == WsvDocument([line])
    with pytest.raises(TypeError, match=r"'WsvLine' object is not iterable"):
        WsvDocument(line)  # type: ignore[arg-type]


def test_eq() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    a = WsvDocument([line])
    b = WsvDocument([line])
    assert a == b
    assert a != type("WsvDocument", (), {"lines": [line]})()


def test_repr() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    doc = WsvDocument([line])

    assert repr(doc) == f"Document(lines=[{line!r}])"


@pytest.mark.parametrize(
    ("preserves", "expected"),
    [("preserve", ["a \tb c #comment"]), ("compact", ["a b c"]), ("pretty", ["a\tb\tc\t#comment"])],
)
def test_serialize(
    preserves: Literal["preserve", "compact", "pretty"], expected: list[str]
) -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")
    doc = WsvDocument([line])
    assert doc.serialize(preserves) == expected


def test_fail_serialize() -> None:
    with pytest.raises(ValueError, match="'invalid' is not a valid SerializationMode"):
        WsvDocument().serialize("invalid")  # type: ignore[arg-type]


def test_pretty() -> None:
    line = WsvLine(["ab", "b", "c"], [None, " \t", " "], "comment")
    line2 = WsvLine(["a", "b", "c"], [None, " \t", " "], "comment")
    doc = WsvDocument([line, line2])
    assert doc.serialize("pretty") == ["ab\tb\tc\t#comment", "a \tb\tc\t#comment"]


def test_parse() -> None:
    text = """a \tb c #comment\na \tb c #comment\n"""
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")
    doc = WsvDocument([line, line])
    assert WsvDocument.parse(text) == doc


def test_load() -> None:
    line = WsvLine(["a", "b", "c"], [None, " \t", " ", " "], "comment")

    with tempfile.NamedTemporaryFile() as file:
        with pytest.raises(ValueError, match=r"Can't save empty document"):
            WsvDocument().save(file.name)

        Path(file.name).write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match=r"Empty file or no new line at the end"):
            WsvDocument.load(file.name)
        Path(file.name).write_text("a b c", encoding="utf-8")
        with pytest.raises(ValueError, match=r"Empty file or no new line at the end"):
            WsvDocument.load(file.name)

    with tempfile.NamedTemporaryFile() as file:
        doc = WsvDocument([line])
        doc.save(file.name)
        assert WsvDocument.load(file.name) == doc


def test_from_pandas() -> None:
    test_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    doc = WsvDocument.from_pandas(test_df)

    lines = [WsvLine(["a", "b"]), WsvLine(["1", "4"]), WsvLine(["2", "5"]), WsvLine(["3", "6"])]
    expected_doc = WsvDocument(lines)

    doc_wo_header = WsvDocument.from_pandas(test_df, header=False)
    lines_wo_header = lines[1:]
    expected_doc_wo_header = WsvDocument(lines_wo_header)

    assert doc == expected_doc
    assert doc_wo_header == expected_doc_wo_header
