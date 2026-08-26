use std::fs;
use std::path::PathBuf;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyType;

use crate::line::WsvLine;
use crate::parser::parse_lines;
use crate::serializer::{prettify_values, serialize_line, serialize_value};

enum SerializationMode {
    Preserve,
    Compact,
    Pretty,
}

impl SerializationMode {
    fn parse(mode: &str) -> PyResult<Self> {
        match mode {
            "preserve" => Ok(Self::Preserve),
            "compact" => Ok(Self::Compact),
            "pretty" => Ok(Self::Pretty),
            other => Err(PyValueError::new_err(format!("'{other}' is not a valid SerializationMode"))),
        }
    }
}

/// Manager for an ordered collection of WSV lines and their (de)serialization.
#[pyclass(module = "whitespacesv._whitespacesv", eq, skip_from_py_object)]
#[derive(Clone, Debug, PartialEq)]
pub struct WsvDocument {
    lines: Vec<WsvLine>,
}

#[pymethods]
impl WsvDocument {
    #[new]
    #[pyo3(signature = (lines=None))]
    fn new(lines: Option<Vec<WsvLine>>) -> Self {
        Self { lines: lines.unwrap_or_default() }
    }

    #[getter]
    fn lines(&self) -> Vec<WsvLine> {
        self.lines.clone()
    }

    #[setter]
    fn set_lines(&mut self, lines: Vec<WsvLine>) {
        self.lines = lines;
    }

    fn __repr__(&self) -> String {
        let parts: Vec<String> = self.lines.iter().map(WsvLine::__repr__).collect();
        format!("Document(lines=[{}])", parts.join(", "))
    }

    /// Parses `text` into a document, preserving original whitespace and comments.
    ///
    /// # Errors
    ///
    /// Returns `Err` (a `WsvParserError`) if `text` is not valid WSV.
    #[classmethod]
    fn parse(_cls: &Bound<'_, PyType>, text: &str) -> PyResult<Self> {
        Ok(Self { lines: parse_lines(text)? })
    }

    /// Serializes the lines to a list of strings using the given mode.
    ///
    /// # Errors
    ///
    /// Returns `Err` if `mode` is not one of `preserve`, `compact`, or `pretty`.
    #[pyo3(signature = (mode="preserve"))]
    fn serialize(&self, mode: &str) -> PyResult<Vec<String>> {
        let mode = SerializationMode::parse(mode)?;

        let values: Vec<Vec<String>> = self
            .lines
            .iter()
            .map(|line| line.values.iter().map(|v| serialize_value(v.as_deref())).collect())
            .collect();

        Ok(match mode {
            SerializationMode::Compact => values.iter().map(|row| row.join(" ")).collect(),
            SerializationMode::Pretty => {
                let comments: Vec<Option<String>> =
                    self.lines.iter().map(|line| line.comment_ref().map(str::to_string)).collect();
                prettify_values(&values, &comments)
            }
            SerializationMode::Preserve => values
                .iter()
                .zip(&self.lines)
                .map(|(row, line)| serialize_line(row, line.whitespaces_ref(), line.comment_ref()))
                .collect(),
        })
    }

    /// Loads a document from `file_path`, stripping a leading UTF-8 BOM if present.
    ///
    /// # Errors
    ///
    /// Returns `Err` if the file is empty, does not end with a newline, or is not valid WSV.
    #[classmethod]
    fn load(_cls: &Bound<'_, PyType>, file_path: PathBuf) -> PyResult<Self> {
        let text = load_txt(&file_path)?;
        if text.is_empty() || !text.ends_with('\n') {
            return Err(PyValueError::new_err("Empty file or no new line at the end"));
        }
        Ok(Self { lines: parse_lines(&text)? })
    }

    /// Serializes the document to a single newline-terminated string.
    ///
    /// # Errors
    ///
    /// Returns `Err` if `mode` is not one of `preserve`, `compact`, or `pretty`.
    #[pyo3(signature = (mode="preserve"))]
    fn to_string(&self, mode: &str) -> PyResult<String> {
        let mut text = self.serialize(mode)?.join("\n");
        text.push('\n');
        Ok(text)
    }

    /// Saves the document to `file_path` with a trailing newline.
    ///
    /// # Errors
    ///
    /// Returns `Err` if the document has no lines, `mode` is invalid, or the write fails.
    #[pyo3(signature = (file_path, mode="preserve"))]
    fn save(&self, file_path: PathBuf, mode: &str) -> PyResult<()> {
        if self.lines.is_empty() {
            return Err(PyValueError::new_err("Can't save empty document"));
        }
        let content = self.to_string(mode)?;
        fs::write(&file_path, content)?;
        Ok(())
    }
}

fn load_txt(file_path: &PathBuf) -> PyResult<String> {
    let text = fs::read_to_string(file_path)?;
    Ok(text.strip_prefix('\u{feff}').map(str::to_string).unwrap_or(text))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn serialize_rejects_unknown_mode() {
        let doc = WsvDocument::new(None);
        assert!(doc.serialize("invalid").is_err());
    }

    #[test]
    fn to_string_appends_trailing_newline() {
        let doc = WsvDocument { lines: parse_lines("a b c\n").unwrap() };
        assert_eq!(doc.to_string("compact").unwrap(), "a b c\n");
    }

    #[test]
    fn save_rejects_empty_document() {
        let doc = WsvDocument::new(None);
        assert!(doc.save(PathBuf::from("/tmp/does-not-matter.wsv"), "preserve").is_err());
    }
}
