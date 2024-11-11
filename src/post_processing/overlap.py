import geopandas as gpd


DDPI_FILE = "ddpi.geojson"
CITIES_FILE = "cities.json"
DISTANCE_FILE = "hub_line_distance.geojson"
DISTANCE_THRESHOLD = 20
DDPI_FILE_OUTPUT = "ddpi_v2.geojson"


def remove(ddpi_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ddpi_gdf = ddpi_gdf.sjoin(ddpi_gdf, how="left", predicate="intersects")
    ddpi_gdf = ddpi_gdf.dissolve("ddpi_id_right")

    ddpi_gdf = ddpi_gdf.reset_index().dissolve("ddpi_id_left")

    ddpi_gdf = ddpi_gdf.drop(["ddpi_id_right", "is_anchorage_right", "index_right"], axis=1).reset_index()

    return ddpi_gdf.rename(columns={"ddpi_id_left": "ddpi_id", "is_anchorage_left": "is_anchorage"})
