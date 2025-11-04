"""SCRIPT RODADO NO SERVIDOR ARTAXO, DEVIDO À NECESSIDADE DE JUNÇÃO DE RASTERS
DE ALTA RESOLUÇÃO"""


# %%
from pathlib import Path
import glob
import rioxarray as rxr
from rioxarray.merge import merge_arrays
import geopandas as gpd
import numpy as np
from tqdm import tqdm
from shapely.geometry import Point


# %% Caminhos
inputs_path = Path('./data').resolve()
silt_fraction_path = inputs_path / 'silt_fraction'
roads_template_path = inputs_path / 'roads_template_old_grid.parquet'

# %%
# listing raster files
files = glob.glob(str(silt_fraction_path / '*.tif'))

# listing open rasters
raster_list = [rxr.open_rasterio(file) for file in files]

# Set crs for each raster
for raster in raster_list:
    raster.rio.write_crs("epsg:4326", inplace=True)

# Merge rasters
merged_raster = merge_arrays(dataarrays = raster_list,
                             nodata=0,
                             crs="EPSG:4326")

# %%
# Reading roads template
roads_template = gpd.read_parquet(roads_template_path)

# %%
roads_template.geometry.is_empty.sum()

# %%
# Exploding multilines
roads_template = roads_template.explode()

# Reformatting segment id values
roads_template['segment_id'] = roads_template['segment_id'].str.replace('segment_','').astype(np.int32)

# %%
roads_template.geom_type.unique()

# %%
# Explodir linhas em pontos mantendo 'segment_id'
rows = []

for row in tqdm(roads_template.itertuples()):
    for point in row.geometry.coords:
        rows.append({
            'segment_id': row.segment_id,
            'geometry': Point(point)
        })

# Criar novo GeoDataFrame com os pontos
points_gdf = gpd.GeoDataFrame(rows, crs=roads_template.crs)

# %%
# Amostrando valores de silt fraction nos pontos 
points_gdf.loc[:, 'silt_fraction'] = merged_raster.sel(
    x=points_gdf.geometry.x.to_xarray(),
    y=points_gdf.geometry.y.to_xarray(),
    method='nearest').values[0] # Aplicando valores da primeira banda nos pontos

# %%
# Aggregating silt fraction values by segment, calculating the mean value
points_gdf = (
    points_gdf
    .groupby('segment_id')
    .agg({'silt_fraction': 'mean'})
)

# %%
# Assigning 
roads_template = roads_template.merge(points_gdf,
                                      left_on = ['segment_id'],
                                      right_index=True,
                                      how = 'left')

# %%
roads_template.head()

# %%
roads_template.to_parquet(inputs_path / 'roads_template_old_grid_with_sF.parquet')


