import geopandas as gpd

from h3ronpy.pandas.vector import geodataframe_to_cells
from h3ronpy import ContainmentMode


H3_POLYFILL_MODE = ContainmentMode.Covers


def as_h3_csv(gdf: gpd.GeoDataFrame, file_name: str, resolution: int):
    df_ddpi = geodataframe_to_cells(gdf, resolution, containment_mode=H3_POLYFILL_MODE)

    df_ddpi["cell"] = df_ddpi["cell"].apply(hex)
    df_ddpi["cell"] = df_ddpi["cell"].str.replace("0x", "")

    df_ddpi.to_csv(file_name, index=False)


def as_csv(gdf: gpd.GeoDataFrame, file_name: str):
    gdf.to_csv(file_name, index=False)
