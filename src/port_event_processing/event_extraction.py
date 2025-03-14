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


def process_day(day_file: str) -> pl.LazyFrame:
    df_lazy = (
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
            by="MMSI",
        )
        .agg(
            pl.col("LATITUDE").first(),
            pl.col("LONGITUDE").first(),
            pl.col("SOG").max(),
            pl.col("h3_cell").first(),
            pl.col("SHIPANDCARGOTYPECODE").first(),
            pl.col("TIMESTAMPUTC").last().alias("last_timestamp"),
            pl.col("MAXDRAUGHT").unique(),
            pl.col("DESTINATION").unique(),
            pl.col("NAVSTATUSCODE").unique(),
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
        .with_columns(
            pl.col("NAVSTATUSCODE")
            .list.contains(NAV_STATUS_CODES["moored"])
            .alias("is_moored_event"),
            pl.col("NAVSTATUSCODE")
            .list.contains(NAV_STATUS_CODES["anchored"])
            .alias("is_anchored_event"),
        )
        .filter(
            (pl.col("is_moored_event"))
            | (pl.col("is_anchored_event"))
            | (pl.col("SOG") <= SPEED_OVER_GROUND_THRESHOLD)
            | (pl.col("number_of_h3_cells") == NUMBER_OF_H3_CELLS_THRESHOLD)
            | (pl.col("MAXDRAUGHT").len() >= DRAUGHT_COUNT_THRESHOLD)
            | (pl.col("drift_iqr") >= DRIFT_THRESHOLD)
            | (pl.col("cog_iqr") <= COG_IQR_THRESHOLD)
            | (pl.col("rate_of_turn_iqr") <= RATE_OF_TURN_THRESHOLD)
            | (pl.col("DESTINATION").len() >= DESTINATION_COUNT_THRESHOLD)
        )
        .with_columns(
            pl.when(pl.col("SOG") <= SPEED_OVER_GROUND_THRESHOLD)
            .then(True)
            .otherwise(False)
            .cast(pl.Boolean)
            .alias("no_sog_event"),
            pl.when(pl.col("number_of_h3_cells") == 1)
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("no_movement_event"),
            pl.when(pl.col("drift_iqr") >= DRIFT_THRESHOLD)
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("drifting_event"),
            pl.when(pl.col("rate_of_turn_iqr") <= RATE_OF_TURN_THRESHOLD)
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("no_rate_of_turn_event"),
            pl.when(pl.col("DESTINATION").len() >= 2)
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("destination_changed_event"),
            pl.when(pl.col("MAXDRAUGHT").len() >= 2)
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("draught_changed_event"),
            pl.when(pl.col("SHIPANDCARGOTYPECODE").is_in(TOWING_VESSEL_TYPES))
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("towing_event"),
            pl.when(pl.col("is_moored_event"))
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("is_moored_event"),
            pl.when(pl.col("is_anchored_event"))
            .then(True)
            .otherwise(False)
            .cast(pl.UInt8)
            .alias("is_anchored_event"),
        )
        .drop(
            [
                "NAVSTATUSCODE",
                "SHIPANDCARGOTYPECODE",
                "DESTINATION",
                "MAXDRAUGHT",
                "number_of_messages",
                "SOG",
                "number_of_h3_cells",
                "drift_iqr",
                "rate_of_turn_iqr",
                "MAXDRAUGHT",
            ]
        )
    )

    return df_lazy.collect()
