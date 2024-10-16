import os
import tqdm
import polars as pl


STATIC_MESSAGES = [5]
YEARS_WANTED = ["2020"]
DYNAMIC_MESSAGES = [1, 2, 3]
PORT_CELLS_FILE = "data/h3_cells_11.csv"
INPUT_DIRECTORY = "/media/pbusenius/BigData/AIS"
COLUMNS = ["MMSI", "MESSAGEID", "MAXDRAUGHT", "TIMESTAMPUTC", "TRUEHEADING", "h3_cell"]


def get_static_messages(df: pl.LazyFrame) -> pl.LazyFrame:
    return df.filter(
        pl.col("MESSAGEID").is_in(STATIC_MESSAGES)
    ).select(
        ["MMSI", "TIMESTAMPUTC", "MAXDRAUGHT"]
    ).drop_nulls(
        ["MAXDRAUGHT"]
    )


def get_dynamic_messages(df: pl.LazyFrame, port_cells: pl.LazyFrame) -> pl.LazyFrame:
    return df.filter(
        pl.col("MESSAGEID").is_in(DYNAMIC_MESSAGES)
    ).join(
        other=port_cells, left_on="h3_cell", right_on="h3_cells", how="left"
    ).drop_nulls(
        ["TRUEHEADING", "id"]
    ).select(
        ["MMSI", "TIMESTAMPUTC", "TRUEHEADING", "h3_cell", "id"]
    )


def process_day(df: pl.DataFrame, port_cells: pl.DataFrame) -> pl.DataFrame:
    df_static = get_static_messages(df)
    df_dynamic = get_dynamic_messages(df, port_cells)

    df = df_dynamic.join_asof(other=df_static, on="TIMESTAMPUTC", by="MMSI", tolerance="60m", strategy="forward")

    return df.groupby("h3_cell").agg(
        pl.col("MAXDRAUGHT").mean().alias("draught"),
        pl.col("TRUEHEADING").mean().alias("heading")
    )
    

def main():
    port_stats = None

    port_cells_df = pl.read_csv(PORT_CELLS_FILE)
    for year in YEARS_WANTED:
        year_path = os.path.join(INPUT_DIRECTORY, year)
        for day in tqdm.tqdm(os.listdir(year_path)):
            try:
                df = pl.read_parquet(f"{os.path.join(year_path, day)}/*.parquet", columns=COLUMNS)
                df = process_day(df, port_cells_df)

                if port_stats is not None:
                    port_stats.extend(df)
                else:
                    port_stats = df
            except:
                print(day)
                break

    port_stats.groupby("h3_cell").agg(
        pl.col("draught").mean(),
        pl.col("heading").mean(),
    ).write_csv("port_stats.csv")


if __name__ == "__main__":
    main()
