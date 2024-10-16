import os
import h3
import sys
import tqdm
import polars as pl

from typing import Tuple


YEARS = ["2020"]
H3_RESOLUTION = 11
NUMBER_OF_WORKERS = 10
H3_ROUGH_RESOLUTION = 6
INPUT_DIRECTOR = "/media/pbusenius/BigData/AIS"
COLUMNS = ["MMSI", "TIMESTAMPUTC", "LONGITUDE", "LATITUDE", "SHIPANDCARGOTYPECODE",
           "SIZEA", "SIZEB", "SIZEC", "SIZED", "NAVSTATUSCODE", "COG", "SOG", "TRUEHEADING", 
           "MAXDRAUGHT", "ROT", "MESSAGEID", "DESTINATION", "MESSAGESOURCE"]


def compute_h3_cell(values: Tuple[float]) -> int:
    try:
        return h3.geo_to_h3(values[0], values[1], values[2])
    except TypeError:
        pass


def cast_types(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        pl.col("MMSI").cast(pl.UInt32(), strict=False),
        pl.col("MESSAGEID").cast(pl.UInt8(), strict=False),
        pl.col("LONGITUDE").cast(pl.Float32(), strict=False),
        pl.col("LATITUDE").cast(pl.Float32(), strict=False),
        pl.col("SHIPANDCARGOTYPECODE").cast(pl.UInt16(), strict=False),
        pl.col("SIZEA").cast(pl.UInt16(), strict=False),
        pl.col("SIZEB").cast(pl.UInt16(), strict=False),
        pl.col("SIZEC").cast(pl.UInt16(), strict=False),
        pl.col("SIZED").cast(pl.UInt16(), strict=False),
        pl.col("NAVSTATUSCODE").cast(pl.UInt8(), strict=False),
        pl.col("COG").cast(pl.Float32(), strict=False),
        pl.col("SOG").cast(pl.Float32(), strict=False),
        pl.col("TRUEHEADING").cast(pl.UInt16(), strict=False),
        pl.col("MAXDRAUGHT").cast(pl.Float32(), strict=False),
        pl.col("ROT").cast(pl.Int8(), strict=False),
        pl.col("DESTINATION").cast(pl.Utf8(), strict=True),
        pl.col("MESSAGESOURCE").map_dict({"AIS-T": True, "AIS-S": False}).alias("terrestrial_message"),
    )

    df = df.drop(["MESSAGESOURCE"])

    return df


def process_hour_file(hour_file: str):
    if "type_cast" in hour_file:
        return
    
    if os.path.exists(hour_file.replace(".parquet", "_type_cast.parquet")):
        return
    
    try:
        df = pl.read_parquet(hour_file, columns=COLUMNS)
    except:
        return
    
    try:
        df = cast_types(df)
    except pl.ComputeError:
        return

    df.write_parquet(hour_file.replace(".parquet", "_type_cast.parquet"))


def main(day_path):
    hour_files = [os.path.join(day_path, hour_file) for hour_file in os.listdir(day_path)]
    for hour_file in tqdm.tqdm(hour_files):
        process_hour_file(hour_file)


if __name__ == "__main__":
    args = sys.argv

    main(args[1])
