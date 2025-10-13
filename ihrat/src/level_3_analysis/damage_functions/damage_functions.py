import numpy as np
from pathlib import Path
import geopandas as gpd
from rasterio.features import geometry_mask
import json
from scipy.interpolate import LinearNDInterpolator

from ihrat.src.tools import dictionaries as dics


class FunctionLibrary:
    def __init__(self):
        json_path = "C:\\Users\\revueltaap\\UNICAN\\EMCAN 2024 A2 ADAPTA - Documentos\\02_Tareas\\Proyecto ihrat\\ihrat\\ihrat\\src\\level_3_analysis\\damage_functions\\damage_functions_dictionary.json"
        with open(json_path, "r") as f:
            self.data = json.load(f)
        # Índice por nombre → bloque de datos de la función
        self.index = {f["nombre"]: f for f in self.data["funciones"]}
        self.cache = {}

    def get(self, nombre):
        # Si ya está en caché, devuelve directamente
        if nombre in self.cache:
            return self.cache[nombre]

        # Si no, la crea y la guarda
        fdata = self.index[nombre]
        tipo = fdata["type"]

        if tipo == "interpolation":
            pts = np.column_stack([fdata[var] for var in fdata["variables"]])
            vals = np.array(fdata["values"])
            kind = fdata["interpolation_type"]
            f = LinearNDInterpolator(pts, vals)

        self.cache[nombre] = f
        return f

def apply_damage_fun_shp(system_dic):
    #Compute the damage fraction on the exposed value of a given element from the exposed system and add it to the dic

    indiv_element_dic = system_dic[list(system_dic.keys())[0]]
    haz_keys = [k for k in indiv_element_dic.keys() if k not in [dics.keysdic['Damage function'],
                                                                 dics.keysdic['Exposed value'],
                                                                 dics.keysdic['Type of system'],
                                                                 dics.keysdic['Impact scenario'],'geometry']]
    lib = FunctionLibrary()

    for indiv_element_dic in system_dic.values():
        f_name=indiv_element_dic[dics.keysdic['Damage function']]
        input_values=[indiv_element_dic[key] for key in haz_keys]
        f=lib.get(f_name)
        indiv_element_dic[dics.keysdic['Damage fraction']]=round(float(f(*input_values)),3)

def apply_dam_fun_raster(raster_scen_data_list,combined_mask,dm_fun):

    lib = FunctionLibrary()
    f = lib.get(dm_fun)

    # 3️⃣ Crear un array de salida vacío (mismo shape que el primer raster)
    raster_scen_data = np.full_like(raster_scen_data_list[0], np.nan, dtype=np.float32)

    raster_scen_data[combined_mask] = f(*[r[combined_mask] for r in raster_scen_data_list])

    return raster_scen_data

def apply_dam_fun_file(raster_scen_data_list,combined_mask,dm_fun_file,kwargs):
    lib = FunctionLibrary()

    dm_fun_file_path=Path.cwd().parent.parent/'inputs'/'dam_fun_files'/dm_fun_file+'.shp'
    gdf = gpd.read_file(dm_fun_file_path)

    # 3️⃣ Crear un array de salida vacío (mismo shape que el primer raster)
    raster_scen_data = np.full_like(raster_scen_data_list[0], np.nan, dtype=np.float32)

    for index, row in gdf.iterrows():
        geom = row.geometry
        mask = geometry_mask([geom], transform=kwargs['transform'], invert=True,
                             out_shape=raster_scen_data.shape)
        mask = combined_mask & mask

        dm_fun_name = row['DAM_FUN']
        f = lib.get(dm_fun_name)

        raster_scen_data[mask] = f(*[r[mask] for r in raster_scen_data_list])

    return raster_scen_data