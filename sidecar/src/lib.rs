use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

/// A simple function to try all this out
#[pyfunction]
fn hello_python() -> PyResult<String> {
    Ok("Hello Python!".to_owned())
}

/// A Python module implemented in Rust.
#[pymodule]
fn sidecar(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(hello_python))?;

    Ok(())
}
