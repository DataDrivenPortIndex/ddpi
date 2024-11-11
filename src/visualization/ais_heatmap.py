import os
import glob
import polars as pl
import h3ronpy.polars

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
    ).collect(streaming=True)

    df = (
        df.with_columns(pl.col("h3_cell_rough").h3.change_resolution(5).alias("h3"))
        .group_by("h3")
        .agg(pl.col("MMSI_COUNT").sum())
        .with_columns(
            pl.col("h3")
            .map_elements(lambda x: f"{x:0x}", return_dtype=pl.String)
            .alias("h3")
        )
    )

    df.write_csv(OUTPUT_FILE)


if __name__ == "__main__":
    main()
