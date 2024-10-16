import os
import sys
import tarfile
import pyarrow as pa

from pyarrow import csv
from typing import List


H3_RESOLUTION = 11
NUMBER_OF_WORKERS = 8
H3_ROUGH_RESOLUTION = 8
ZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2020"
UNZIPPED_FILES_DIRECTORY = "/media/pbusenius/BigData/AIS/2020"
COLUMNS = ["MMSI", "IMO", "TIMESTAMPUTC", "LONGITUDE", "LATITUDE", "SHIPANDCARGOTYPECODE",
           "SIZEA", "SIZEB", "SIZEC", "SIZED", "NAVSTATUSCODE", "COG", "SOG", "TRUEHEADING", 
           "MAXDRAUGHT", "ROT", "MESSAGEID", "DESTINATION"]
COLUMN_TYPES = {"MMSI": pa.uint32(), "IMO": pa.uint32(), "LONGITUDE": pa.float32(), "LATITUDE": pa.float32(),
                "SHIPANDCARGOTYPECODE": pa.uint16(), "SIZEA": pa.uint16(), "SIZEB": pa.uint16(), "SIZEC": pa.uint16(), "SIZED": pa.uint16(),
                "NAVSTATUSCODE": pa.uint8(), "COG": pa.float32(), "SOG": pa.float32(), "TRUEHEADING": pa.uint16(),
                "MAXDRAUGHT": pa.float32(), "ROT": pa.uint8(), "MESSAGEID": pa.uint8(), "DESTINATION": pa.string()}


def get_date_from_file_name(file_name: str) -> str:
    return os.path.basename(file_name).split("ais-")[1].split(".")[0]


def unpack_tar_file(file: str, day_directory: str) -> List[str]:
    try:
        os.mkdir(day_directory)
    except FileExistsError:
        pass

    if ".tar" in file:
        with tarfile.open(file, "r") as t:
            for member in t.getmembers():
                t.extract(member, day_directory)

        return [os.path.join(day_directory, i) for i in os.listdir(day_directory)]


def process_csv_file(csv_files: str):
    csv_options = csv.ConvertOptions(
        include_columns=COLUMNS,
        column_types=COLUMN_TYPES
    )
def main(tar_file: str):
    date = get_date_from_file_name(tar_file)
    date_directory = os.path.join(UNZIPPED_FILES_DIRECTORY, date)
    csv_files = unpack_tar_file(tar_file, date_directory)
    for csv_file in csv_files:
        pass


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        main(os.path.join(ZIPPED_FILES_DIRECTORY, sys.argv[1]))
    # day_files = os.listdir(ZIPPED_FILES_DIRECTORY)
    # day_files = [os.path.join(ZIPPED_FILES_DIRECTORY, i) for i in day_files if ".tar" in i]
   
    # for day_file in day_files:
    #     print(day_file)
    #     process_day_tar_gz(day_file)
    #     break