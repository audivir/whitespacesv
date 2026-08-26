use pyo3::PyErr;

use crate::error::parser_error;
use crate::utils::is_ord_whitespace;

const NEW_LINE: char = '\n';
const DOUBLE_QUOTE: char = '"';
const HASH: char = '#';
const SLASH: char = '/';

/// Byte-offset cursor over WSV document text, decoding one Unicode scalar value at a time.
pub struct WsvCharIterator<'a> {
    text: &'a str,
    ix: usize,
}

impl<'a> WsvCharIterator<'a> {
    pub fn new(text: &'a str) -> Self {
        Self { text, ix: 0 }
    }

    fn current(&self) -> Option<char> {
        self.text[self.ix..].chars().next()
    }

    pub fn forward(&mut self) {
        if let Some(c) = self.current() {
            self.ix += c.len_utf8();
        }
    }

    pub fn is_eof(&self) -> bool {
        self.ix >= self.text.len()
    }

    pub fn is_char(&self, c: char) -> bool {
        self.current() == Some(c)
    }

    pub fn try_read_char(&mut self, c: char) -> bool {
        if !self.is_char(c) {
            return false;
        }
        self.forward();
        true
    }

    pub fn is_whitespace(&self) -> bool {
        self.current().is_some_and(is_ord_whitespace)
    }

    pub fn is_end_of_section(&self) -> bool {
        self.is_char(NEW_LINE) || self.is_eof()
    }

    pub fn stop_read(&self) -> bool {
        self.is_whitespace() || self.is_char(HASH) || self.is_end_of_section()
    }

    pub fn get_string(&self, start_ix: usize) -> String {
        self.text[start_ix..self.ix].to_string()
    }

    fn jump(&mut self, eol: bool) -> usize {
        let start_ix = self.ix;
        while let Some(c) = self.current() {
            if c == NEW_LINE || (!eol && !is_ord_whitespace(c)) {
                break;
            }
            self.forward();
        }
        start_ix
    }

    pub fn read_comment_text(&mut self) -> String {
        let start_ix = self.jump(true);
        self.get_string(start_ix)
    }

    pub fn read_whitespace_or_null(&mut self) -> Option<String> {
        let start_ix = self.jump(false);
        if self.ix == start_ix {
            return None;
        }
        Some(self.get_string(start_ix))
    }

    /// Returns the zero-based line index and in-line character position of the cursor.
    pub fn get_line_info(&self) -> (usize, usize) {
        let consumed = &self.text[..self.ix];
        let line_ix = consumed.matches(NEW_LINE).count();
        let line_position = consumed.rsplit(NEW_LINE).next().unwrap_or("").chars().count();
        (line_ix, line_position)
    }

    pub fn get_exc(&self, message: &str) -> PyErr {
        let (line_ix, line_position) = self.get_line_info();
        let char_ix = self.text[..self.ix].chars().count();
        parser_error(char_ix, line_ix, line_position, message)
    }

    /// Reads a double-quoted string starting after the opening quote.
    ///
    /// # Errors
    ///
    /// Returns `Err` if the string is unterminated, an escaped line break is malformed, or a
    /// character other than a quote or slash follows a closing quote.
    pub fn read_string(&mut self) -> Result<String, PyErr> {
        let mut result = String::new();
        loop {
            if self.is_end_of_section() {
                return Err(self.get_exc("String not closed"));
            }
            let c = self.current().expect("checked by is_end_of_section");
            if c != DOUBLE_QUOTE {
                result.push(c);
                self.forward();
                continue;
            }
            self.forward();

            if self.try_read_char(DOUBLE_QUOTE) {
                result.push(DOUBLE_QUOTE);
            } else if self.try_read_char(SLASH) {
                if !self.try_read_char(DOUBLE_QUOTE) {
                    return Err(self.get_exc("Invalid string line break"));
                }
                result.push(NEW_LINE);
            } else if self.stop_read() {
                break;
            } else {
                return Err(self.get_exc("Invalid character after string"));
            }
        }
        Ok(result)
    }

    /// Reads an unquoted value up to the next whitespace, newline, or hash.
    ///
    /// # Errors
    ///
    /// Returns `Err` if a double quote appears inside the value, or the value is empty.
    pub fn read_value(&mut self) -> Result<String, PyErr> {
        let start_ix = self.ix;
        while let Some(c) = self.current() {
            if is_ord_whitespace(c) || c == NEW_LINE || c == HASH {
                break;
            }
            if c == DOUBLE_QUOTE {
                return Err(self.get_exc("Invalid double quote in value"));
            }
            self.forward();
        }
        if self.ix == start_ix {
            return Err(self.get_exc("Invalid value"));
        }
        Ok(self.get_string(start_ix))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn jump_stops_before_newline_unless_eol() {
        let mut it = WsvCharIterator::new("a b c");
        it.forward();
        let start = it.jump(false);
        assert_eq!(start, 1);
        assert_eq!(it.ix, 2);
    }

    #[test]
    fn read_whitespace_or_null_returns_none_at_non_whitespace() {
        let mut it = WsvCharIterator::new(" a");
        assert_eq!(it.read_whitespace_or_null(), Some(" ".to_string()));
        assert_eq!(it.read_whitespace_or_null(), None);
    }

    #[test]
    fn line_info_tracks_newlines_in_char_units() {
        let mut it = WsvCharIterator::new("abc\ndef");
        for _ in 0..7 {
            it.forward();
        }
        assert_eq!(it.get_line_info(), (1, 3));
    }

    #[test]
    fn line_info_counts_multibyte_chars_not_bytes() {
        let mut it = WsvCharIterator::new("\u{3000}\u{3000}a");
        for _ in 0..3 {
            it.forward();
        }
        assert_eq!(it.get_line_info(), (0, 3));
    }

    #[test]
    fn read_string_handles_escapes() {
        let mut it = WsvCharIterator::new("\"hegd\"\"\"");
        it.try_read_char('"');
        assert_eq!(it.read_string().unwrap(), "hegd\"");

        let mut it = WsvCharIterator::new("\"heg\"/\"d\"");
        it.try_read_char('"');
        assert_eq!(it.read_string().unwrap(), "heg\nd");

        let mut it = WsvCharIterator::new("\"heg");
        it.try_read_char('"');
        assert!(it.read_string().is_err());

        let mut it = WsvCharIterator::new("\"heg\"f");
        it.try_read_char('"');
        assert!(it.read_string().is_err());
    }

    #[test]
    fn read_value_stops_at_special_chars() {
        assert_eq!(WsvCharIterator::new("a#").read_value().unwrap(), "a");
        assert_eq!(WsvCharIterator::new("a\n").read_value().unwrap(), "a");
        assert!(WsvCharIterator::new("a\"").read_value().is_err());
        assert!(WsvCharIterator::new("").read_value().is_err());
    }
}
