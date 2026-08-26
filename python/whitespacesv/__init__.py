"""The main module of the whitespacesv package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from whitespacesv._whitespacesv import WsvDocument, WsvLine, WsvParserError

if TYPE_CHECKING:
    import polars as pl

__all__ = ["WsvDocument", "WsvLine", "WsvParserError", "from_polars", "to_polars"]


def to_polars(document: WsvDocument, header: bool = True, infer_types: bool = True) -> pl.DataFrame:
    """Converts document to a polars DataFrame via a CSV round trip.

    Args:
        document: The document to convert.
        header: Whether the first row is the header.
        infer_types: Whether to infer column types from the values.
    """
    import csv
    import io

    import polars as pl

    rows = [line.values for line in document.lines if line.values]
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    buffer.seek(0)

    return pl.read_csv(buffer, has_header=header, infer_schema=infer_types)


def from_polars(frame: pl.DataFrame, header: bool = True) -> WsvDocument:
    """Converts a polars DataFrame to a document.

    Args:
        frame: The DataFrame to convert.
        header: Whether to add the column names as the first row.
    """
    rows = [[None if value is None else str(value) for value in row] for row in frame.iter_rows()]
    if header:
        rows.insert(0, [str(column) for column in frame.columns])
    return WsvDocument([WsvLine(row) for row in rows])
