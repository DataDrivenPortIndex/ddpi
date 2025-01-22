import glob
import pandas as pd
import geopandas as gpd

from shapely import geometry
from sklearn.cluster import DBSCAN


DBSCAN_EPS = 0.02
DBSCAN_MIN_SAMPLES = 5
POLYFON_BUFFER = 0.003
PORT_THRESHOLD = 0.6
ANCHORAGE_THRESHOLD = 0.6


def cluster_points(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    clustering = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES).fit(
        gdf[["LONGITUDE", "LATITUDE"]].to_numpy()
    )
    gdf["cluster_id"] = clustering.labels_

    gdf = gdf[gdf.cluster_id >= 0]

    return gdf


def get_data_from_csv(directory: str) -> gpd.GeoDataFrame:
    df = pd.concat([pd.read_csv(file) for file in glob.glob(f"{directory}/*.csv")])
    # df = pd.read_csv(file)

    df = df[
        (df["port_score"] >= PORT_THRESHOLD)
        | (df["anchorage_score"] >= ANCHORAGE_THRESHOLD)
    ]

    df = pd.DataFrame(
        df.values.repeat(df["number_of_unique_vessels"], axis=0), columns=df.columns
    )

    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["LONGITUDE"], df["LATITUDE"])
    )


def create_polygon(gdf: gpd.GeoDataFrame, buffer=False) -> gpd.GeoDataFrame:
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
        port_gdf["geometry"] = port_gdf.geometry.buffer(POLYFON_BUFFER)

    port_gdf = port_gdf.loc[port_gdf.geometry.geometry.type == "Polygon"]

    return port_gdf


def combine_port_anchorage(
    gdf_port: gpd.GeoDataFrame, gdf_anchorage: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    ddpi_gdf = pd.concat([gdf_port, gdf_anchorage], ignore_index=True)

    ddpi_gdf["id"] = range(len(ddpi_gdf))
    ddpi_gdf.insert(0, "ddpi_id", ddpi_gdf["id"])

    ddpi_gdf.drop("id", axis=1, inplace=True)

    return ddpi_gdf


def filter_port_type(
    gdf: gpd.GeoDataFrame, field: str, threshold: int
) -> gpd.GeoDataFrame:
    return gdf[gdf[field] >= threshold].copy()


def generate(validated_port_events_directory: str) -> gpd.GeoDataFrame:
    gdf = get_data_from_csv(validated_port_events_directory)

    # process ports #####################################################################################
    port_gdf = filter_port_type(gdf, "port_score", PORT_THRESHOLD)
    port_gdf = cluster_points(port_gdf)
    port_gdf = create_polygon(port_gdf, buffer=True)
    port_gdf.drop(columns=["cluster_id"], inplace=True, axis=1)
    port_gdf["is_anchorage"] = False

    # process anchorages ################################################################################
    anchorage_gdf = filter_port_type(gdf, "anchorage_score", ANCHORAGE_THRESHOLD)
    anchorage_gdf = cluster_points(anchorage_gdf)
    anchorage_gdf = create_polygon(anchorage_gdf, buffer=True)
    anchorage_gdf.drop(["cluster_id"], inplace=True, axis=1)
    anchorage_gdf["is_anchorage"] = True

    # combine ports and anchorages ######################################################################
    gdf_ddpi = combine_port_anchorage(port_gdf, anchorage_gdf)

    gdf_ddpi = gdf_ddpi.set_crs("epsg:4326")

    return gdf_ddpi
