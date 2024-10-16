mod parallel_h3_mod;

use polars::prelude::*;
use pyo3::prelude::*;
use pyo3_polars::error::PyPolarsErr;
use pyo3_polars::PyDataFrame;

#[pyfunction]
fn parallel_lat_lon_to_cell(
    pydf: PyDataFrame,
    col_a: &str,
    col_b: &str,
    resolution: u8,
    name: &str,
) -> PyResult<PyDataFrame> {
    let df: DataFrame = pydf.into();
    let df = parallel_h3_mod::parallel_lat_lon_to_cell(df, col_a, col_b, resolution, name)
        .map_err(PyPolarsErr::from)?;

    Ok(PyDataFrame(df))
}

/// A Python module implemented in Rust.
#[pymodule]
fn polars_h3(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parallel_lat_lon_to_cell, m)?)?;
    Ok(())
}
