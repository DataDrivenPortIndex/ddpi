import os
import polars as pl

from typing import Dict
from pyo3_h3 import parallel_lat_lon_to_cell

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


def aggregate_ais(df: pl.DataFrame) -> pl.DataFrame:
    return df.group_by_dynamic("TIMESTAMPUTC", by="MMSI", every="1m").agg(
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


def class_messages(df: pl.DataFrame, mode_config: Dict) -> pl.DataFrame:
    return (
        df.filter(pl.col("MESSAGEID").is_in(mode_config["position"]))[
            mode_config["position_columns"]
        ]
        .join_asof(
            other=df.filter(pl.col("MESSAGEID") == mode_config["static"])[
                mode_config["static_columns"]
            ],
            on="TIMESTAMPUTC",
            by="MMSI",
            tolerance="2h",
            strategy="forward",
        )
        .drop_nulls(["SIZEA", "SHIPANDCARGOTYPECODE"])
        .with_columns(pl.lit(mode_config["class_a"]).alias("is_class_a"))
    )


def simplifiy(day: str, output_directory: str):
    if not os.path.exists:
        os.mkdir(output_directory)
        
    out_path = f"{os.path.join(output_directory, os.path.basename(day))}.parquet"
    if not os.path.isfile(out_path):
        df = pl.read_parquet(f"{day}/*type_cast.parquet", columns=AIS_COLUMNS)

        # filter and combine class a and class b messages
        class_a_df = class_messages(df, CLASS_A_MESSAGES)
        class_b_df = class_messages(df, CLASS_B_MESSAGES)

        df = pl.concat([class_a_df, class_b_df]).sort("TIMESTAMPUTC")

        df = aggregate_ais(df)

        df = df.filter(
            (~pl.col("LATITUDE").is_infinite()) & (~pl.col("LONGITUDE").is_infinite())
        )

        # TODO: remove type conversion and handle this in rust
        df = df.with_columns(
            [
                pl.col("LONGITUDE").cast(pl.Float64),
                pl.col("LATITUDE").cast(pl.Float64),
            ]
        )

        # add h3 cells
        df_h3_cell = parallel_lat_lon_to_cell(
            df.select(["LONGITUDE", "LATITUDE"]),
            "LATITUDE",
            "LONGITUDE",
            H3_RESOLUTION,
            "h3_cell",
        )
        df_h3_cell = df_h3_cell.drop(["LONGITUDE", "LATITUDE"])

        df_h3_cell_rough = parallel_lat_lon_to_cell(
            df.select(["LONGITUDE", "LATITUDE"]),
            "LATITUDE",
            "LONGITUDE",
            H3_ROUGH_RESOLUTION,
            "h3_cell_rough",
        )
        df_h3_cell_rough = df_h3_cell_rough.drop(["LONGITUDE", "LATITUDE"])

        df = pl.concat([df, df_h3_cell, df_h3_cell_rough], how="horizontal")

        df.write_parquet(out_path)
