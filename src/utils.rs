/// Reports whether `c` is one of the Unicode whitespace code points recognized by WSV.
pub fn is_ord_whitespace(c: char) -> bool {
    let c = c as u32;
    c == 9
        || (11..=13).contains(&c)
        || matches!(c, 32 | 133 | 160 | 5760)
        || (8192..=8202).contains(&c)
        || matches!(c, 8232 | 8233 | 8239 | 8287 | 12288)
}

/// Reports whether `s` is non-empty and contains only whitespace characters.
pub fn is_string_whitespace(s: &str) -> bool {
    !s.is_empty() && s.chars().all(is_ord_whitespace)
}

/// Reports whether `value` contains a character that forces quoting on serialization.
pub fn contains_string_special_chars(value: &str) -> bool {
    value
        .chars()
        .any(|c| c == '\n' || is_ord_whitespace(c) || c == '"' || c == '#')
}

#[cfg(test)]
mod tests {
    use super::*;

    const WHITESPACES: [u32; 24] = [
        0x0009, 0x000B, 0x000C, 0x000D, 0x0020, 0x0085, 0x00A0, 0x1680, 0x2000, 0x2001, 0x2002,
        0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x2028, 0x2029, 0x202F,
        0x205F, 0x3000,
    ];

    #[test]
    fn matches_known_whitespace_table() {
        for c in 0u32..0xFFFF {
            let Some(ch) = char::from_u32(c) else {
                continue;
            };
            assert_eq!(is_ord_whitespace(ch), WHITESPACES.contains(&c), "codepoint {c:#x}");
        }
    }

    #[test]
    fn empty_string_is_not_whitespace() {
        assert!(!is_string_whitespace(""));
    }

    #[test]
    fn mixed_string_is_not_whitespace() {
        assert!(!is_string_whitespace(" a"));
        assert!(is_string_whitespace("   "));
    }

    #[test]
    fn special_chars_cover_whitespace_quote_and_hash() {
        assert!(contains_string_special_chars("a\nb"));
        assert!(contains_string_special_chars("a\"b"));
        assert!(contains_string_special_chars("a#b"));
        assert!(contains_string_special_chars("a b"));
        assert!(!contains_string_special_chars("abc"));
    }
}
