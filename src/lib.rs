mod document;
mod error;
mod iterator;
mod line;
mod parser;
mod serializer;
mod utils;

use pyo3::prelude::*;

use document::WsvDocument;
use error::WsvParserError;
use line::WsvLine;

#[pymodule]
fn _whitespacesv(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<WsvLine>()?;
    m.add_class::<WsvDocument>()?;
    m.add_class::<WsvParserError>()?;
    Ok(())
}
