use h3o::{LatLng, Resolution};
use polars::prelude::*;
use polars_core::utils::accumulate_dataframes_vertical;
use rayon::prelude::*;

// TODO: add generic implementation of lat_lon_to_cell (handle f32 and f64)

/// Create `n` splits so that we can slice a polars data structure
/// and process the chunks in parallel
fn split_offsets(len: usize, n: usize) -> Vec<(usize, usize)> {
    if n == 1 {
        vec![(0, len)]
    } else {
        let chunk_size = len / n;

        (0..n)
            .map(|partition| {
                let offset = partition * chunk_size;
                let len = if partition == (n - 1) {
                    len - offset
                } else {
                    chunk_size
                };
                (partition * chunk_size, len)
            })
            .collect()
    }
}

// compute h3 index for given lat lon values
fn lat_lon_to_cell(lat: f64, lon: f64, resolution: u8) -> u64 {
    let res = Resolution::try_from(resolution).expect("resolution");
    let coord = LatLng::new(lat, lon).expect("valid coord");

    let cell = coord.to_cell(res);

    u64::from(cell)
}

fn apply_h3_cell(lat: &Series, lon: &Series, resolution: u8) -> UInt64Chunked {
    match (lat.dtype(), lon.dtype()) {
        (DataType::Float64, DataType::Float64) => {
            let a = lat.f64().unwrap();
            let b = lon.f64().unwrap();

            a.into_iter()
                .zip(b.into_iter())
                .map(|(opt_a, opt_b)| match (opt_a, opt_b) {
                    (Some(a), Some(b)) => Some(lat_lon_to_cell(a, b, resolution)),
                    _ => None,
                })
                .collect()
        }
        _ => panic!("unpexptected dtypes"),
    }
}

pub(super) fn parallel_lat_lon_to_cell(
    df: DataFrame,
    col_a: &str,
    col_b: &str,
    resolution: u8,
    name: &str,
) -> PolarsResult<DataFrame> {
    let offsets = split_offsets(df.height(), rayon::current_num_threads());

    let dfs = offsets
        .par_iter()
        .map(|(offset, len)| {
            let mut sub_df = df.slice(*offset as i64, *len);
            let lat_col = sub_df.column(col_a).unwrap();
            let lon_col = sub_df.column(col_b).unwrap();

            // compute h3_cells
            let h3_cell_series = Series::new(name, apply_h3_cell(lat_col, lon_col, resolution));

            // add h3_cell column
            sub_df.with_column(h3_cell_series).unwrap();

            Ok(sub_df)
        })
        .collect::<PolarsResult<Vec<_>>>()?;

    accumulate_dataframes_vertical(dfs)
}
