import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.geometry

from shapely import geometry
from h3.api import basic_int as h3
from sklearn.cluster import DBSCAN


PORT_THRESHOLD = 0.6
ANCHORAGE_THRESHOLD = 0.6
PORT_EVENTS_FILE = "validated_port_events.csv"


def h3_to_geo(h3_cell: int):
    try:
        return h3.h3_to_geo(h3_cell)
    except Exception:
        return pd.NA, pd.NA


def cluster_points(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    clustering = DBSCAN(eps=0.02, min_samples=5).fit(
        gdf[["LONGITUDE", "LATITUDE"]].to_numpy()
    )
    gdf["cluster_id"] = clustering.labels_

    gdf = gdf[gdf.cluster_id >= 0]

    return gdf


def get_data_from_csv(file: str) -> gpd.GeoDataFrame:
    df = pd.read_csv(file)

    df = df[
        (df["port_score"] >= PORT_THRESHOLD)
        | (df["anchorage_score"] >= ANCHORAGE_THRESHOLD)
    ]

    df["LATITUDE"], df["LONGITUDE"] = np.vectorize(h3_to_geo)(df["h3_cell"])

    df = pd.DataFrame(
        df.values.repeat(df["number_of_unique_vessels"], axis=0), columns=df.columns
    )

    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["LONGITUDE"], df["LATITUDE"])
    )


def create_port_polygon(gdf: gpd.GeoDataFrame, buffer=False) -> gpd.GeoDataFrame:
    port_gdf = (
        gdf.groupby(["cluster_id"])
        .agg(
            {
                "geometry": lambda x: geometry.MultiPoint(list(x.geometry)).convex_hull,
            }
        )
        .reset_index()
    )

    port_gdf = port_gdf.set_geometry("geometry")

    if buffer:
        port_gdf["geometry"] = port_gdf.geometry.buffer(0.003)

    port_gdf = port_gdf.loc[port_gdf.geometry.geometry.type == "Polygon"]

    return port_gdf


def polyfill(port_polygon: str, h3_resolution: int):
    return h3.polyfill(
        shapely.geometry.mapping(port_polygon), h3_resolution, geo_json_conformant=False
    )


def main():
    gdf = get_data_from_csv(PORT_EVENTS_FILE)

    ports_gdf = gdf[gdf["port_score"] >= PORT_THRESHOLD].copy()
    anchorage_gdf = gdf[gdf["anchorage_score"] >= ANCHORAGE_THRESHOLD].copy()

    gdf_ports = cluster_points(ports_gdf)
    gdf_anchorage = cluster_points(anchorage_gdf)

    gdf_ports = create_port_polygon(gdf_ports, buffer=False)
    gdf_anchorage = create_port_polygon(gdf_anchorage, buffer=False)

    gdf_ports.drop(columns=["cluster_id"], inplace=True, axis=1)
    gdf_anchorage.drop(["cluster_id"], inplace=True, axis=1)

    gdf_anchorage["geometry"] = gdf_anchorage["geometry"].simplify(0.000001)

    gdf_ports["is_anchorage"] = False
    gdf_anchorage["is_anchorage"] = True

    gdf_ports.to_csv("ddpi_ports.csv")
    gdf_anchorage.to_csv("ddpi_anchorage.csv")

    ddpi_gdf = pd.concat([gdf_ports, gdf_anchorage])
    ddpi_gdf.rename(columns={"geometry": "geom"}, inplace=True)
    ddpi_gdf.index.name = "id"

    ddpi_gdf.to_csv("ddpi.csv")


if __name__ == "__main__":
    main()
