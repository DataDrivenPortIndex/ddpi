import pandas as pd
import geopandas as gpd


geojsonInput = "custom.geo.json"
countries_df = gpd.read_file(geojsonInput)
countries_df = countries_df[["adm0_a3", "geometry"]]

ddpi_df = pd.read_csv("ddpi.csv")
ddpi_df = gpd.GeoDataFrame(ddpi_df, geometry=gpd.GeoSeries.from_wkt(ddpi_df["geom"]))
ddpi_df = ddpi_df.set_crs("epsg:4326")


ddpi_with_iso_code_df = gpd.sjoin(ddpi_df, countries_df, how="left", predicate="intersects")

ddpi_with_iso_code_df = ddpi_with_iso_code_df[["geometry", "adm0_a3", "is_anchorage"]]

ddpi_with_iso_code_df.rename(columns={"adm0_a3": "country_code"}, inplace=True)
ddpi_with_iso_code_df.index.name = "id"

ddpi_with_iso_code_df.to_csv("ddpi.csv")
ddpi_with_iso_code_df.to_parquet("ddpi.parquet")
