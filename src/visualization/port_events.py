import os
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv(override=True)

sns.set_style("darkgrid")

MMSI_WANTED = 229600000
DATE = "2020-01-1[8-9]"


def get_messages(mmsi: str) -> pl.DataFrame:
    input_directory = os.getenv("AIS_SIMPLIFIED_DIRECTORY")
    df = pl.read_parquet(os.path.join(input_directory, f"{DATE}*.parquet"))

    df = df.filter(pl.col("MMSI") == mmsi)

    return df


def plot_column(column: str, df: pl.DataFrame, name: str, label=""):
    # setting the dimensions of the plot
    fig, ax = plt.subplots(figsize=(10, 8))

    sns.lineplot(x="TIMESTAMPUTC", y=column, markers=True, data=df, ax=ax)
    plt.ylabel(label)

    # draw vessel in port marker
    plt.axvspan("2020-01-18 20:24:00", "2020-01-19 18:59:00", facecolor="r", alpha=0.2)

    plt.tight_layout()

    plt.savefig(f"{name}.png")
    plt.clf()


def no_movement_aggregation(df: pl.DataFrame) -> pl.DataFrame:
    df_no_movement = df.group_by_dynamic(
        "TIMESTAMPUTC",
        every="15m",
        period="3h",
        group_by="MMSI",
    ).agg(pl.col("h3_cell").n_unique().alias("NUMBER_OF_H3_CELLS"))

    return df_no_movement


def destination_changed_aggregation(df: pl.DataFrame) -> pl.DataFrame:
    df_destination_changed = df.group_by_dynamic(
        "TIMESTAMPUTC",
        every="15m",
        period="3h",
        group_by="MMSI",
    ).agg(pl.col("DESTINATION").n_unique().sub(1).alias("DESTINATION_CHANGED"))

    return df_destination_changed


def main():
    df = get_messages(MMSI_WANTED)

    df = df.with_columns(
        (pl.col("COG").abs().sub(pl.col("TRUEHEADING").abs())).abs().alias("DRIFT"),
    )

    plot_column("COG", df, "cog", "course over ground (in degree)")
    plot_column("SOG", df, "sog", "speed over ground (in knots/hour)")
    plot_column("DRIFT", df, "drift", "drift (in degree)")
    plot_column("MAXDRAUGHT", df, "draught", "draught (in meter)")
    plot_column("TRUEHEADING", df, "heading", "heading (in degree)")
    plot_column("ROT", df, "rot", "rate of turn (in degree/minute)")
    plot_column("NAVSTATUSCODE", df, "nav_status", "navigation status code")

    df_no_movement = no_movement_aggregation(df)
    plot_column(
        "NUMBER_OF_H3_CELLS", df_no_movement, "no_movement_event", "number of h3 cells"
    )

    df_destination_changed = destination_changed_aggregation(df)
    plot_column(
        "DESTINATION_CHANGED",
        df_destination_changed,
        "destination_changed",
        "destination change",
    )


if __name__ == "__main__":
    main()
