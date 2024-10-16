import os
import glob
import polars as pl
import h3.api.basic_int as h3

from typing import Tuple


DAY_FILTER = "2020-0[6, 7, 8, 9, 10]*.parquet"
OUTPUT_FILE = "activities_class_b.csv"
INPUT_PATH = "/media/pbusenius/BigData/AIS/simplified"


def compute_h3_cell(values: Tuple[float]) -> int:
    return h3.h3_to_parent(values[0], values[1])


def main():
    queries = []
    day_files = glob.glob(os.path.join(INPUT_PATH, DAY_FILTER))

    for day_file in day_files:
        queries.append(
            pl.scan_parquet(
                day_file,
            ).select(
                ["MMSI", "h3_cell_rough", "LATITUDE", "LONGITUDE"]
            ).filter(
                (pl.col("h3_cell_rough") != 0) & (pl.col("is_class_a") == False)
            ).groupby("h3_cell_rough").agg(
                pl.col("MMSI").n_unique().alias("MMSI_COUNT"),
            )
        )

    queries = pl.collect_all(queries)
    df = pl.concat(queries)

    df = df.with_columns(
        pl.col(["h3_cell_rough",]).apply(lambda x: compute_h3_cell((x, 5))).alias('h3_cell_rough'),
    )

    df = df.groupby("h3_cell_rough").agg(
        pl.col("MMSI_COUNT").sum()
    )

    df = df.with_columns(
        pl.col("h3_cell_rough").apply(lambda x: f"{x:0x}").alias('h3_cell_rough'),
    )

    df.write_csv(OUTPUT_FILE)


if __name__ == "__main__":
    main()
