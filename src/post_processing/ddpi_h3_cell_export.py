import h3
import json
import numpy as np
import pandas as pd
import geopandas as gpd

from typing import Set
from shapely.geometry import Polygon


DDPI_CSV_FILE = "data/ddpi.csv"
H3_RESOLUTIONS = [10]


def polyfill(polygon: Polygon, resolution: int) -> Set[str]:
    return h3.polyfill(
        json.loads(gpd.GeoSeries([polygon]).to_json())["features"][0]["geometry"],
        resolution,
        geo_json_conformant=True
    )


def get_buffer_size(resolution: int) -> float:
    return h3.edge_length(resolution, unit="m")


def buffer_polygon(df: gpd.GeoDataFrame, buffer: float) -> gpd.GeoDataFrame:
    df = df.to_crs("EPSG:6622")
    df["geometry"] = df["geometry"].buffer(buffer)

    return df.to_crs("EPSG:4326")


def main():
    ddpi_df = pd.read_csv(DDPI_CSV_FILE)
    ddpi_gdf = gpd.GeoDataFrame(ddpi_df, geometry=gpd.GeoSeries.from_wkt(ddpi_df["geom"]))[["id", "geometry"]]

    ddpi_gdf.crs = "EPSG:4326"

    for h3_resolution in H3_RESOLUTIONS:
        buffer = get_buffer_size(h3_resolution)
        buffered_ddpi_gdf = buffer_polygon(ddpi_gdf, buffer)
        buffered_ddpi_gdf.to_csv(f"data/{h3_resolution}.csv")
        buffered_ddpi_gdf["h3_cells"] = np.vectorize(polyfill)(buffered_ddpi_gdf["geometry"], h3_resolution)
        buffered_ddpi_gdf[["id", "h3_cells"]].explode("h3_cells").to_csv(f"h3_cells_resolution_{h3_resolution}.csv", index=False)


if __name__ == "__main__":
    main()
