import polars as pl

MIN_DAYS = 10
EVENT_THRESHOLD = 0.35
PORT_THRESHOLD = 0.7
ANCHORAGE_THRESHOLD = 0.7
MICROSECONDS_IN_DAY = 864000
MIN_NUMBER_OF_VESSELS = 2
NO_SOG_EVENT_THRESHOLD = 0
NO_MOVEMENT_EVENT_THRESHOLD = 0


def min_max_feature_scaling(df: pl.LazyFrame, column: str) -> pl.LazyFrame:
    return df.with_columns(
        (pl.col(column) - pl.col(column).min())
        / (pl.col(column).max() - pl.col(column).min()).alias(column)
    )


def validate(port_events_input_file: str, port_events_output_file: str):
    pl.scan_parquet(port_events_input_file).group_by("h3_cell").agg(
        pl.col("LATITUDE").first(),
        pl.col("LONGITUDE").first(),
        pl.col("MMSI").n_unique().alias("number_of_unique_vessels"),
        pl.col("no_sog_event").mean(),
        pl.col("no_movement_event").mean(),
        pl.col("is_moored_event").mean(),
        pl.col("is_anchored_event").mean(),
        pl.col("drifting_event").mean(),
        pl.col("no_rate_of_turn_event").mean(),
        pl.col("destination_changed_event").mean(),
        pl.col("draught_changed_event").mean(),
        pl.col("towing_event").mean(),
        pl.col("last_timestamp").min().alias("first_timestamp"),
        pl.col("last_timestamp").max().alias("last_timestamp"),
    ).filter(
        (pl.col("number_of_unique_vessels") >= MIN_NUMBER_OF_VESSELS)
        & (
            (pl.col("no_sog_event") > NO_SOG_EVENT_THRESHOLD)
            | (pl.col("no_movement_event") > NO_MOVEMENT_EVENT_THRESHOLD)
        )
        & (
            pl.col("last_timestamp") - pl.col("first_timestamp")
            >= MICROSECONDS_IN_DAY * MIN_DAYS
        )
    ).with_columns(
        (
            pl.col("no_sog_event")
            .add(pl.col("no_rate_of_turn_event"))
            .add(pl.col("no_movement_event"))
            .add(pl.col("drifting_event"))
            .add(pl.col("draught_changed_event"))
            .add(pl.col("towing_event"))
            .add(pl.col("destination_changed_event"))
            .add(pl.col("is_moored_event"))
            .add(pl.col("is_anchored_event"))
        ).alias("event_score"),
        (pl.col("is_moored_event").sub(pl.col("is_anchored_event"))).alias(
            "port_score"
        ),
        (pl.col("is_anchored_event").sub(pl.col("is_moored_event"))).alias(
            "anchorage_score"
        ),
    ).with_columns(
        (pl.col("event_score") - pl.col("event_score").min())
        / (pl.col("event_score").max() - pl.col("event_score").min()).alias(
            "event_score"
        ),
        (pl.col("port_score") - pl.col("port_score").min())
        / (pl.col("port_score").max() - pl.col("port_score").min()).alias("port_score"),
        (pl.col("anchorage_score") - pl.col("anchorage_score").min())
        / (pl.col("anchorage_score").max() - pl.col("anchorage_score").min()).alias(
            "port_score"
        ),
    ).collect(streaming=True).write_csv(port_events_output_file)
