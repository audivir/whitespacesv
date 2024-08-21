"""This module contains the WsvLine class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from whitespacesv.utils import is_string_whitespace

if TYPE_CHECKING:
    from collections.abc import Sequence


class WsvLine:
    """The WsvLine class represents a line in a WSV document."""

    def __init__(
        self,
        values: Sequence[str | None] | None = None,
        whitespaces: Sequence[str | None] | None = None,
        comment: str | None = None,
    ) -> None:
        """Initializes the WsvLine."""
        self.values = list(values) if values is not None else []

        WsvLine.validate_whitespaces(whitespaces)
        WsvLine.validate_comment(comment)

        self._whitespaces = list(whitespaces) if whitespaces is not None else None
        self._comment = comment

    @override
    def __repr__(self) -> str:
        return f"Line({self.values}, {self.whitespaces}, {self.comment})"

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, WsvLine):
            return False

        return (
            self.values == value.values  # noqa: PD011
            and self.whitespaces == value.whitespaces
            and self.comment == value.comment
        )

    @property
    def whitespaces(self) -> list[str | None] | None:
        """The whitespaces of the line."""
        return self._whitespaces

    @property
    def comment(self) -> str | None:
        """The comment of the line."""
        return self._comment

    @staticmethod
    def validate_whitespaces(whitespaces: Sequence[str | None] | None) -> None:
        """Validates the whitespaces: no non-whitespace character allowed."""
        if whitespaces is not None:
            for whitespace in whitespaces:
                if not whitespace:
                    continue

                if not is_string_whitespace(whitespace):
                    raise ValueError(
                        "Whitespace value contains non whitespace character/line feed"
                    )

    @staticmethod
    def validate_comment(comment: str | None) -> None:
        """Validates the comment: no line feed allowed."""
        if not comment:
            return

        if "\n" in comment:
            raise ValueError("Line feed in comment is not allowed")
