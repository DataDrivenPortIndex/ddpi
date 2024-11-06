import pandas as pd
import geopandas as gpd

from h3ronpy.pandas.vector import geodataframe_to_cells
from h3ronpy import ContainmentMode


def export_as_h3(gdf: gpd.GeoDataFrame, resolution: int) -> pd.DataFrame:
    df_ddpi = geodataframe_to_cells(gdf, 10, containment_mode=ContainmentMode.Covers)

    df_ddpi["cell"] = df_ddpi["cell"].apply(hex)
    df_ddpi["cell"] = df_ddpi["cell"].str.replace("0x", "")

    return df_ddpi
