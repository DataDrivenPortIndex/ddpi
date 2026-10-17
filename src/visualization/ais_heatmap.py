import os
import glob
import h3ronpy
import polars as pl

from dotenv import load_dotenv


load_dotenv(override=True)


DAY_FILTER = "2020-0[6, 7, 8, 9, 10]*.parquet"
OUTPUT_FILE = "ais_activities.csv"


def main():
    day_files = glob.glob(
        os.path.join(os.getenv("AIS_SIMPLIFIED_DIRECTORY"), DAY_FILTER)
    )

    df = (
        pl.scan_parquet(day_files, glob=True)
        .select(["MMSI", "h3_cell_rough"])
        .group_by("h3_cell_rough")
        .agg(
            pl.col("MMSI").n_unique().alias("MMSI_COUNT"),
        )
    ).collect()

    # h3ronpy's polars expression namespace is not compatible with polars 2.0
    df = (
        df.with_columns(
            pl.Series(h3ronpy.change_resolution(df["h3_cell_rough"], 5)).alias("h3")
        )
        .group_by("h3")
        .agg(pl.col("MMSI_COUNT").sum())
    )
    df = df.with_columns(pl.Series(h3ronpy.cells_to_string(df["h3"])).alias("h3"))

    df.write_csv(OUTPUT_FILE)


if __name__ == "__main__":
    main()
