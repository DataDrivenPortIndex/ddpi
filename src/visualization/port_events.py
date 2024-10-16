import os
import polars as pl
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("darkgrid")

MMSI_WANTED = 229600000
INPUT_DIRECTORY = "data/simplified_ais"
DATE = "2020-01-1[8-9]"


def get_messages(mmsi: str) -> pd.DataFrame:
    df = pl.read_parquet(os.path.join(INPUT_DIRECTORY, f"{DATE}*.parquet"))
    # df = pd.read_parquet(os.path.join(INPUT_DIRECTORY, f"{DATE}.parquet"))
    df = df.to_pandas()

    return df[df["MMSI"]==MMSI_WANTED]


def plot_column(column: str, df: pd.DataFrame, name: str, label=""):
    # setting the dimensions of the plot
    fig, ax = plt.subplots(figsize=(10, 8))

    sns.lineplot(x="TIMESTAMPUTC", y=column, markers=True, data=df, ax=ax)
    plt.ylabel(label)
    
    # draw vessel in port marker
    plt.axvspan("2020-01-18 20:24:00", "2020-01-19 18:59:00", facecolor='r', alpha=0.2)

    plt.tight_layout()

    plt.savefig(f"{name}.png")
    plt.clf()


def main():
    df = get_messages(MMSI_WANTED)

    df["DRIFT"] = (df["COG"].abs() - df["TRUEHEADING"].abs()).abs()

    plot_column("COG", df, "cog", "course over ground (in degree)")
    plot_column("SOG", df, "sog", "speed over ground (in knots/hour)")
    plot_column("DRIFT", df, "drift", "drift (in degree)")
    plot_column("MAXDRAUGHT", df, "draught", "draught (in meter)")
    plot_column("TRUEHEADING", df, "heading", "heading (in degree)")
    plot_column("ROT", df, "rot", "rate of turn (in degree/minute)")
    plot_column("NAVSTATUSCODE", df, "nav_status", "navigation status code")

    df[["TIMESTAMPUTC", "NAVSTATUSCODE"]].to_csv(f"{MMSI_WANTED}.csv")


if __name__ == "__main__":
    main()
