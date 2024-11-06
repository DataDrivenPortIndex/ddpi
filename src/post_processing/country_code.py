import geopandas as gpd

# TODO find geojson with better resolution
COUNTRIES_GEOJSON = "data/countries.geojson"


def read_countries_geojson() -> gpd.GeoDataFrame:
    countries_df = gpd.read_file(COUNTRIES_GEOJSON)

    return countries_df[["adm0_a3", "geometry"]]


def add_country_code(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf_countries = read_countries_geojson()

    gdf_ddpi_with_country_codes = gpd.sjoin(
        gdf, gdf_countries, how="left", predicate="intersects"
    )

    gdf_ddpi_with_country_codes = gdf_ddpi_with_country_codes[
        ["geometry", "adm0_a3", "is_anchorage"]
    ]

    gdf_ddpi_with_country_codes.rename(
        columns={"adm0_a3": "country_code"}, inplace=True
    )

    return gdf_ddpi_with_country_codes
