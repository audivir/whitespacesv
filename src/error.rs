use pyo3::exceptions::PyException;
use pyo3::prelude::*;

/// Container for a WSV parse failure at a specific line and character position.
#[pyclass(extends = PyException, module = "whitespacesv._whitespacesv")]
pub struct WsvParserError {
    #[pyo3(get)]
    ix: usize,
    #[pyo3(get)]
    line_ix: usize,
    #[pyo3(get)]
    line_position: usize,
    formatted: String,
}

#[pymethods]
impl WsvParserError {
    #[new]
    fn new(ix: usize, line_ix: usize, line_position: usize, message: String) -> Self {
        let formatted = format!("{message} ({}, {})", line_ix + 1, line_position + 1);
        Self { ix, line_ix, line_position, formatted }
    }

    fn __str__(&self) -> &str {
        &self.formatted
    }
}

/// Builds a ready-to-raise `WsvParserError` for the given position and message.
pub fn parser_error(ix: usize, line_ix: usize, line_position: usize, message: &str) -> PyErr {
    PyErr::new::<WsvParserError, _>((ix, line_ix, line_position, message.to_string()))
}
