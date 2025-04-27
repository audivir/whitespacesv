"""Utility functions for the whitespacesv package."""

# ruff: noqa: PLR2004
from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from whitespacesv.txt import TxtCharIterator, chars_to_ords, ords_to_chars

if TYPE_CHECKING:
    import pandas as pd


def is_ord_whitespace(c: int) -> bool:
    """True if the character is a whitespace character."""
    return (
        c == 9
        or 11 <= c <= 13
        or c in {32, 133, 160, 5760}
        or 8192 <= c <= 8202
        or c in {8232, 8233, 8239, 8287, 12288}  # IDEOGRAPHIC_SPACE
    )


def is_string_whitespace(string: str) -> bool:
    """True if the string is non-empty and contains only whitespace characters."""
    if not string:
        return False
    ords = chars_to_ords(string)
    return all(is_ord_whitespace(c) for c in ords)


def contains_string_special_chars(value: str) -> bool:
    """True if the string contains special characters."""
    ords = chars_to_ords(value)

    return any(
        c == 10 or is_ord_whitespace(c) or c in {34, 35}  # HASH
        for c in ords
    )


class WsvParserError(Exception):
    """Exception raised when the WSV document could not be parsed."""

    def __init__(self, ix: int, line_ix: int, line_position: int, message: str) -> None:
        """Could not parse the WSV document.

        Raises with the line and position of the error

        Args:
            ix (int): The index of the error in the document
            line_ix (int): The line number of the error
            line_position (int): The position in the line of the error
            message (str): The error message
        """
        super().__init__(f"{message} ({line_ix + 1}, {line_position + 1})")
        self.ix = ix
        self.line_ix = line_ix
        self.line_position = line_position


class WsvCharIterator(TxtCharIterator):
    """An iterator for a WSV document."""

    def is_whitespace(self) -> bool:
        """True if at the current position is a whitespace character."""
        if self.is_eof():
            return False
        return is_ord_whitespace(self._chars[self.ix])

    def get_string(self, start_ix: int) -> str:
        """Returns the string from the start index to the current index."""
        part = self._chars[start_ix : self.ix]
        return ords_to_chars(part)

    def jump(self, eol: bool = False) -> int:
        """Jumps to the next whitespace or non-whitespace character.

        If eol is True, jumps to the next line.
        """
        start_ix = self.ix
        while True:
            if self.is_eof():
                break
            c = self._chars[self.ix]
            if c == 0x0A:  # NEW_LINE
                break
            if not eol and not is_ord_whitespace(c):
                break
            self.forward()

        return start_ix

    def read_comment_text(self) -> str:
        """Reads the comment text until the end of the line."""
        # we were at a hash and skipped to the next character
        # forward now until the end of the line
        start_ix = self.jump(eol=True)

        return self.get_string(start_ix)

    def read_whitespace_or_null(self) -> str | None:
        """Reads the whitespace until the next non-whitespace character."""
        start_ix = self.jump()

        if self.ix == start_ix:
            return None

        return self.get_string(start_ix)

    def get_exc(self, message: str) -> WsvParserError:
        """Returns a WsvParserException with the current line and position."""
        line_ix, line_position = self.get_line_info()
        return WsvParserError(self.ix, line_ix, line_position, message)

    def stop_read(self) -> bool:
        """True if the current character is hash/new line or EOF or whitespace."""
        return (
            self.is_whitespace()
            or self.is_char(0x23)  # HASH
            or self.is_end_of_section()
        )

    def is_end_of_section(self) -> bool:
        """1 if the current character is a new line, 2 if EOF, 0 otherwise."""
        return self.is_char(0x0A) or self.is_eof()  # NEW_LINE

    def read_string(self) -> str:
        """Reads the string until the next double quote."""
        chars: list[int] = []
        while True:
            # read string should have breaked earlier
            if self.is_end_of_section():  # NEW_LINE
                raise self.get_exc("String not closed")

            c = self._chars[self.ix]

            # NON QUOTED CHARACTERS
            if c != 0x22:  # DOUBLE_QUOTE
                chars.append(c)
                self.forward()
                continue
            # pylint: enable=consider-using-assignment-expr

            # BEGIN OF QUOTED SEQUENCE
            self.forward()

            if self.try_read_char(0x22):  # DOUBLE_QUOTE
                chars.append(0x22)  # DOUBLE_QUOTE

            elif self.try_read_char(0x2F):  # SLASH
                if not self.try_read_char(0x22):  # DOUBLE_QUOTE
                    raise self.get_exc("Invalid string line break")
                chars.append(0x0A)  # NEW_LINE

            elif self.stop_read():
                break

            else:
                raise self.get_exc("Invalid character after string")

        return ords_to_chars(chars)

    def read_value(self) -> str:
        """Reads the value until the next whitespace or new line."""
        start_ix = self.ix
        while True:
            if self.is_eof():
                break

            c = self._chars[self.ix]
            if is_ord_whitespace(c) or c in {10, 35}:  # NEW_LINE  # HASH
                break

            if c == 0x22:  # DOUBLE_QUOTE
                raise self.get_exc("Invalid double quote in value")

            self.forward()

        if self.ix == start_ix:
            raise self.get_exc("Invalid value")

        return self.get_string(start_ix)


def reinfer_types(df: pd.DataFrame) -> pd.DataFrame:
    """Infer the types of the DataFrame from a temporary CSV file."""
    import pandas as pd

    tmp = StringIO()
    df.to_csv(tmp, index=False)
    return pd.read_csv(StringIO(tmp.getvalue()))


# ruff: noqa: ERA001

# TAB = 0x09
# LINE_TAB = 0x0B
# FORM_FEED = 0x0C
# CARRIAGE_RETURN = 0x0D
# SPACE = 0x20
# NEXT_LINE = 0x85
# NO_BREAK_SPACE = 0xA0
# OGHAM_SPACE_MARK = 0x1680
# EN_QUAD = 0x2000
# EM_QUAD = 0x2001
# EN_SPACE = 0x2002
# EM_SPACE = 0x2003
# THREE_PER_EM_SPACE = 0x2004
# FOUR_PER_EM_SPACE = 0x2005
# SIX_PER_EM_SPACE = 0x2006
# FIGURE_SPACE = 0x2007
# PUNCTUATION_SPACE = 0x2008
# THIN_SPACE = 0x2009
# HAIR_SPACE = 0x200A
# LINE_SEPARATOR = 0x2028
# PARAGRAPH_SEPARATOR = 0x2029
# NARROW_NO_BREAK_SPACE = 0x202F
# MEDIUM_MATHEMATICAL_SPACE = 0x205F
# IDEOGRAPHIC_SPACE = 0x3000

# # see above for the constants
# WHITESPACES = [
# 0x0009,
# 0x000B,
# 0x000C,
# 0x000D,
# 0x0020,
# 0x0085,
# 0x00A0,
# 0x1680,
# 0x2000,
# 0x2001,
# 0x2002,
# 0x2003,
# 0x2004,
# 0x2005,
# 0x2006,
# 0x2007,
# 0x2008,
# 0x2009,
# 0x200A,
# 0x2028,
# 0x2029,
# 0x202F,
# 0x205F,
# 0x3000,
# ]
