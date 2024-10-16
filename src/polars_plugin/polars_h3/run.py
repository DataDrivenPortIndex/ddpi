import polars as pl
from polars_h3 import parallel_lat_lon_to_cell


df = pl.read_parquet("ais-2022-11-04-23.parquet")
print(df)

df = parallel_lat_lon_to_cell(df, "LATITUDE", "LONGITUDE", 11, "h3_cell")
print(df)
