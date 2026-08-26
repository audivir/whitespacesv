from _typeshed import StrPath
from typing_extensions import Self, override

class WsvLine:
    """Stores the values, whitespaces, and trailing comment of a single WSV line."""

    values: list[str | None]

    def __init__(
        self,
        values: list[str | None] | None = None,
        whitespaces: list[str | None] | None = None,
        comment: str | None = None,
    ) -> None:
        """Creates a line from optional values, whitespaces, and a trailing comment.

        Raises:
            ValueError: If a whitespace entry contains a non-whitespace character, or comment
                contains a line feed.
        """
    @property
    def whitespaces(self) -> list[str | None] | None:
        """Raw whitespace strings between values, if the line retains them."""
    @property
    def comment(self) -> str | None:
        """Trailing comment text, if the line has one."""
    @override
    def __eq__(self, value: object) -> bool: ...
    @staticmethod
    def validate_whitespaces(whitespaces: list[str | None] | None) -> None:
        """Checks that every entry in whitespaces contains only whitespace characters.

        Raises:
            ValueError: If an entry contains a non-whitespace character.
        """
    @staticmethod
    def validate_comment(comment: str | None) -> None:
        """Checks that comment contains no line feed.

        Raises:
            ValueError: If comment contains a line feed.
        """

class WsvDocument:
    """Manages an ordered collection of WSV lines and their (de)serialization."""

    lines: list[WsvLine]

    def __init__(self, lines: list[WsvLine] | None = None) -> None:
        """Creates a document from the given lines, or an empty document if none are given."""
    @override
    def __eq__(self, value: object) -> bool: ...
    @classmethod
    def parse(cls, text: str) -> Self:
        """Parses text into a document, preserving original whitespace and comments.

        Raises:
            WsvParserError: If text is not valid WSV.
        """
    def serialize(self, mode: str = "preserve") -> list[str]:
        """Serializes the lines to a list of strings using the given mode.

        Raises:
            ValueError: If mode is not one of "preserve", "compact", or "pretty".
        """
    @classmethod
    def load(cls, file_path: StrPath) -> Self:
        """Loads a document from file_path, stripping a leading UTF-8 BOM if present.

        Raises:
            ValueError: If the file is empty or does not end with a newline.
            WsvParserError: If the file content is not valid WSV.
        """
    def to_string(self, mode: str = "preserve") -> str:
        """Serializes the document to a single newline-terminated string.

        Raises:
            ValueError: If mode is not one of "preserve", "compact", or "pretty".
        """
    def save(self, file_path: StrPath, mode: str = "preserve") -> None:
        """Saves the document to file_path with a trailing newline.

        Raises:
            ValueError: If the document has no lines, or mode is invalid.
        """

class WsvParserError(Exception):
    """The WSV document could not be parsed at the given position."""

    ix: int
    line_ix: int
    line_position: int
