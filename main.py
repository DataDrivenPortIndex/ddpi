
import os

from tqdm import tqdm
from dotenv import load_dotenv

from src.pre_processing import ais_simplification
from src.errors.env import MissingEnvironmentVariable



load_dotenv()


def get_env(name: str) -> str:
    value = os.getenv(name)

    print(value)

    if value != "" and "XXXXX" not in value:
        return value

    raise MissingEnvironmentVariable(f"Enviroment variable'{name}' does not exist")



def main():
    # ais simplification
    ais_input_directory = get_env("AIS_INPUT_DIRECTORY")

    for day_file in tqdm(os.listdir(ais_input_directory)):
        ais_simplification.simplifiy(day_file)

    # event extraction


    # event validation



if __name__ == "__main__":
    main()