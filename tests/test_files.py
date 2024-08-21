# %%
"""Test reading and writing files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
import pytest

from whitespacesv import WsvDocument
from whitespacesv.line import WsvLine

ASSETS = Path(__file__).parent / "assets"


def test_table() -> None:
    path = ASSETS / "table.txt"
    csv_path = ASSETS / "table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    wsv_str_df = doc.to_pandas(infer_types=False)
    wsv_header_false = doc.to_pandas(header=False)
    csv_header_false = pd.read_csv(csv_path, header=None)
    csv_header_false.columns = csv_header_false.columns.astype(str)

    assert wsv_header_false.equals(csv_header_false)
    csv_df = pd.read_csv(csv_path)
    assert wsv_df.equals(csv_df)
    assert wsv_str_df.equals(csv_df.astype(str))
    from_pandas = WsvDocument.from_pandas(wsv_df)
    to_pandas = from_pandas.to_pandas()
    assert wsv_df.equals(to_pandas)


def test_jagged_table() -> None:
    path = ASSETS / "jagged_table.txt"
    csv_path = ASSETS / "jagged_table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    csv_df = pd.read_csv(csv_path)
    assert wsv_df.equals(csv_df)


def test_comment_table() -> None:
    path = ASSETS / "comment_table.txt"
    csv_path = ASSETS / "comment_table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    csv_df = pd.read_csv(csv_path)
    assert not wsv_df.equals(csv_df)
    # without comment line
    csv_df = csv_df.iloc[:-1].astype(int)
    assert wsv_df.equals(csv_df)


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
    ("mode", "expected"),
    [("preserve", TABLE), ("compact", COMPACT), ("pretty", PRETTY)],
)
def test_space_lines(
    mode: Literal["preserve", "compact", "pretty"], expected: str
) -> None:
    doc = WsvDocument.parse(expected)
    assert doc.to_string(mode) == expected


@pytest.fixture
def test_line() -> WsvLine:
    values = ["Region 10", "105", "random", "3", "1"]
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
    comment: str | None | Literal[-1],
    test_line: WsvLine,
) -> None:
    doc = WsvDocument([test_line])
    assert doc.to_string(mode) == output
    if whitespace == -1:
        whitespace = test_line.whitespaces
    if comment == -1:
        comment = test_line.comment
    parsed_line = WsvLine(test_line.values, whitespace, comment)
    assert WsvDocument.parse(output).lines == [parsed_line]
