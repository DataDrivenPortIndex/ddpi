import os
import h3ronpy
import polars as pl

from typing import Dict
from h3ronpy.vector import coordinates_to_cells

H3_RESOLUTION = 10
H3_ROUGH_RESOLUTION = 6
OUTPUT_DIRECTORY = "/media/pbusenius/BigData/AIS/simplified"
AIS_COLUMNS = [
    "MMSI",
    "MESSAGEID",
    "TIMESTAMPUTC",
    "DESTINATION",
    "SHIPANDCARGOTYPECODE",
    "SOG",
    "COG",
    "LATITUDE",
    "LONGITUDE",
    "TRUEHEADING",
    "ROT",
    "SIZEA",
    "SIZEB",
    "SIZEC",
    "SIZED",
    "MAXDRAUGHT",
    "NAVSTATUSCODE",
]
CLASS_A_MESSAGES = {
    "class_a": True,
    "static": 5,
    "position": [1, 2, 3],
    "position_columns": [
        "MMSI",
        "TIMESTAMPUTC",
        "SOG",
        "COG",
        "TRUEHEADING",
        "ROT",
        "NAVSTATUSCODE",
        "LATITUDE",
        "LONGITUDE",
    ],
    "static_columns": [
        "MMSI",
        "TIMESTAMPUTC",
        "DESTINATION",
        "SHIPANDCARGOTYPECODE",
        "SIZEA",
        "SIZEB",
        "SIZEC",
        "SIZED",
        "MAXDRAUGHT",
    ],
}
CLASS_B_MESSAGES = {
    "class_a": False,
    "static": 19,
    "position": [18, 19],
    "position_columns": [
        "MMSI",
        "TIMESTAMPUTC",
        "SOG",
        "COG",
        "TRUEHEADING",
        "ROT",
        "NAVSTATUSCODE",
        "LATITUDE",
        "LONGITUDE",
    ],
    "static_columns": [
        "MMSI",
        "TIMESTAMPUTC",
        "DESTINATION",
        "SHIPANDCARGOTYPECODE",
        "SIZEA",
        "SIZEB",
        "SIZEC",
        "SIZED",
        "MAXDRAUGHT",
    ],
}


def aggregate_ais(df: pl.LazyFrame) -> pl.LazyFrame:
    return df.group_by_dynamic("TIMESTAMPUTC", group_by="MMSI", every="1m").agg(
        pl.col("SOG").mean(),
        pl.col("COG").mean(),
        pl.col("ROT").mean(),
        pl.col("TRUEHEADING").mean(),
        pl.col("SIZEA").first(),
        pl.col("SIZEB").first(),
        pl.col("SIZEC").first(),
        pl.col("SIZED").first(),
        pl.col("SHIPANDCARGOTYPECODE").first(),
        pl.col("NAVSTATUSCODE").last(),
        pl.col("DESTINATION").last(),
        pl.col("MAXDRAUGHT").last(),
        pl.col("LATITUDE").first(),
        pl.col("LONGITUDE").first(),
        pl.col("is_class_a").first(),
    )


def class_messages(df: pl.LazyFrame, mode_config: Dict) -> pl.LazyFrame:
    return (
        df.filter(pl.col("MESSAGEID").is_in(mode_config["position"]))
        .select(mode_config["position_columns"])
        .join_asof(
            other=df.filter(pl.col("MESSAGEID") == mode_config["static"]).select(
                mode_config["static_columns"]
            ),
            on="TIMESTAMPUTC",
            by="MMSI",
            tolerance="2h",
            strategy="forward",
        )
        .drop_nulls(["SIZEA", "SHIPANDCARGOTYPECODE"])
        .with_columns(pl.lit(mode_config["class_a"]).alias("is_class_a"))
    )


def simplifiy(day: str, output_directory: str):
    out_path = f"{os.path.join(output_directory, os.path.basename(day))}.parquet"
    if not os.path.isfile(out_path):
        lf = pl.scan_parquet(f"{day}/*type_cast.parquet").select(AIS_COLUMNS)

        # filter and combine class a and class b messages
        class_a_lf = class_messages(lf, CLASS_A_MESSAGES)
        class_b_lf = class_messages(lf, CLASS_B_MESSAGES)

        lf = pl.concat([class_a_lf, class_b_lf]).sort("TIMESTAMPUTC")

        # TODO: remove type conversion and handle this in rust
        df = (
            aggregate_ais(lf)
            .filter(
                (~pl.col("LATITUDE").is_infinite())
                & (~pl.col("LONGITUDE").is_infinite())
            )
            .with_columns(
                pl.col("LONGITUDE").cast(pl.Float64),
                pl.col("LATITUDE").cast(pl.Float64),
            )
            .collect()
        )

        # add h3 cells, the rough cell is derived from the fine cell instead of the coordinates
        h3_cell = pl.Series(
            coordinates_to_cells(df["LATITUDE"], df["LONGITUDE"], H3_RESOLUTION)
        ).alias("h3_cell")
        h3_cell_rough = pl.Series(
            h3ronpy.change_resolution(h3_cell, H3_ROUGH_RESOLUTION)
        ).alias("h3_cell_rough")

        df.with_columns(h3_cell, h3_cell_rough).write_parquet(out_path)
