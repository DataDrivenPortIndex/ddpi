import geopandas as gpd


DDPI_FILE = "ddpi.geojson"
CITIES_FILE = "cities.json"
DISTANCE_FILE = "hub_line_distance.geojson"
DISTANCE_THRESHOLD = 20
DDPI_FILE_OUTPUT = "ddpi_v2.geojson"


def spatial_join(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.sjoin(gdf, how="left", predicate="intersects")
    gdf = gdf.dissolve("ddpi_id_right")

    gdf = gdf.reset_index().dissolve("ddpi_id_left")

    gdf =  gdf.drop(["ddpi_id_right", "is_anchorage_right", "index_right"], axis=1).reset_index()

    return gdf.rename(columns={"ddpi_id_left": "ddpi_id", "is_anchorage_left": "is_anchorage"})

    

def remove(ddpi_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    number_of_ports = len(ddpi_gdf)
    
    ddpi_gdf = spatial_join(ddpi_gdf)

    if number_of_ports == len(ddpi_gdf):
        return ddpi_gdf

    return remove(ddpi_gdf)
