import numpy as np
from pathlib import Path
import geopandas as gpd
from rasterio.features import geometry_mask

import dictionaries as dics

def apply_damage_fun_shp(indiv_element_dic):
    #Compute the damage fraction on the exposed value of a given element from the exposed system and add it to the dic

    dam_fun=globals().get(indiv_element_dic[dics.keysdic['Damage function']])
    indiv_element_dic[dics.keysdic['Damage fraction']]=round(dam_fun(indiv_element_dic[dics.keysdic['Impact value']]), 3)

def apply_dam_fun_raster(raster_scen_data,mask_scen,dm_fun):
    dam_fun = globals().get(dm_fun)
    dam_fun_vec=np.vectorize(dam_fun)
    raster_scen_data[mask_scen] = dam_fun_vec(raster_scen_data[mask_scen])

    return raster_scen_data

def apply_dam_fun_file(raster_scen_data,mask_scen,dm_fun_file,kwargs):

    dm_fun_file_path=Path.cwd().parent.parent/'inputs'/'partial_agg_map'/dm_fun_file+'.shp'

    gdf = gpd.read_file(dm_fun_file_path)

    for index, row in gdf.iterrows():
        geom = row.geometry
        mask = geometry_mask([geom], transform=kwargs['transform'], invert=True,
                             out_shape=raster_scen_data.shape)
        mask_comb = mask_scen & mask

        dam_fun = globals().get(gdf.loc[index,'DAM_FUN'])
        dam_fun_vec = np.vectorize(dam_fun)

        raster_scen_data[mask] = dam_fun_vec(raster_scen_data[mask_comb])

    return raster_scen_data

def pop_A(imp_val):
    if imp_val<0.3:
        return 0
    else:
        return 1

def pop_B(imp_val):
    if imp_val < 0.5:
        return 0
    else:
        return 1

def build_A(imp_val):
    if imp_val > 3:
        return 1
    else:
        return 0.33*imp_val

def build_B(imp_val):
    if imp_val > 6:
        return 1
    else:
        return 0.17*imp_val

def build_C(imp_val):
    if imp_val > 9:
        return 1
    else:
        return 0.11*imp_val