import polars as pl

from typing import List


PORT_EVENTS_FILES = ["port_events2020.parquet", "port_events2021.parquet", "port_events2022.parquet"]
MIN_DAYS = 30
EVENT_THRESHOLD = 0.35
PORT_THRESHOLD = 0.7
ANCHORAGE_THRESHOLD = 0.7
MICROSECONDS_IN_DAY = 86400000
MIN_NUMBER_OF_VESSELS = 2
NO_SOG_EVENT_THRESHOLD = 0
NO_MOVEMENT_EVENT_THRESHOLD = 0
EVENT_SCORE_COLUMNS = ["no_sog_event", "no_movement_event", "drifting_event", "draught_changed_event",
                       "towing_event", "destination_changed_event", "moored_event", "anchored_event"]


def min_max_feature_scaling(df: pl.LazyFrame, column: str) -> pl.LazyFrame:
    return df.with_columns(
        (pl.col(column) - pl.col(column).min()) / (pl.col(column).max() - pl.col(column).min()).alias(column)
    )


def process_port_events(port_event_file: str):
    pl.scan_parquet(port_event_file).groupby("h3_cell").agg(
        pl.col("LATITUDE").first(),
        pl.col("LONGITUDE").first(),
        pl.col("MMSI").n_unique().alias("number_of_unique_vessels"),
        pl.col("no_sog_event").mean(),
        pl.col("no_movement_event").mean(),
        pl.col("moored_event").mean(),
        pl.col("anchored_event").mean(),
        pl.col("drifting_event").mean(),
        pl.col("rate_of_turn_event").mean(),
        pl.col("destination_changed_event").mean(),
        pl.col("draught_changed_event").mean(),
        pl.col("towing_event").mean(),
        pl.col("last_timestamp").min().alias("first_timestamp"),
        pl.col("last_timestamp").max().alias("last_timestamp")
    ).filter(
        (pl.col("number_of_unique_vessels") >= MIN_NUMBER_OF_VESSELS) &
        (
            (pl.col("no_sog_event") > NO_SOG_EVENT_THRESHOLD) |
            (pl.col("no_movement_event") > NO_MOVEMENT_EVENT_THRESHOLD) 
        ) &
        (pl.col("last_timestamp") - pl.col("first_timestamp") >= MICROSECONDS_IN_DAY * MIN_DAYS)
    ).with_columns(
        (pl.sum(EVENT_SCORE_COLUMNS)).alias("event_score"),
        (pl.col("moored_event").sub(pl.col("anchored_event"))).alias("port_score"),
        (pl.col("anchored_event").sub(pl.col("moored_event"))).alias("anchorage_score")
    ).with_columns(
        (pl.col("event_score") - pl.col("event_score").min()) / (pl.col("event_score").max() - pl.col("event_score").min()).alias("event_score"),
        (pl.col("port_score") - pl.col("port_score").min()) / (pl.col("port_score").max() - pl.col("port_score").min()).alias("port_score"),
        (pl.col("anchorage_score") - pl.col("anchorage_score").min()) / (pl.col("anchorage_score").max() - pl.col("anchorage_score").min()).alias("port_score"),
    ).collect(streaming=True).write_parquet(f"validated_{port_event_file}")


def combine_port_events(port_event_dfs: List[pl.DataFrame]):
    df = pl.concat(port_event_dfs)
    df.groupby("h3_cell").agg(
        pl.col("LATITUDE").first(),
        pl.col("LONGITUDE").first(),
        pl.col("number_of_unique_vessels").sum(),
        pl.col("no_sog_event").mean(),
        pl.col("no_movement_event").mean(),
        pl.col("moored_event").mean(),
        pl.col("anchored_event").mean(),
        pl.col("drifting_event").mean(),
        pl.col("rate_of_turn_event").mean(),
        pl.col("destination_changed_event").mean(),
        pl.col("draught_changed_event").mean(),
        pl.col("towing_event").mean(),
        pl.col("event_score").mean(),
        pl.col("port_score").mean(),
        pl.col("anchorage_score").mean(),
        pl.col("first_timestamp").min(),
        pl.col("last_timestamp").max()
    ).with_columns(
        ((pl.col("last_timestamp") - pl.col("first_timestamp")).cast(pl.Int64()) / MICROSECONDS_IN_DAY).alias("event_life_span")
    ).filter(
        (pl.col("event_score") >= EVENT_THRESHOLD) &
        (
            (pl.col("port_score") >= PORT_THRESHOLD) |
            (pl.col("anchorage_score") >= ANCHORAGE_THRESHOLD) 
        ) &
        (pl.col("number_of_unique_vessels") >= 10)
    ).drop(
        ["no_sog_event", "no_movement_event", "moored_event", "anchored_event",
        "drifting_event", "rate_of_turn_event", "destination_changed_event",
        "draught_changed_event", "towing_event"]
    ).with_columns(
        pl.col("number_of_unique_vessels").clip(1, 30)
    ).write_csv("validated_port_events.csv")


def main():
    for port_event_file in PORT_EVENTS_FILES:
        process_port_events(port_event_file)

    dfs = []
    for validated_port_events in PORT_EVENTS_FILES:
        df = pl.read_parquet(f"validated_{validated_port_events}")
        dfs.append(df)

    combine_port_events(dfs)



if __name__ == "__main__":
    main()
