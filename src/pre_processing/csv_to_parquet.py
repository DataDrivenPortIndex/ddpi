import os
import sys
import tarfile
import subprocess
import polars as pl
import h3.api.basic_int as h3

from typing import List, Tuple


H3_RESOLUTION = 11
NUMBER_OF_WORKERS = 8
H3_ROUGH_RESOLUTION = 8
ZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2020"
UNZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2020"

COLUMNS = ["MMSI", "TIMESTAMPUTC", "LONGITUDE", "LATITUDE", "SHIPANDCARGOTYPECODE",
           "SIZEA", "SIZEB", "SIZEC", "SIZED", "NAVSTATUSCODE", "COG", "SOG", "TRUEHEADING", 
           "MAXDRAUGHT", "ROT", "MESSAGEID", "DESTINATION"]
COLUMN_TYPES_POLARS = {"MMSI": pl.UInt32(), "IMO": pl.UInt32, "LONGITUDE": pl.Float32(), "LATITUDE": pl.Float32(),
                       "SHIPANDCARGOTYPECODE": pl.UInt16(), "SIZEA": pl.UInt16(), "SIZEB": pl.UInt16(), "SIZEC": pl.UInt16(), 
                       "SIZED": pl.UInt16(), "NAVSTATUSCODE": pl.UInt8(), "COG": pl.Float32(), "SOG": pl.Float32(), "TRUEHEADING": pl.UInt16(),
                       "MAXDRAUGHT": pl.Float32(), "ROT": pl.Int8(), "MESSAGEID": pl.Utf8(), "DESTINATION": pl.Utf8(), "MESSAGEID": pl.UInt8()}


def unpack_tar_file(file: str, day_directory: str) -> List[str]:
    try:
        os.mkdir(day_directory)
    except FileExistsError:
        pass

    if ".tar" in file:
        with tarfile.open(file, "r:gz") as t:
            for member in t.getmembers():
                t.extract(member, day_directory)

        return [os.path.join(day_directory, i) for i in os.listdir(day_directory)]


def unpack_tar_file_subprocess(file: str, day_directory: str) -> List[str]:
    try:
        os.mkdir(day_directory)
    except FileExistsError:
        pass

    subprocess.run(["tar", "-xzf", file, "-C", day_directory], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return [os.path.join(day_directory, i) for i in os.listdir(day_directory)]


def get_date_from_file_name(file_name: str) -> str:
    return os.path.basename(file_name).split("ais-")[1].split(".")[0]


def compute_h3_cell(values: Tuple[float]) -> int:
    try:
        return h3.geo_to_h3(values[0], values[1], values[2])
    except TypeError:
        pass


def directory_exists(directory_path: str) -> bool:
    return os.path.isdir(directory_path)


def csv_to_parquet_polars(csv_file: str):
    try:
        df = pl.read_csv(csv_file, columns=COLUMNS, separator="|", dtypes=COLUMN_TYPES_POLARS, ignore_errors=True)
        df = df.with_columns(
            pl.col("TIMESTAMPUTC").str.strptime(pl.Datetime("ms"), fmt='%+'),
        )

        df = df.with_columns(
            pl.struct(pl.col(["LONGITUDE", "LATITUDE"])).apply(lambda x: compute_h3_cell((x["LATITUDE"], x["LONGITUDE"], H3_RESOLUTION))).alias('h3_cell'),
            pl.struct(pl.col(["LONGITUDE", "LATITUDE"])).apply(lambda x: compute_h3_cell((x["LATITUDE"], x["LONGITUDE"], H3_ROUGH_RESOLUTION))).alias('h3_cell_rough'),
        )

        df.write_parquet(csv_file.replace(".csv", ".parquet"))

    except pl.ComputeError as e:
        print(f"csv file: {csv_file} could not be processed: {e}")
    finally:
        os.remove(csv_file)


def process_day_tar_gz(tar_file: str):
    date = get_date_from_file_name(tar_file)
    date_directory = os.path.join(UNZIPPED_FILES_DIRECTORY, date)

    if os.path.exists(date_directory):
        return
    
    csv_files = unpack_tar_file_subprocess(tar_file, date_directory)
    for csv_file in csv_files:
        csv_to_parquet_polars(csv_file)


if __name__ == "__main__":
    process_day_tar_gz(os.path.join(ZIPPED_FILES_DIRECTORY, sys.argv[1]))
