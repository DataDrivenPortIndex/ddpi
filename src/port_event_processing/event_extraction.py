import polars as pl


DRIFT_THRESHOLD = 90
COG_IQR_THRESHOLD = 10
DRAUGHT_COUNT_THRESHOLD = 2
RATE_OF_TURN_THRESHOLD = 10
DYNAMIC_GROUPBY_EVERY = "30m"
DYNAMIC_GROUPBY_PERIOD = "6h"
TOWING_VESSEL_TYPES = [52, 53]
DESTINATION_COUNT_THRESHOLD = 2
MINIMUN_NUMBER_OF_MESSAGES = 30
NUMBER_OF_H3_CELLS_THRESHOLD = 1
SPEED_OVER_GROUND_THRESHOLD = 0.2
YEARS_TO_PROCESS = [2020, 2021, 2022]
NAV_STATUS_CODES = {"moored": 5, "anchored": 1}


def as_flag(condition: pl.Expr, dtype=pl.UInt8) -> pl.Expr:
    return condition.fill_null(False).cast(dtype)


def process_day(day_file: str) -> pl.LazyFrame:
    return (
        pl.scan_parquet(day_file)
        .with_columns(
            pl.col("NAVSTATUSCODE").cast(pl.Int64),
            (pl.col("COG").abs().sub(pl.col("TRUEHEADING").abs())).abs().alias("DRIFT"),
            pl.col("TIMESTAMPUTC").dt.replace_time_zone("UTC").set_sorted(),
        )
        .group_by_dynamic(
            "TIMESTAMPUTC",
            every=DYNAMIC_GROUPBY_EVERY,
            period=DYNAMIC_GROUPBY_PERIOD,
            group_by="MMSI",
        )
        .agg(
            pl.col("LATITUDE").first(),
            pl.col("LONGITUDE").first(),
            pl.col("SOG").max(),
            pl.col("h3_cell").first(),
            pl.col("SHIPANDCARGOTYPECODE").first(),
            pl.col("TIMESTAMPUTC").last().alias("last_timestamp"),
            pl.col("MAXDRAUGHT").n_unique().alias("number_of_draughts"),
            pl.col("DESTINATION").n_unique().alias("number_of_destinations"),
            pl.col("NAVSTATUSCODE")
            .eq(NAV_STATUS_CODES["moored"])
            .any()
            .alias("is_moored_event"),
            pl.col("NAVSTATUSCODE")
            .eq(NAV_STATUS_CODES["anchored"])
            .any()
            .alias("is_anchored_event"),
            pl.col("MMSI").count().alias("number_of_messages"),
            pl.col("h3_cell").n_unique().alias("number_of_h3_cells"),
            (pl.col("COG").quantile(0.25).sub(pl.col("COG").quantile(0.75)))
            .abs()
            .alias("cog_iqr"),
            (pl.col("DRIFT").quantile(0.25).sub(pl.col("DRIFT").quantile(0.75)))
            .abs()
            .alias("drift_iqr"),
            (pl.col("ROT").quantile(0.25) - pl.col("ROT").quantile(0.75))
            .abs()
            .alias("rate_of_turn_iqr"),
        )
        .filter(pl.col("number_of_messages") >= MINIMUN_NUMBER_OF_MESSAGES)
        .filter(
            (pl.col("is_moored_event"))
            | (pl.col("is_anchored_event"))
            | (pl.col("SOG") <= SPEED_OVER_GROUND_THRESHOLD)
            | (pl.col("number_of_h3_cells") == NUMBER_OF_H3_CELLS_THRESHOLD)
            | (pl.col("number_of_draughts") >= DRAUGHT_COUNT_THRESHOLD)
            | (pl.col("drift_iqr") >= DRIFT_THRESHOLD)
            | (pl.col("cog_iqr") <= COG_IQR_THRESHOLD)
            | (pl.col("rate_of_turn_iqr") <= RATE_OF_TURN_THRESHOLD)
            | (pl.col("number_of_destinations") >= DESTINATION_COUNT_THRESHOLD)
        )
        .with_columns(
            as_flag(pl.col("SOG") <= SPEED_OVER_GROUND_THRESHOLD, pl.Boolean).alias(
                "no_sog_event"
            ),
            as_flag(pl.col("number_of_h3_cells") == 1).alias("no_movement_event"),
            as_flag(pl.col("drift_iqr") >= DRIFT_THRESHOLD).alias("drifting_event"),
            as_flag(pl.col("rate_of_turn_iqr") <= RATE_OF_TURN_THRESHOLD).alias(
                "no_rate_of_turn_event"
            ),
            as_flag(
                pl.col("number_of_destinations") >= DESTINATION_COUNT_THRESHOLD
            ).alias("destination_changed_event"),
            as_flag(pl.col("number_of_draughts") >= DRAUGHT_COUNT_THRESHOLD).alias(
                "draught_changed_event"
            ),
            as_flag(pl.col("SHIPANDCARGOTYPECODE").is_in(TOWING_VESSEL_TYPES)).alias(
                "towing_event"
            ),
            as_flag(pl.col("is_moored_event")).alias("is_moored_event"),
            as_flag(pl.col("is_anchored_event")).alias("is_anchored_event"),
        )
        .drop(
            [
                "SHIPANDCARGOTYPECODE",
                "number_of_destinations",
                "number_of_draughts",
                "number_of_messages",
                "SOG",
                "number_of_h3_cells",
                "drift_iqr",
                "rate_of_turn_iqr",
            ]
        )
    )
