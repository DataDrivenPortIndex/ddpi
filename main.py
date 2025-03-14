import os
import polars as pl

from tqdm import tqdm
from dotenv import load_dotenv

from src.post_processing import geo_information_enrichment
from src.post_processing import overlap
from src.port_event_processing import export
from src.port_event_processing import cluster_generation
from src.port_event_processing import event_extraction
from src.port_event_processing import event_validation
from src.data_preparation import ais_simplification
from src.errors.env import MissingEnvironmentVariable


load_dotenv(override=True)


def get_enviroment_variable(name: str) -> str:
    value = os.getenv(name)

    if value is not None and value != "" and "XXXXX" not in value:
        return value

    raise MissingEnvironmentVariable(f"Enviroment variable'{name}' does not exist")


def simplification(input_directory: str, output_directory: str):
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for day_file in tqdm(os.listdir(input_directory)):
        day_file_path = os.path.join(input_directory, day_file)
        ais_simplification.simplifiy(day_file_path, output_directory)


def extraction(input_directory: str, output_directory: str, years: str):
    dfs = []

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for year in years:
        output_file = os.path.join(output_directory, f"port_events_{year}.parquet")
        for day_file in tqdm(os.listdir(input_directory)):
            if year in day_file:
                if os.path.isfile(output_file):
                    continue
                try:
                    day_file_path = os.path.join(input_directory, day_file)

                    df_lazy = event_extraction.process_day(day_file_path)

                    dfs.append(df_lazy)
                except pl.exceptions.ComputeError:
                    print(day_file)
                    pass

        if not os.path.isfile(output_file):
            pl.concat(dfs).write_parquet(output_file)


def validation(input_directory: str, output_directory: str):
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for port_event_file in tqdm(os.listdir(input_directory)):
        event_file_path = os.path.join(input_directory, port_event_file)
        validated_event_file_path = os.path.join(
            output_directory, f"validated_{port_event_file.split('.')[0]}.csv"
        )

        event_validation.validate(event_file_path, validated_event_file_path)


def main():
    ais_input_directory = get_enviroment_variable("AIS_INPUT_DIRECTORY")
    ais_simplified_directory = get_enviroment_variable("AIS_SIMPLIFIED_DIRECTORY")
    ais_port_events_directory = get_enviroment_variable("AIS_PORT_EVENTS_DIRECTORY")
    ais_validated_port_events_directory = get_enviroment_variable("AIS_VALIDATED_PORT_EVENTS_DIRECTORY")


    # Data-Preparation ##################################################################################
    simplification(ais_input_directory, ais_simplified_directory)

    # Port-Event-Processing #############################################################################
    extraction(ais_simplified_directory, ais_port_events_directory, ["2020"])

    validation(ais_port_events_directory, ais_validated_port_events_directory)

    # Port-Cluster generation ###########################################################################
    gdf = cluster_generation.generate(ais_validated_port_events_directory)

    # DDPI-Cleaning #####################################################################################
    gdf = overlap.remove(gdf)

    # DDPI-Enrichment ###################################################################################
    gdf = geo_information_enrichment.enrich(gdf)

    # DDPI Export #######################################################################################
    export.as_geojson(gdf, "ddpi.geojson")


if __name__ == "__main__":
    main()
