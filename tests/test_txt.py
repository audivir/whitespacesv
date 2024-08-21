"""Tests for whitespacesv.txt module."""

from __future__ import annotations

import tempfile

import pytest

from whitespacesv.txt import TxtCharIterator, TxtDocument, chars_to_ords, ords_to_chars


@pytest.mark.parametrize(
    ("chars", "expected_result"), [("abc", [97, 98, 99]), ("", [])]
)
def test_chars_to_ords(chars: str, expected_result: list[int]) -> None:
    assert chars_to_ords(chars) == expected_result


@pytest.mark.parametrize(("ords", "expected_result"), [([97, 98, 99], "abc"), ([], "")])
def test_ords_to_chars(ords: list[int], expected_result: str) -> None:
    assert ords_to_chars(ords) == expected_result


@pytest.mark.parametrize(("text", "content"), [("abc", b"abc"), ("", b""), (None, b"")])
def test_reliable_txt_document(text: str | None, content: bytes) -> None:
    doc = TxtDocument() if text is None else TxtDocument(text)
    safe_text = content.decode("utf-8")
    assert doc.text == safe_text

    with tempfile.NamedTemporaryFile("w") as temp:
        doc.save(temp.name)
        assert TxtDocument.load(temp.name).text == safe_text


def test_rel_txt_char_iterator() -> None:
    it = TxtCharIterator("abc")
    assert it.chars == [97, 98, 99]
    assert it.ix == 0
    it.forward()
    assert it.ix == 1

    it = TxtCharIterator("a")
    assert not it.is_eof()
    assert it.is_char(0x61)
    it.forward()
    assert it.is_eof()
    assert not it.is_char(0x61)

    it = TxtCharIterator("a")
    assert it.is_char(0x61)
    assert it.ix == 0
    assert it.try_read_char(0x61)
    assert it.ix == 1


@pytest.mark.parametrize(
    ("text", "steps", "expected"), [("abc\ndef", 2, (0, 2)), ("abc\ndef", 7, (1, 3))]
)
def test_get_line_info(text: str, steps: int, expected: tuple[int, int]) -> None:
    it = TxtCharIterator(text)
    for _ in range(steps):
        it.forward()
    assert it.get_line_info() == expected
