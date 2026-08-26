"""Test reading and writing files, and round-tripping through polars."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import polars as pl
import pytest
from whitespacesv import WsvDocument, WsvLine, to_polars

ASSETS = Path(__file__).parent / "assets"


def test_table() -> None:
    doc = WsvDocument.load(ASSETS / "table.txt")
    frame = to_polars(doc)
    expected = pl.read_csv(ASSETS / "table.csv")
    assert frame.equals(expected)


def test_jagged_table() -> None:
    doc = WsvDocument.load(ASSETS / "jagged_table.txt")
    frame = to_polars(doc)
    expected = pl.read_csv(ASSETS / "jagged_table.csv")
    assert frame.equals(expected)


def test_comment_table_drops_comment_only_line() -> None:
    doc = WsvDocument.load(ASSETS / "comment_table.txt")
    frame = to_polars(doc)
    expected = pl.read_csv(ASSETS / "comment_table.csv", comment_prefix="#")
    assert frame.equals(expected)


TABLE = """\
"a b" "c d" #comment
"1 2" 3
4 "no comment in this line"
"""
COMPACT = """"a b" "c d"
"1 2" 3
4 "no comment in this line"
"""
PRETTY = """\
"a b"\t"c d"                    \t#comment
"1 2"\t3
4    \t"no comment in this line"
"""


@pytest.mark.parametrize(
    ("mode", "expected"), [("preserve", TABLE), ("compact", COMPACT), ("pretty", PRETTY)]
)
def test_space_lines(mode: Literal["preserve", "compact", "pretty"], expected: str) -> None:
    doc = WsvDocument.parse(expected)
    assert doc.to_string(mode) == expected


@pytest.fixture
def sample_line() -> WsvLine:
    values: list[str | None] = ["Region 10", "105", "random", "3", "1"]
    return WsvLine(values, [None, "\t", " ", " ", " "], "test")


@pytest.mark.parametrize(
    ("mode", "output", "whitespace", "comment"),
    [
        ("compact", '"Region 10" 105 random 3 1\n', [None, " ", " ", " ", " "], None),
        ("preserve", '"Region 10"\t105 random 3 1#test\n', -1, -1),
        (
            "pretty",
            '"Region 10"\t105\trandom\t3\t1\t#test\n',
            [None, "\t", "\t", "\t", "\t", "\t"],
            "test",
        ),
    ],
)
def test_to_string(
    mode: Literal["preserve", "compact", "pretty"],
    output: str,
    whitespace: list[str | None] | Literal[-1] | None,
    comment: str | Literal[-1] | None,
    sample_line: WsvLine,
) -> None:
    doc = WsvDocument([sample_line])
    assert doc.to_string(mode) == output
    if whitespace == -1:
        whitespace = sample_line.whitespaces
    if comment == -1:
        comment = sample_line.comment
    parsed_line = WsvLine(sample_line.values, whitespace, comment)
    assert WsvDocument.parse(output).lines == [parsed_line]
