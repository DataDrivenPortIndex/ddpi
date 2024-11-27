import numpy as np
import pandas as pd
import geopandas as gpd
import fast_geo_distance


DDPI_BUFFER = 15000
COUNTRY_FILE = "data/[1,2,3].geojson"
WPI_FILE = "data/wpi.geojson"
CITY_FILE = "data/cities.geojson"


def build_wpi_distance_dict(poi_gdf):
    poi_gdf = poi_gdf.drop_duplicates(subset=["World Port Index Number"])
    wpi_id = poi_gdf["World Port Index Number"].to_list()
    wpi_name = poi_gdf["Main Port Name"].to_list()
    distance = poi_gdf["distance"].to_list()

    return [
        {"id": wpi_id[i], "name": wpi_name[i], "distance": distance[i]}
        for i in range(len(wpi_id))
    ]


def build_city_distance_dict(poi_gdf):
    poi_gdf = poi_gdf.drop_duplicates(subset=["name"])
    city_name = poi_gdf["name"].to_list()
    country_name = poi_gdf["country_name"].to_list()
    distance = poi_gdf["distance"].to_list()

    return [
        {"name": city_name[i], "country": country_name[i], "distance": distance[i]}
        for i in range(len(city_name))
    ]


def calculate_poi_distance(port_point, poi_gdf: gpd.GeoDataFrame):
    poi_points = [(point.y, point.x) for point in poi_gdf.geometry.to_list()]

    poi_list = []

    for point in split_port_polygon_into_n_sepments(port_point, 5):
        tmp_poi_gdf = poi_gdf.copy()
        tmp_poi_gdf["distance"] = fast_geo_distance.batch_geodesic(
            point.y, point.x, poi_points
        )

        tmp_poi_gdf = tmp_poi_gdf[tmp_poi_gdf["distance"] <= DDPI_BUFFER]

        poi_list.append(tmp_poi_gdf)

    poi_gdf = pd.concat(poi_list).drop_duplicates(keep=False)

    return poi_gdf.nsmallest(10, columns="distance")


def split_port_polygon_into_n_sepments(port_polygon, n=5):
    port_linestring = port_polygon.boundary

    distances = np.linspace(0, port_linestring.length, n)

    points = [port_linestring.interpolate(distance) for distance in distances]

    return points


def reduce_poi_gdf(poi_gdf: gpd.GeoDataFrame, ddpi_gdf: gpd.GeoDataFrame):
    negative_gdf = poi_gdf.copy()

    for _, row in ddpi_gdf.iterrows():
        negative_gdf = negative_gdf[~negative_gdf.within(row.geometry)]

    return pd.concat([poi_gdf, negative_gdf]).drop_duplicates(keep=False)


def enrich(ddpi_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ddpi_gdf = ddpi_gdf.to_crs("EPSG:3857")
    buffered_ddpi_gdf = ddpi_gdf.copy()
    buffered_ddpi_gdf["geometry"] = buffered_ddpi_gdf["geometry"].buffer(
        DDPI_BUFFER / 111111
    )

    # read wpi-file and reduce
    wpi_gdf = gpd.read_file(WPI_FILE)
    wpi_gdf["World Port Index Number"] = wpi_gdf["World Port Index Number"].astype(int)
    wpi_gdf = reduce_poi_gdf(wpi_gdf, buffered_ddpi_gdf)

    ddpi_gdf["wpi"] = ddpi_gdf.apply(
        lambda x: build_wpi_distance_dict(calculate_poi_distance(x.geometry, wpi_gdf)),
        axis=1,
    )

    # read city-file and reduce
    cities_gdf = gpd.read_file(CITY_FILE)
    cities_gdf = reduce_poi_gdf(cities_gdf, buffered_ddpi_gdf)

    ddpi_gdf["city"] = ddpi_gdf.apply(
        lambda x: build_city_distance_dict(
            calculate_poi_distance(x.geometry, cities_gdf)
        ),
        axis=1,
    )

    # country
    # country_gdf = gpd.read_file(COUNTRY_FILE)
    # print(country_gdf)

    ddpi_gdf = ddpi_gdf.to_crs("epsg:4326")

    return ddpi_gdf
