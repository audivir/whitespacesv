"""Base class for a TxtDocument and a TxtCharIterator."""

# ruff: noqa: PLR2004
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import Self, TypeAlias

if TYPE_CHECKING:
    from os import PathLike

StrPath: TypeAlias = "str | PathLike[str]"


def chars_to_ords(chars: str) -> list[int]:
    """Convert a string to a list of code points.

    Args:
        chars (str): The string to convert

    Returns:
        The list of code points
    """
    return [ord(c) for c in chars]


def ords_to_chars(ords: list[int]) -> str:
    """Convert a list of code points to a string.

    Args:
        ords (list[int]): The list of code points to convert

    Returns:
        the joined string
    """
    return "".join([chr(c) for c in ords])


class TxtDocument:
    """A class representing a text document."""

    def __init__(self, text: str = "") -> None:
        """Initializes the document with a text."""
        self._text = text

    @property
    def text(self) -> str:
        """The text of the document."""
        return self._text

    def save(self, file_path: StrPath) -> None:
        r"""Writes the text with '\\n' line endings to a file."""
        with open(file_path, "w", newline="\n", encoding="utf-8") as file:  # noqa: PTH123
            file.write(self._text)

    @classmethod
    def load(cls, file_path: StrPath) -> Self:
        """Loads a text document from a file.

        If the file has a utf-8 BOM, it is ignored.
        """
        text = Path(file_path).read_text(encoding="utf-8")

        # Allow for utf-8 BOM but ignore it
        if text and text[0] and text[0] == "\ufeff":
            text = text[1:]

        return cls(text)


class TxtCharIterator:
    """An iterator for a text."""

    def __init__(self, text: str) -> None:
        """Initializes the iterator with a text."""
        self._chars = chars_to_ords(text)
        self._ix = 0

    @property
    def ix(self) -> int:
        """The current index in the text."""
        return self._ix

    @property
    def chars(self) -> list[int]:
        """The list of code points."""
        return self._chars

    def forward(self) -> None:
        """Advances the iterator."""
        self._ix += 1

    def get_line_info(self) -> tuple[int, int]:
        """Returns the line index and the position in the line."""
        line_ix = 0
        line_position = 0
        for i in range(self._ix):
            if self._chars[i] == 0x0A:  # NEW_LINE
                line_ix += 1
                line_position = 0
            else:
                line_position += 1
        return line_ix, line_position

    def is_eof(self) -> bool:
        """True if the iterator is at the end of the text."""
        return self._ix >= len(self._chars)

    def is_char(self, c: int) -> bool:
        """True if the current character is c."""
        if self.is_eof():
            return False
        return self._chars[self._ix] == c

    def try_read_char(self, c: int) -> bool:
        """True if the current character is c and advances the iterator."""
        if not self.is_char(c):
            return False
        self.forward()
        return True


# ruff: noqa: ERA001
# NEW_LINE = 0x0A
# NEW_LINE_CHAR = "\n"
