use crate::utils::contains_string_special_chars;

/// Serializes a single value, quoting and escaping it if required.
pub fn serialize_value(value: Option<&str>) -> String {
    let Some(value) = value else {
        return "-".to_string();
    };

    if value == "-" {
        return "\"-\"".to_string();
    }

    if value.is_empty() {
        return "\"\"".to_string();
    }

    if !contains_string_special_chars(value) {
        return value.to_string();
    }

    let mut result = String::with_capacity(value.len() + 2);
    result.push('"');
    for c in value.chars() {
        match c {
            '\n' => result.push_str("\"/\""),
            '"' => result.push_str("\"\""),
            other => result.push(other),
        }
    }
    result.push('"');
    result
}

fn serialize_whitespace(whitespace: Option<&str>, is_required: bool) -> &str {
    match whitespace {
        Some(w) => w,
        None if is_required => " ",
        None => "",
    }
}

fn get_whitespace(whitespaces: &[Option<String>], ix: usize) -> Option<&str> {
    whitespaces.get(ix).and_then(|w| w.as_deref())
}

/// Interleaves serialized values with the original (or default) whitespace between them.
pub fn serialize_values_with_whitespace(values: &[String], whitespaces: &[Option<String>]) -> String {
    if values.is_empty() {
        return serialize_whitespace(whitespaces.first().and_then(|w| w.as_deref()), false).to_string();
    }

    let mut result = String::new();
    for (ix, value) in values.iter().enumerate() {
        result.push_str(serialize_whitespace(get_whitespace(whitespaces, ix), ix != 0));
        result.push_str(value);
    }

    if whitespaces.len() > values.len() {
        result.push_str(serialize_whitespace(get_whitespace(whitespaces, values.len()), false));
    }

    result
}

/// Serializes a line from already-serialized values, whitespace, and an optional comment.
pub fn serialize_line(values: &[String], whitespaces: Option<&[Option<String>]>, comment: Option<&str>) -> String {
    let mut line = match whitespaces {
        Some(whitespaces) if !whitespaces.is_empty() => {
            serialize_values_with_whitespace(values, whitespaces)
        }
        _ => values.join(" "),
    };

    if let Some(comment) = comment {
        line.push('#');
        line.push_str(comment);
    }

    line
}

/// Right-pads each column to the widest value in it and joins columns with a tab.
pub fn prettify_values(values: &[Vec<String>], comments: &[Option<String>]) -> Vec<String> {
    let num_cols = values.iter().map(Vec::len).max().unwrap_or(0);
    let col_sizes: Vec<usize> = (0..num_cols)
        .map(|col| values.iter().filter_map(|row| row.get(col)).map(String::len).max().unwrap_or(0))
        .collect();

    values
        .iter()
        .zip(comments)
        .map(|(row, comment)| {
            let mut line = row
                .iter()
                .enumerate()
                .map(|(ix, value)| format!("{value:<width$}", width = col_sizes[ix]))
                .collect::<Vec<_>>()
                .join("\t");

            if let Some(comment) = comment {
                line.push('\t');
                line.push('#');
                line.push_str(comment);
            }

            line.trim().to_string()
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize_value_escapes_special_cases() {
        assert_eq!(serialize_value(None), "-");
        assert_eq!(serialize_value(Some("")), "\"\"");
        assert_eq!(serialize_value(Some("a")), "a");
        assert_eq!(serialize_value(Some("-")), "\"-\"");
        assert_eq!(serialize_value(Some("a b")), "\"a b\"");
        assert_eq!(serialize_value(Some("a\nb")), "\"a\"/\"b\"");
        assert_eq!(serialize_value(Some("a\"b")), "\"a\"\"b\"");
    }

    #[test]
    fn serialize_line_falls_back_to_space_join_without_whitespace() {
        let values = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        assert_eq!(serialize_line(&values, None, None), "a b c");
        assert_eq!(serialize_line(&values, Some(&[]), Some("comment")), "a b c#comment");
    }

    #[test]
    fn serialize_line_preserves_given_whitespace() {
        let values = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let whitespaces = vec![None, Some(" \t".to_string()), Some(" ".to_string())];
        assert_eq!(serialize_line(&values, Some(&whitespaces), None), "a \tb c");
    }

    #[test]
    fn prettify_pads_columns_to_widest_value() {
        let values = vec![
            vec!["ab".to_string(), "b".to_string(), "c".to_string()],
            vec!["a".to_string(), "b".to_string(), "c".to_string()],
        ];
        let comments = vec![Some("comment".to_string()), Some("comment".to_string())];
        assert_eq!(
            prettify_values(&values, &comments),
            vec!["ab\tb\tc\t#comment".to_string(), "a \tb\tc\t#comment".to_string()]
        );
    }
}
