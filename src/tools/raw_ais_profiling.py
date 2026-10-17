import os
import sys
import polars as pl

from dotenv import load_dotenv

from src.data_preparation import ais_simplification

# Profiles one day of raw AIS data before simplification:
# - full schema and value ranges (units of SOG/COG/TRUEHEADING/ROT)
# - AIS "not available" values per message type
# - message 24 parts and how many vessels survive the class a/b static join
#
# usage (from the repository root):
#   python -m src.tools.raw_ais_profiling [day_directory]

load_dotenv(override=True)


POSITION_MESSAGES = [1, 2, 3, 18, 19]
NUMERIC_COLUMNS = [
    "SOG",
    "COG",
    "TRUEHEADING",
    "ROT",
    "LATITUDE",
    "LONGITUDE",
    "MAXDRAUGHT",
    "SIZEA",
    "SIZEB",
    "SIZEC",
    "SIZED",
    "SHIPANDCARGOTYPECODE",
    "NAVSTATUSCODE",
]


def number(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Float64)


def unavailable_checks() -> dict[str, pl.Expr]:
    destination = pl.col("DESTINATION").cast(pl.String)

    return {
        "TRUEHEADING == 511": number("TRUEHEADING") == 511,
        "COG >= 360": number("COG") >= 360,
        "SOG >= 102.3": number("SOG") >= 102.3,
        "ROT == -128": number("ROT") == -128,
        "abs(ROT) >= 127": number("ROT").abs() >= 127,
        "LATITUDE not in [-90, 90]": number("LATITUDE").abs() > 90,
        "LONGITUDE not in [-180, 180]": number("LONGITUDE").abs() > 180,
        "LATITUDE/LONGITUDE == 0/0": (number("LATITUDE") == 0)
        & (number("LONGITUDE") == 0),
        "LATITUDE/LONGITUDE not finite": ~number("LATITUDE").is_finite()
        | ~number("LONGITUDE").is_finite(),
        "MAXDRAUGHT == 0": number("MAXDRAUGHT") == 0,
        "any SIZE == 0": pl.any_horizontal(
            number(column) == 0 for column in ["SIZEA", "SIZEB", "SIZEC", "SIZED"]
        ),
        "SHIPANDCARGOTYPECODE == 0": number("SHIPANDCARGOTYPECODE") == 0,
        "NAVSTATUSCODE == 15": number("NAVSTATUSCODE") == 15,
        "DESTINATION empty": destination.str.strip_chars() == "",
        "DESTINATION contains @": destination.str.contains("@", literal=True),
        "DESTINATION untrimmed": destination != destination.str.strip_chars(),
    }


def value_ranges(lf: pl.LazyFrame, schema: pl.Schema) -> pl.LazyFrame:
    return pl.concat(
        [
            lf.select(
                pl.lit(column).alias("column"),
                pl.lit(str(schema[column])).alias("dtype"),
                pl.col(column).null_count().alias("nulls"),
                number(column).min().alias("min"),
                number(column).max().alias("max"),
            )
            for column in NUMERIC_COLUMNS
        ]
    )


def unavailable_values(lf: pl.LazyFrame) -> pl.LazyFrame:
    return (
        lf.group_by("MESSAGEID")
        .agg(
            pl.len().alias("messages"),
            pl.col("MMSI").n_unique().alias("vessels"),
            *[
                check.fill_null(False).sum().alias(name)
                for name, check in unavailable_checks().items()
            ],
        )
        .sort("MESSAGEID")
    )


def message_24_parts(lf: pl.LazyFrame, schema: pl.Schema) -> pl.LazyFrame:
    part_columns = [column for column in schema.names() if "PART" in column.upper()]
    message_24 = lf.filter(pl.col("MESSAGEID") == 24)

    # without a part number column, part b is the one carrying the ship type
    if part_columns:
        return message_24.group_by(part_columns).agg(pl.len().alias("messages"))

    return message_24.group_by(
        pl.col("SHIPANDCARGOTYPECODE").is_not_null().alias("has_ship_type (part b)")
    ).agg(pl.len().alias("messages"))


def static_join_survival(lf: pl.LazyFrame) -> pl.LazyFrame:
    lf = lf.select(ais_simplification.AIS_COLUMNS)

    return pl.concat(
        [
            pl.concat(
                [
                    lf.filter(pl.col("MESSAGEID").is_in(mode_config["position"]))
                    .select(pl.col("MMSI").n_unique().alias("vessels_with_positions")),
                    ais_simplification.class_messages(lf, mode_config).select(
                        pl.col("MMSI").n_unique().alias("vessels_after_static_join")
                    ),
                ],
                how="horizontal",
            ).with_columns(pl.lit(name).alias("class"))
            for name, mode_config in [
                ("a", ais_simplification.CLASS_A_MESSAGES),
                ("b", ais_simplification.CLASS_B_MESSAGES),
            ]
        ]
    ).select("class", "vessels_with_positions", "vessels_after_static_join")


def default_day_directory() -> str:
    input_directory = os.getenv("AIS_INPUT_DIRECTORY")

    return os.path.join(input_directory, sorted(os.listdir(input_directory))[0])


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else default_day_directory()

    lf = pl.scan_parquet(f"{day}/*type_cast.parquet")
    schema = lf.collect_schema()

    ranges, unavailable, parts, survival = pl.collect_all(
        [
            value_ranges(lf, schema),
            unavailable_values(lf),
            message_24_parts(lf, schema),
            static_join_survival(lf),
        ]
    )

    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=200, fmt_str_lengths=40):
        print(f"day: {day}\n\nschema:")
        for column, dtype in schema.items():
            print(f"  {column}: {dtype}")

        print("\nvalue ranges:")
        print(ranges)

        print(f"\nnot available values per message type (position: {POSITION_MESSAGES}):")
        print(
            unavailable.with_columns(pl.col("MESSAGEID").cast(pl.String)).transpose(
                include_header=True, header_name="check", column_names="MESSAGEID"
            )
        )

        print("\nmessage 24 parts:")
        print(parts)

        print("\nstatic join survival (current simplification logic):")
        print(survival)


if __name__ == "__main__":
    main()
