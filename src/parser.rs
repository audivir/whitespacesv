use pyo3::PyErr;

use crate::iterator::WsvCharIterator;
use crate::line::WsvLine;

fn parse_value_wrapper(it: &mut WsvCharIterator<'_>) -> Result<Option<String>, PyErr> {
    if it.try_read_char('"') {
        return Ok(Some(it.read_string()?));
    }
    let value = it.read_value()?;
    if value == "-" {
        return Ok(None);
    }
    Ok(Some(value))
}

fn try_parse_comment(
    it: &mut WsvCharIterator<'_>,
    whitespace: &Option<String>,
    whitespaces: &mut Vec<Option<String>>,
) -> Option<String> {
    if !it.try_read_char('#') {
        return None;
    }
    let comment = it.read_comment_text();
    if whitespace.is_none() {
        whitespaces.push(None);
    }
    Some(comment)
}

fn parse_line(it: &mut WsvCharIterator<'_>) -> Result<WsvLine, PyErr> {
    let mut values: Vec<Option<String>> = Vec::new();
    let mut whitespaces: Vec<Option<String>> = Vec::new();

    let mut whitespace = it.read_whitespace_or_null();
    whitespaces.push(whitespace.clone());

    let mut comment: Option<String> = None;

    while !it.is_end_of_section() {
        let found = try_parse_comment(it, &whitespace, &mut whitespaces);
        let stops = matches!(&found, Some(text) if !text.is_empty());
        comment = found;
        if stops {
            break;
        }

        let value = parse_value_wrapper(it)?;
        values.push(value);

        let found = try_parse_comment(it, &whitespace, &mut whitespaces);
        let stops = matches!(&found, Some(text) if !text.is_empty());
        comment = found;
        if stops {
            break;
        }

        whitespace = it.read_whitespace_or_null();
        match &whitespace {
            None => break,
            Some(_) => whitespaces.push(whitespace.clone()),
        }
    }

    Ok(WsvLine::new_unchecked(values, Some(whitespaces), comment))
}

/// Parses `text` into WSV lines, preserving original whitespace and comments.
///
/// # Errors
///
/// Returns `Err` (a `WsvParserError`) at the first malformed value, unterminated string, or
/// invalid escape sequence encountered.
pub fn parse_lines(text: &str) -> Result<Vec<WsvLine>, PyErr> {
    let mut lines = Vec::new();
    let mut it = WsvCharIterator::new(text);

    while !it.is_eof() {
        lines.push(parse_line(&mut it)?);
        it.forward();
    }

    Ok(lines)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_value_wrapper_maps_dash_to_none() {
        let mut it = WsvCharIterator::new("-");
        assert_eq!(parse_value_wrapper(&mut it).unwrap(), None);

        let mut it = WsvCharIterator::new("\"test test\"");
        assert_eq!(parse_value_wrapper(&mut it).unwrap(), Some("test test".to_string()));
    }

    #[test]
    fn empty_text_yields_no_lines() {
        assert_eq!(parse_lines("").unwrap(), Vec::new());
    }

    #[test]
    fn text_without_trailing_newline_yields_one_line() {
        let lines = parse_lines("a b").unwrap();
        assert_eq!(lines.len(), 1);
        assert_eq!(
            lines[0].values,
            vec![Some("a".to_string()), Some("b".to_string())]
        );
    }

    #[test]
    fn parses_values_whitespace_and_comment() {
        let lines = parse_lines("a \tb c #comment\n").unwrap();
        assert_eq!(lines.len(), 1);
        let first = &lines[0];
        assert_eq!(
            first.values,
            vec![Some("a".to_string()), Some("b".to_string()), Some("c".to_string())]
        );
        assert_eq!(first.comment_ref(), Some("comment"));
    }
}
