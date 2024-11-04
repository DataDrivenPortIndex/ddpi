
import os

from tqdm import tqdm
from dotenv import load_dotenv

from src.errors.env import MissingEnvironmentVariable


load_dotenv()


def load_env(name: str) -> str:
    value = os.getenv(name)

    print(value)

    if value != "":
        return value

    raise MissingEnvironmentVariable(f"Enviroment variable'{name}' does not exist")



def main():
    # ais simplification

    ais_input_directory = load_env("AIS_INPUT_DIRECTORY")

    for i in tqdm(os.listdir(ais_input_directory)):
        print(i)

if __name__ == "__main__":
    main()