"""The document module of the whitespacesv package."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

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


class WsvDocument:
    """A class representing a WSV document."""

    def __init__(
        self,
        lines: Sequence[WsvLine] | None = None,
    ):
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

    def serialize(self, mode: SerializationMode | str = "preserve") -> list[str]:
        """Serializes the lines.

        Args:
            mode:
                The serialization mode,
                for more information see :class:`SerializationMode`

        Returns:
            A list of serialized lines
        """
        if isinstance(mode, str):
            mode = SerializationMode(mode)

        values = [
            [serialize_value(value) for value in line.values] for line in self.lines
        ]

        SM = SerializationMode

        if mode == SM.COMPACT or mode == SM.PRETTY:  # pylint: disable=consider-using-in
            if mode == SM.COMPACT:
                serialized = [" ".join(x) for x in values]
            else:
                serialized = prettify_values(
                    values, [line.comment for line in self.lines]
                )
        else:
            serialized = [
                serialize_line(line_values, line.whitespaces, line.comment)
                for line_values, line in zip(values, self.lines)
            ]

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
        doc = cls.parse(file.text)
        return doc

    def to_string(
        self, mode: Literal["preserve", "compact", "pretty"] = "preserve"
    ) -> str:
        """Serializes the document to a string.

        Args:
            mode:
                The serialization mode,
                for more information see :class:`SerializationMode`

        Returns:
            The serialized string
        """
        return "\n".join(self.serialize(mode)) + "\n"

    def save(
        self,
        file_path: StrPath,
        mode: Literal["preserve", "compact", "pretty"] = "preserve",
    ) -> None:
        """Saves the document to a file with a new line appended

        Args:
            file_path:
                The path to the file to save
            mode:
                The serialization mode,
                for more information see :class:`SerializationMode`
        """
        if not self.lines:
            raise ValueError("Can't save empty document")
        content = self.to_string(mode)
        file = TxtDocument(content)
        file.save(file_path)

    def to_pandas(self, header: bool = True, infer_types: bool = True) -> pd.DataFrame:
        """Converts the document to a pandas DataFrame

        Args:
            header:
                Whether the first row is the header
            infer_types:
                Whether to infer the types of the columns.
                For more information see :func:`reinfer_types`
        """
        # skip empty rows
        values = [x.values for x in self.lines if x.values]

        if header:
            columns, values = values[0], values[1:]
        else:
            columns = None

        df = pd.DataFrame(values, columns=columns)

        if infer_types:
            return reinfer_types(df)

        return df

    @classmethod
    def from_pandas(cls, df: pd.DataFrame, header: bool = True) -> Self:
        """Converts the DataFrame to the document

        If header is True, the column names are added as the first row.
        """
        # all except nan or None to string
        df = df.copy()

        values = list(df.itertuples(index=False, name=None))
        values = [[str(x) if pd.notna(x) else None for x in row] for row in values]
        if header:
            values.insert(0, list(df.columns))
        lines = [WsvLine(x) for x in values]
        return cls(lines)
