import pandas as pd
import geopandas as gpd

from shapely import wkt


CSV_INPUT_FILE = "../../data/ddpi.csv"
GEOJSON_FILE = "../../data/ddpi.geojson"


def main():
    df = pd.read_csv(CSV_INPUT_FILE)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326')

    gdf.to_file(GEOJSON_FILE, driver="GeoJSON")  
    


if __name__ == "__main__":
    main()
