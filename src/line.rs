use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::utils::is_string_whitespace;

/// Container for the values, whitespaces, and trailing comment of a single WSV line.
#[pyclass(module = "whitespacesv._whitespacesv", eq, from_py_object)]
#[derive(Clone, Debug, PartialEq)]
pub struct WsvLine {
    #[pyo3(get, set)]
    pub values: Vec<Option<String>>,
    whitespaces: Option<Vec<Option<String>>>,
    comment: Option<String>,
}

impl WsvLine {
    pub fn new_unchecked(
        values: Vec<Option<String>>,
        whitespaces: Option<Vec<Option<String>>>,
        comment: Option<String>,
    ) -> Self {
        Self { values, whitespaces, comment }
    }

    pub fn whitespaces_ref(&self) -> Option<&[Option<String>]> {
        self.whitespaces.as_deref()
    }

    pub fn comment_ref(&self) -> Option<&str> {
        self.comment.as_deref()
    }
}

#[pymethods]
impl WsvLine {
    /// Creates a line from optional values, whitespaces, and a trailing comment.
    ///
    /// # Errors
    ///
    /// Returns `Err` if `whitespaces` contains a non-whitespace character or `comment` contains
    /// a line feed.
    #[new]
    #[pyo3(signature = (values=None, whitespaces=None, comment=None))]
    fn py_new(
        values: Option<Vec<Option<String>>>,
        whitespaces: Option<Vec<Option<String>>>,
        comment: Option<String>,
    ) -> PyResult<Self> {
        validate_whitespaces(whitespaces.as_deref())?;
        validate_comment(comment.as_deref())?;
        Ok(Self { values: values.unwrap_or_default(), whitespaces, comment })
    }

    /// Raw whitespace strings between values, if the line retains them.
    #[getter]
    fn whitespaces(&self) -> Option<Vec<Option<String>>> {
        self.whitespaces.clone()
    }

    /// Trailing comment text, if the line has one.
    #[getter]
    fn comment(&self) -> Option<String> {
        self.comment.clone()
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Line({}, {}, {})",
            repr_values(&self.values),
            repr_whitespaces(&self.whitespaces),
            repr_comment(&self.comment)
        )
    }

    /// Checks that every entry in `whitespaces` contains only whitespace characters.
    ///
    /// # Errors
    ///
    /// Returns `Err` if an entry contains a non-whitespace character.
    #[staticmethod]
    fn validate_whitespaces(whitespaces: Option<Vec<Option<String>>>) -> PyResult<()> {
        validate_whitespaces(whitespaces.as_deref())
    }

    /// Checks that `comment` contains no line feed.
    ///
    /// # Errors
    ///
    /// Returns `Err` if `comment` contains a line feed.
    #[staticmethod]
    fn validate_comment(comment: Option<String>) -> PyResult<()> {
        validate_comment(comment.as_deref())
    }
}

fn validate_whitespaces(whitespaces: Option<&[Option<String>]>) -> PyResult<()> {
    let Some(whitespaces) = whitespaces else { return Ok(()) };
    for whitespace in whitespaces.iter().flatten() {
        if whitespace.is_empty() {
            continue;
        }
        if !is_string_whitespace(whitespace) {
            return Err(PyValueError::new_err(
                "Whitespace value contains non whitespace character/line feed",
            ));
        }
    }
    Ok(())
}

fn validate_comment(comment: Option<&str>) -> PyResult<()> {
    let Some(comment) = comment else { return Ok(()) };
    if comment.is_empty() {
        return Ok(());
    }
    if comment.contains('\n') {
        return Err(PyValueError::new_err("Line feed in comment is not allowed"));
    }
    Ok(())
}

fn repr_values(values: &[Option<String>]) -> String {
    let parts: Vec<String> = values.iter().map(repr_opt_string).collect();
    format!("[{}]", parts.join(", "))
}

fn repr_whitespaces(whitespaces: &Option<Vec<Option<String>>>) -> String {
    match whitespaces {
        None => "None".to_string(),
        Some(ws) => {
            let parts: Vec<String> = ws.iter().map(repr_opt_string).collect();
            format!("[{}]", parts.join(", "))
        }
    }
}

fn repr_comment(comment: &Option<String>) -> String {
    match comment {
        None => "None".to_string(),
        Some(c) => c.clone(),
    }
}

fn repr_opt_string(value: &Option<String>) -> String {
    match value {
        None => "None".to_string(),
        Some(v) => format!("'{}'", v.replace('\\', "\\\\").replace('\'', "\\'")),
    }
}
