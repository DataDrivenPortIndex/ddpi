import os
import polars as pl

from tqdm import tqdm
from dotenv import load_dotenv

from src.port_detection import event_extraction
from src.pre_processing import ais_simplification
from src.errors.env import MissingEnvironmentVariable


load_dotenv(override=True)


def get_enviroment_variable(name: str) -> str:
    value = os.getenv(name)

    if value != "" and "XXXXX" not in value:
        print(f"\tEnviroment variable '{name}' set to:\t {value}")
        return value

    raise MissingEnvironmentVariable(f"Enviroment variable'{name}' does not exist")


def simplification(input_directory: str, output_directory: str):
    for day_file in tqdm(os.listdir(input_directory)):
        day_file_path = os.path.join(input_directory, day_file)
        ais_simplification.simplifiy(day_file_path, output_directory)


def extraction(input_directory: str, output_directory: str, year: str):
    dfs = []
    for day_file in tqdm(os.listdir(input_directory)):
        day_file_path = os.path.join(input_directory, day_file)

        df_lazy = event_extraction.process_day(day_file_path)

        dfs.append(df_lazy)

    output_file = os.path.join(output_directory, f"port_events_{year}.parquet")

    pl.concat(dfs).write_parquet(output_file)


def main():
    print("Setup")
    ais_input_directory = get_enviroment_variable("AIS_INPUT_DIRECTORY")
    ais_simplified_directory = get_enviroment_variable("AIS_SIMPLIFIED_DIRECTORY")
    ais_port_events_directory = get_enviroment_variable("AIS_PORT_EVENTS_DIRECTORY")

    print("Processing\n")

    print("Perform AIS-Simplification:")
    simplification(ais_input_directory, ais_simplified_directory)

    print("Perform Port-Event-Extraction:")
    extraction(ais_simplified_directory, ais_port_events_directory, "2020")

    print("Perform Port-Event-Validation:")

    print("Perform Port-Clustering:")


if __name__ == "__main__":
    main()
