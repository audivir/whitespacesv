"""The document module of the whitespacesv package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd
from typing_extensions import Self, override

from whitespacesv.line import WsvLine
from whitespacesv.parser import parse_lines
from whitespacesv.serializer import (
    SerializationMode,
    prettify_values,
    serialize_line,
    serialize_value,
)
from whitespacesv.txt import StrPath, TxtDocument
from whitespacesv.utils import reinfer_types

if TYPE_CHECKING:
    from collections.abc import Sequence

SM = SerializationMode


class WsvDocument:
    """A class representing a WSV document."""

    def __init__(self, lines: Sequence[WsvLine] | None = None) -> None:
        """Initializes the WSV document.

        Args:
            lines:
                The lines of the document.
                If no lines are provided, an empty document is created
        """
        self.lines = list(lines) if lines is not None else []

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, WsvDocument):
            return False

        return self.lines == value.lines

    @override
    def __repr__(self) -> str:
        return f"Document(lines={self.lines})"

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parses the content to a WsvDocument.

        Args:
            text:
                The text to parse

        Returns:
            The parsed WsvDocument
        """
        lines = parse_lines(text)
        return cls(lines)

    def serialize(
        self,
        mode: Literal["preserve", "compact", "pretty"] | SerializationMode = "preserve",
    ) -> list[str]:
        """Serializes the lines.

        Args:
            mode: If mode is `preserve`, the values are serialized
                with the original whitespaces and comments.
                If mode is `compact`, the values are serialized
                without whitespaces and comments.
                If mode is `pretty`, the values are serialized with
                a minimum of whitespaces and the original comments.

        Returns:
            A list of serialized lines
        """
        mode = SerializationMode(mode)

        values = [
            [serialize_value(value) for value in line.values]  # noqa: PD011
            for line in self.lines
        ]

        if mode == SM.COMPACT:
            serialized = [" ".join(x) for x in values]
        elif mode == SM.PRETTY:
            serialized = prettify_values(values, [line.comment for line in self.lines])
        elif mode == SM.PRESERVE:
            serialized = [
                serialize_line(line_values, line.whitespaces, line.comment)
                for line_values, line in zip(values, self.lines, strict=False)
            ]
        else:
            raise RuntimeError(f"Invalid mode: {mode}")  # pragma: no cover

        return serialized

    @classmethod
    def load(cls, file_path: StrPath) -> Self:
        """Loads the content from a file into a WsvDocument.

        Args:
            file_path:
                The path to the file to load

        Returns:
            The WsvDocument
        """
        file = TxtDocument.load(file_path)
        text = file.text
        if not text or not text[-1] == "\n":
            raise ValueError("Empty file or no new line at the end")
        return cls.parse(file.text)

    def to_string(
        self, mode: Literal["preserve", "compact", "pretty"] = "preserve"
    ) -> str:
        """Serializes the document to a string.

        Args:
            mode:
                The serialization mode,
                for more information see `SerializationMode`

        Returns:
            The serialized string
        """
        return "\n".join(self.serialize(mode)) + "\n"

    def save(
        self,
        file_path: StrPath,
        mode: Literal["preserve", "compact", "pretty"] = "preserve",
    ) -> None:
        """Saves the document to a file with a new line appended.

        Args:
            file_path:
                The path to the file to save
            mode:
                The serialization mode,
                for more information see `SerializationMode`
        """
        if not self.lines:
            raise ValueError("Can't save empty document")
        content = self.to_string(mode)
        file = TxtDocument(content)
        file.save(file_path)

    def to_pandas(self, header: bool = True, infer_types: bool = True) -> pd.DataFrame:
        """Converts the document to a pandas DataFrame.

        Args:
            header:
                Whether the first row is the header
            infer_types:
                Whether to infer the types of the columns.
                For more information see `reinfer_types`
        """
        # skip empty rows
        values = [x.values for x in self.lines if x.values]  # noqa: PD011

        if header:
            columns, values = values[0], values[1:]
        else:
            columns = None

        output_df = pd.DataFrame(values, columns=columns)

        if infer_types:
            return reinfer_types(output_df)

        return output_df

    @classmethod
    def from_pandas(cls, input_df: pd.DataFrame, header: bool = True) -> Self:
        """Converts the DataFrame to the document.

        If header is True, the column names are added as the first row.
        """
        # all except nan or None to string
        input_df = input_df.copy()

        values = list(input_df.itertuples(index=False, name=None))
        values = [[str(x) if pd.notna(x) else None for x in row] for row in values]
        if header:
            values.insert(0, list(input_df.columns))
        lines = [WsvLine(x) for x in values]
        return cls(lines)
