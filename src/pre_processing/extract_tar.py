import os
import tarfile

from typing import Generator
from functools import partial
from multiprocessing import Pool
from pyarrow import csv, parquet, lib


NUMBER_OF_WORKERS = 5
ZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2021"
UNZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2021"


def unpack_tar_file(file: str, day_directory: str) -> Generator[str, None, None]:
    if ".tar" in file:
        with tarfile.open(file) as t:
            try:
                for f in t.getmembers():
                    t.extract(f, day_directory)
                    yield os.path.join(day_directory, f.name)
            except:
                print(file)


def get_date_from_file_name(file_name: str) -> str:
    return file_name.split("ais-")[1].split(".")[0]


def directory_exists(directory_path: str) -> bool:
    return os.path.isdir(directory_path)


def csv_to_parquet(csv_file: str) -> None:
    try:
        parse_options = csv.ParseOptions(delimiter="|")
        table = csv.read_csv(csv_file, parse_options=parse_options)
        parquet.write_table(table, csv_file.replace(".csv", ".parquet"))
    except lib.ArrowInvalid as e:
        print(e)


def process_day_tar_gz(tar_file: str):
    date = get_date_from_file_name(tar_file)
    date_directory = os.path.join(UNZIPPED_FILES_DIRECTORY, date)

    if not directory_exists(date_directory):
        for csv_file in unpack_tar_file(tar_file, date_directory):
            csv_to_parquet(csv_file)
            os.remove(csv_file)

        os.remove(tar_file)


if __name__ == "__main__":
    day_files = [i for i in os.listdir(ZIPPED_FILES_DIRECTORY) if ".tar" in i]
    day_files = [os.path.join(ZIPPED_FILES_DIRECTORY, i) for i in day_files]

    processing_pool = Pool(processes=NUMBER_OF_WORKERS)
    processing_pool.map(partial(process_day_tar_gz), day_files)
