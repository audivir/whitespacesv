# pylint: disable=invalid-name, missing-function-docstring, missing-module-docstring, consider-using-assignment-expr, protected-access, missing-class-docstring, attribute-defined-outside-init
from __future__ import annotations

from typing_extensions import override

from reliabletxt import (ReliableTxtCharIterator, ReliableTxtDocument,
                         ReliableTxtEncoding, StringUtil)


class WsvChar:
    @staticmethod
    def isWhitespace(c: int) -> bool:
        return (
            c == 0x09
            or (0x0B <= c <= 0x0D)
            or c == 0x0020
            or c == 0x0085
            or c == 0x00A0
            or c == 0x1680
            or (0x2000 <= c <= 0x200A)
            or c == 0x2028
            or c == 0x2029
            or c == 0x202F
            or c == 0x205F
            or c == 0x3000
        )

    @staticmethod
    def getWhitespaceCodePoints() -> list[int]:
        return [
            0x0009,
            0x000B,
            0x000C,
            0x000D,
            0x0020,
            0x0085,
            0x00A0,
            0x1680,
            0x2000,
            0x2001,
            0x2002,
            0x2003,
            0x2004,
            0x2005,
            0x2006,
            0x2007,
            0x2008,
            0x2009,
            0x200A,
            0x2028,
            0x2029,
            0x202F,
            0x205F,
            0x3000,
        ]


class WsvString:
    @staticmethod
    def isWhitespace(string: str) -> bool:
        if not string:
            return False
        codePoints = [ord(c) for c in string]

        return all(WsvChar.isWhitespace(c) for c in codePoints)


class WsvParserException(Exception):
    def __init__(self, index: int, lineIndex: int, linePosition: int, message: str):
        super().__init__(f"{message} ({lineIndex + 1}, {linePosition + 1})")
        self.index = index
        self.lineIndex = lineIndex
        self.linePosition = linePosition


class WsvCharIterator(ReliableTxtCharIterator):
    def __init__(self, text: str):
        ReliableTxtCharIterator.__init__(self, text)

    def isWhitespace(self) -> bool:
        if self.isEndOfText():
            return False
        return WsvChar.isWhitespace(self._chars[self._index])

    def getString(self, startIndex: int) -> str:
        part = self._chars[startIndex : self._index]
        return StringUtil.fromCodePoints(part)

    def readCommentText(self) -> str:
        startIndex = self._index
        while True:
            if self.isEndOfText():
                break
            if self._chars[self._index] == 0x0A:
                break
            self._index += 1

        return self.getString(startIndex)

    def skipCommentText(self) -> None:
        while True:
            if self.isEndOfText():
                break
            if self._chars[self._index] == 0x0A:
                break
            self._index += 1

    def readWhitespaceOrNull(self) -> str | None:
        startIndex = self._index
        while True:
            if self.isEndOfText():
                break
            c = self._chars[self._index]
            if c == 0x0A:
                break
            if not WsvChar.isWhitespace(c):
                break
            self._index += 1

        if self._index == startIndex:
            return None
        return self.getString(startIndex)

    def skipWhitespace(self) -> bool:
        startIndex = self._index
        while True:
            if self.isEndOfText():
                break
            c = self._chars[self._index]
            if c == 0x0A:
                break
            if not WsvChar.isWhitespace(c):
                break
            self._index += 1

        return self._index > startIndex

    def getException(self, message: str) -> WsvParserException:
        lineIndex, linePosition = self.getLineInfo()
        return WsvParserException(self._index, lineIndex, linePosition, message)

    def readString(self) -> str:
        chars = []
        while True:
            if self.isEndOfText() or self.isChar(0x0A):
                raise self.getException("String not closed")

            c = self._chars[self._index]
            if c == 0x22:
                self._index += 1
                if self.tryReadChar(0x22):
                    chars.append(0x22)
                elif self.tryReadChar(0x2F):
                    if not self.tryReadChar(0x22):
                        raise self.getException("Invalid string line break")
                    chars.append(0x0A)
                elif (
                    self.isWhitespace()
                    or self.isChar(0x0A)
                    or self.isChar(0x23)
                    or self.isEndOfText()
                ):
                    break
                else:
                    raise self.getException("Invalid character after string")
            else:
                chars.append(c)
                self._index += 1

        return StringUtil.fromCodePoints(chars)

    def readValue(self) -> str:
        startIndex = self._index
        while True:
            if self.isEndOfText():
                break

            c = self._chars[self._index]
            if WsvChar.isWhitespace(c) or c == 0x0A or c == 0x23:
                break

            if c == 0x22:
                raise self.getException("Invalid double quote in value")

            self._index += 1

        if self._index == startIndex:
            raise self.getException("Invalid value")

        return self.getString(startIndex)


class WsvParser:
    @staticmethod
    def parseLineAsArray(content: str) -> list[str | None]:
        iterator = WsvCharIterator(content)
        result = WsvParser._parseLineAsArray(iterator)
        if iterator.isChar(0x0A):
            raise iterator.getException("Multiple WSV lines not allowed")

        if not iterator.isEndOfText():
            raise iterator.getException("Unexpected parser error")

        return result

    @staticmethod
    def _parseLineAsArray(iterator: WsvCharIterator) -> list[str | None]:
        iterator.skipWhitespace()
        values = []
        while (not iterator.isChar(0x0A)) and (not iterator.isEndOfText()):
            value = None
            if iterator.isChar(0x23):
                break

            if iterator.tryReadChar(0x22):
                value = iterator.readString()
            else:
                value = iterator.readValue()
                if value == "-":
                    value = None

            values.append(value)

            if not iterator.skipWhitespace():
                break

        if iterator.tryReadChar(0x23):
            iterator.skipCommentText()

        return values

    @staticmethod
    def parseDocumentAsJaggedArray(content: str) -> list[list[str | None]]:
        iterator = WsvCharIterator(content)
        lines = []

        while True:
            newLine = WsvParser._parseLineAsArray(iterator)
            lines.append(newLine)

            if iterator.isEndOfText():
                break

            if not iterator.tryReadChar(0x0A):
                raise iterator.getException("Unexpected parser error")

        if not iterator.isEndOfText():
            raise iterator.getException("Unexpected parser error")

        return lines

    @staticmethod
    def parseLine(content: str) -> WsvLine:
        iterator = WsvCharIterator(content)
        result = WsvParser._parseLine(iterator)
        if iterator.isChar(0x0A):
            raise iterator.getException("Multiple WSV lines not allowed")

        if not iterator.isEndOfText():
            raise iterator.getException("Unexpected parser error")

        return result

    @staticmethod
    def _parseLine(iterator: WsvCharIterator) -> WsvLine:
        values = []
        whitespaces = []

        whitespace = iterator.readWhitespaceOrNull()
        whitespaces.append(whitespace)

        while (not iterator.isChar(0x0A)) and (not iterator.isEndOfText()):
            value = None
            if iterator.isChar(0x23):
                break

            if iterator.tryReadChar(0x22):
                value = iterator.readString()
            else:
                value = iterator.readValue()
                if value == "-":
                    value = None

            values.append(value)

            whitespace = iterator.readWhitespaceOrNull()
            if whitespace is None:
                break

            whitespaces.append(whitespace)

        comment = None
        if iterator.tryReadChar(0x23):
            comment = iterator.readCommentText()
            if whitespace is None:
                whitespaces.append(None)

        newLine = WsvLine(values)
        newLine._whitespaces = whitespaces
        newLine._comment = comment
        return newLine

    @staticmethod
    def parseDocument(content: str) -> WsvDocument:
        document = WsvDocument()
        iterator = WsvCharIterator(content)

        while True:
            newLine = WsvParser._parseLine(iterator)
            document.addLine(newLine)

            if iterator.isEndOfText():
                break

            if not iterator.tryReadChar(0x0A):
                raise iterator.getException("Unexpected parser error")

        if not iterator.isEndOfText():
            raise iterator.getException("Unexpected parser error")

        return document

    @staticmethod
    def parseLineNonPreserving(content: str) -> WsvLine:
        values = WsvParser.parseLineAsArray(content)
        return WsvLine(values)

    @staticmethod
    def parseDocumentNonPreserving(content: str) -> WsvDocument:
        document = WsvDocument()
        iterator = WsvCharIterator(content)

        while True:
            lineValues = WsvParser._parseLineAsArray(iterator)
            newLine = WsvLine(lineValues)
            document.addLine(newLine)

            if iterator.isEndOfText():
                break

            if not iterator.tryReadChar(0x0A):
                raise iterator.getException("Unexpected parser error")

        if not iterator.isEndOfText():
            raise iterator.getException("Unexpected parser error")

        return document


class WsvSerializer:
    @staticmethod
    def containsSpecialChar(value: str) -> bool:
        chars = StringUtil.getCodePoints(value)

        return any(
            c == 0x0A or WsvChar.isWhitespace(c) or c == 0x22 or c == 0x23
            for c in chars
        )

    @staticmethod
    def serializeValue(value: str | None) -> str:
        if value is None:
            return "-"

        if len(value) == 0:
            return '""'

        if value == "-":
            return '"-"'

        if WsvSerializer.containsSpecialChar(value):
            result = []
            chars = StringUtil.getCodePoints(value)
            result.append(0x22)
            for c in chars:
                if c == 0x0A:
                    result.append(0x22)
                    result.append(0x2F)
                    result.append(0x22)
                elif c == 0x22:
                    result.append(0x22)
                    result.append(0x22)
                else:
                    result.append(c)
            result.append(0x22)
            return StringUtil.fromCodePoints(result)

        return value

    @staticmethod
    def _serializeWhitespace(whitespace: str | None, isRequired: bool) -> str:
        if whitespace is not None and len(whitespace) > 0:
            return whitespace

        if isRequired:
            return " "

        return ""

    @staticmethod
    def _serializeValuesWithWhitespace(line: WsvLine) -> str:
        result = ""
        whitespaces = line._whitespaces

        if whitespaces is None:
            raise ValueError("Whitespace array is not set")

        comment = line._comment
        if not line.hasValues():
            whitespace = whitespaces[0]
            result += WsvSerializer._serializeWhitespace(whitespace, False)
            return result

        for i, value in enumerate(line.values):
            whitespace = None
            if i < len(whitespaces):
                whitespace = whitespaces[i]

            if i == 0:
                result += WsvSerializer._serializeWhitespace(whitespace, False)
            else:
                result += WsvSerializer._serializeWhitespace(whitespace, True)

            result += WsvSerializer.serializeValue(value)

        if len(whitespaces) >= len(line.values) + 1:
            whitespace = whitespaces[len(line.values)]
            result += WsvSerializer._serializeWhitespace(whitespace, False)
        elif comment is not None and line.hasValues():
            result += " "

        return result

    @staticmethod
    def _serializeValuesWithoutWhitespace(line: WsvLine) -> str:
        result = ""

        if not line.hasValues():
            return result

        isFollowingValue = False
        for value in line.values:
            if isFollowingValue:
                result += " "
            else:
                isFollowingValue = True

            result += WsvSerializer.serializeValue(value)

        if line.getComment() is not None and len(line.values) > 0:
            result += " "

        return result

    @staticmethod
    def serializeLine(line: WsvLine) -> str:
        result = ""
        whitespaces = line._whitespaces
        if whitespaces is not None and len(whitespaces) > 0:
            result += WsvSerializer._serializeValuesWithWhitespace(line)
        else:
            result += WsvSerializer._serializeValuesWithoutWhitespace(line)

        comment = line._comment
        if comment is not None:
            result += "#"
            result += comment

        return result

    @staticmethod
    def serializeLineValues(values: list[str | None]) -> str:
        result = ""
        isFirstValue = True
        for value in values:
            if not isFirstValue:
                result += " "
            else:
                isFirstValue = False

            result += WsvSerializer.serializeValue(value)

        return result

    @staticmethod
    def serializeLineNonPreserving(line: WsvLine) -> str:
        return WsvSerializer.serializeLineValues(line.values)

    @staticmethod
    def serializeDocument(document: WsvDocument) -> str:
        result = ""
        isFirstLine = True
        for line in document.lines:
            if not isFirstLine:
                result += "\n"
            else:
                isFirstLine = False

            result += WsvSerializer.serializeLine(line)

        return result

    @staticmethod
    def serializeDocumentNonPreserving(document: WsvDocument) -> str:
        result = ""
        isFirstLine = True
        for line in document.lines:
            if not isFirstLine:
                result += "\n"
            else:
                isFirstLine = False

            result += WsvSerializer.serializeLineNonPreserving(line)

        return result


class WsvLine:
    def __init__(
        self,
        values: list[str | None] | None = None,
        whitespaces: list[str | None] | None = None,
        comment: str | None = None,
    ):
        if values is None:
            self.values = []
        else:
            self.values = values
        self.setWhitespaces(whitespaces)
        self.setComment(comment)

    def hasValues(self) -> bool:
        return bool(self.values)

    def setWhitespaces(self, whitespaces: list[str | None] | None) -> None:
        WsvLine.validateWhitespaces(whitespaces)
        self._whitespaces = whitespaces

    def setComment(self, comment: str | None) -> None:
        WsvLine.validateComment(comment)
        self._comment = comment

    @staticmethod
    def validateWhitespaces(whitespaces: list[str | None] | None) -> None:
        if whitespaces is not None:
            for whitespace in whitespaces:
                if (
                    whitespace is not None
                    and len(whitespace) > 0
                    and not WsvString.isWhitespace(whitespace)
                ):
                    raise ValueError(
                        "Whitespace value contains non whitespace character/line feed"
                    )

    @staticmethod
    def validateComment(comment: str | None) -> None:
        if comment is not None and comment.find("\n") >= 0:
            raise ValueError("Line feed in comment is not allowed")

    def getWhitespaces(self) -> list[str | None] | None:
        return self._whitespaces

    def getComment(self) -> str | None:
        return self._comment

    @staticmethod
    def parse(content: str, preserveWhitespaceAndComment: bool = True) -> WsvLine:
        if preserveWhitespaceAndComment:
            return WsvParser.parseLine(content)

        return WsvParser.parseLineNonPreserving(content)

    @staticmethod
    def parseAsArray(content: str) -> list[str | None]:
        return WsvParser.parseLineAsArray(content)

    @override
    def __str__(self) -> str:
        return self.toString(True)

    def toString(self, preserveWhitespaceAndComment: bool) -> str:
        if preserveWhitespaceAndComment:
            return WsvSerializer.serializeLine(self)

        return WsvSerializer.serializeLineNonPreserving(self)

    def _set(
        self,
        values: list[str | None],
        whitespaces: list[str | None],
        comment: str | None,
    ) -> None:
        self.values = values
        self._whitespaces = whitespaces
        self._comment = comment


class WsvDocument:
    def __init__(
        self,
        lines: list[WsvLine] | None = None,
        encoding: ReliableTxtEncoding = ReliableTxtEncoding.UTF_8,
    ):
        if lines is None:
            self.lines = []
        else:
            self.lines = lines
        self.encoding = encoding

    def setEncoding(self, encoding: ReliableTxtEncoding) -> None:
        self.encoding = encoding

    def getEncoding(self) -> ReliableTxtEncoding:
        return self.encoding

    def addLine(self, line: WsvLine) -> None:
        self.lines.append(line)

    @override
    def __str__(self) -> str:
        return self.toString()

    def toString(self, preserveWhitespaceAndComments: bool = True) -> str:
        if preserveWhitespaceAndComments:
            return WsvSerializer.serializeDocument(self)

        return WsvSerializer.serializeDocumentNonPreserving(self)

    def toArray(self) -> list[list[str | None]]:
        array = []
        for line in self.lines:
            array.append(line.values)
        return array

    def save(self, filePath: str, preserveWhitespaceAndComments: bool = True) -> None:
        content = self.toString(preserveWhitespaceAndComments)
        file = ReliableTxtDocument(content, self.encoding)
        file.save(filePath)

    @staticmethod
    def parse(content: str, preserveWhitespaceAndComments: bool = True) -> WsvDocument:
        if preserveWhitespaceAndComments:
            return WsvParser.parseDocument(content)

        return WsvParser.parseDocumentNonPreserving(content)

    @staticmethod
    def load(filePath: str, preserveWhitespaceAndComments: bool = True) -> WsvDocument:
        file = ReliableTxtDocument.load(filePath)
        content = file.getText()
        document = WsvDocument.parse(content, preserveWhitespaceAndComments)
        document.setEncoding(file.getEncoding())
        return document

    @staticmethod
    def parseAsJaggedArray(content: str) -> list[list[str | None]]:
        return WsvParser.parseDocumentAsJaggedArray(content)
