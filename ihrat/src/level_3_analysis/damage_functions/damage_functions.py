import numpy as np
from pathlib import Path
import geopandas as gpd
from rasterio.features import geometry_mask

from ihrat.src.tools import dictionaries as dics
from . import damage_functions_dic as dam_fun_dic

def apply_damage_fun_shp(indiv_element_dic):
    #Compute the damage fraction on the exposed value of a given element from the exposed system and add it to the dic
    haz_keys = [k for k in indiv_element_dic.keys() if k not in [dics.keysdic['Damage function'],
                                                                 dics.keysdic['Exposed value'],
                                                                 dics.keysdic['Type of system'],
                                                                 dics.keysdic['Impact scenario'],'geometry']]
    dam_fun = getattr(dam_fun_dic, indiv_element_dic[dics.keysdic['Damage function']], None)
    indiv_element_dic[dics.keysdic['Damage fraction']]=round(dam_fun([indiv_element_dic[key] for key in haz_keys]), 3)

def apply_dam_fun_raster(raster_scen_data_list,combined_mask,dm_fun):
    dam_fun = getattr(dam_fun_dic, dm_fun)
    dam_fun_vec=np.vectorize(dam_fun)

    # 3️⃣ Crear un array de salida vacío (mismo shape que el primer raster)
    raster_scen_data = np.full_like(raster_scen_data_list[0], np.nan, dtype=np.float32)

    raster_scen_data[combined_mask] = dam_fun_vec(*[r[combined_mask] for r in raster_scen_data_list])

    return raster_scen_data

def apply_dam_fun_file(raster_scen_data_list,combined_mask,dm_fun_file,kwargs):

    dm_fun_file_path=Path.cwd().parent.parent/'inputs'/'dam_fun_files'/dm_fun_file+'.shp'
    gdf = gpd.read_file(dm_fun_file_path)

    # 3️⃣ Crear un array de salida vacío (mismo shape que el primer raster)
    raster_scen_data = np.full_like(raster_scen_data_list[0], np.nan, dtype=np.float32)

    for index, row in gdf.iterrows():
        geom = row.geometry
        mask = geometry_mask([geom], transform=kwargs['transform'], invert=True,
                             out_shape=raster_scen_data.shape)
        mask = combined_mask & mask

        dam_fun = globals().get(gdf.loc[index,'DAM_FUN'])
        dam_fun_vec = np.vectorize(dam_fun)

        raster_scen_data[mask] = dam_fun_vec(*[r[mask] for r in raster_scen_data_list])

    return raster_scen_data