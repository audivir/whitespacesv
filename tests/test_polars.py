"""Tests for the to_polars/from_polars conversion functions."""

from __future__ import annotations

import polars as pl
from whitespacesv import WsvDocument, WsvLine, from_polars, to_polars


def make_document() -> WsvDocument:
    return WsvDocument(
        [WsvLine(["a", "b"]), WsvLine(["1", "4"]), WsvLine(["2", "5"]), WsvLine(["3", "6"])]
    )


def test_to_polars_with_header_infers_types() -> None:
    frame = to_polars(make_document())
    expected = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert frame.equals(expected)


def test_to_polars_without_header() -> None:
    frame = to_polars(make_document(), header=False)
    assert frame.shape == (4, 2)
    assert frame.row(0) == ("a", "b")


def test_to_polars_without_infer_types_keeps_strings() -> None:
    frame = to_polars(make_document(), infer_types=False)
    assert frame.dtypes == [pl.String, pl.String]
    assert frame.row(0) == ("1", "4")


def test_to_polars_skips_empty_rows() -> None:
    doc = WsvDocument([WsvLine(["a"]), WsvLine([]), WsvLine(["1"])])
    frame = to_polars(doc)
    assert frame.shape == (1, 1)


def test_from_polars_round_trips_with_header() -> None:
    frame = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    doc = from_polars(frame)
    assert doc == make_document()


def test_from_polars_without_header() -> None:
    frame = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    doc = from_polars(frame, header=False)
    assert doc == WsvDocument(make_document().lines[1:])


def test_from_polars_maps_nulls_to_none() -> None:
    frame = pl.DataFrame({"a": [1, None]})
    doc = from_polars(frame, header=False)
    assert doc.lines[0].values == ["1"]
    assert doc.lines[1].values == [None]
