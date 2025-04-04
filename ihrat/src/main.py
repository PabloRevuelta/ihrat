import geopandas as gpd
import os
import rasterio as rst
import rasterio.plot as rstplot
import rasterstats as rsts
import matplotlib.pyplot as plt
import csv
import numpy as np
from pathlib import Path
import list_dics_functions as ldfun

def reading_shapefiles_exp(): #Returns a list with the path from all the .shp files in the expmaps folder
    #Get the exposition maps folder path
    folderpath=Path.cwd().parent.parent / 'expmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in folderpath.rglob('*.shp') if file.is_file()]
    filesdic={}
    for file in files:
        filesdic[os.path.splitext(os.path.relpath(file, folderpath))[0]]={'path':file,'crs':gpd.read_file(file).crs}

    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return filesdic
def reading_rasters_haz(): #Returns a list with the path from all the .shp files in the expmaps folder
    #Get the exposition maps folder path
    folderpath=Path.cwd().parent.parent / 'hazmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in folderpath.rglob('*.tif') if file.is_file()]
    filesdic = {}
    for file in files:
        filesdic[os.path.splitext(os.path.relpath(file, folderpath))[0]] = file
    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return filesdic

def scen_compute(expname,expdic,dicexp,scen,pathscen):

    #Create new dic for this scenario with the exposure data
    scendic=dicexp
    #Add the hazard scenario
    ldfun.add_value_to_dicofidcs(scendic, 'Hazard scenario', 'flood_2100_tr500_chiqui')

    #Obtain zonal stats for the hazard raster map into the exposition polygons and add them to the dic. We change the
    #None values by 0.
    zonal_stats = rsts.zonal_stats(str(expdic['path']),str(pathscen),stats=['mean'])
    for item in zonal_stats:
        if item['mean']==None:
            item['mean']=0
    ldfun.add_listofdics_to_dicofdics(scendic, zonal_stats, ['Impact value (m)'])

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores. (ESTO LO DEJAMOS ASÍ PORQUE
    #ES PROVISIONAL, YA QUE LUEGO HABRÁ QUE ELEGIR LAS FUNCIONES DE VULN DE UNA LISTA). Lo añadimos al diccionario
    damage_perc_list = []
    for i in range(len(zonal_stats)):
        damage_perc_list.append(0.33 * zonal_stats[i]['mean'])
    # Add the damage percentage to the dictionary of the exposed system
    ldfun.add_list_to_dicofdics(scendic, damage_perc_list, 'Damage fraction')

    # Compute the economic impact, multiplying the damage percentage by the value of each building of the system.
    impact_value_dic = ldfun.product_columns_dic(scendic, 'Damage fraction', 'Exposed value (€)')
    # Add the value to the dictionary of the exposed system
    ldfun.add_dic_to_dicofdics(scendic, impact_value_dic, 'Consequences value (€)')

    # Export the dictionary of exposed systems to a .csv file. FALTA ORDEN DE LA TABLA
    namefile_csv=expname+scen+'.csv'
    path = Path.cwd().parent.parent / 'results/csvs'/namefile_csv
    ldfun.dicofddics_to_csv(scendic, path)

    # Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value
    namefile_shp=expname+scen+'.shp'
    path = Path.cwd().parent.parent / 'results/shps' / namefile_shp
    ldfun.dic_to_shp(scendic, path, expdic['crs'])

    return {'Exposed value (€)':ldfun.column_sum(scendic, 'Exposed value (€)'),\
                  'Consequences value (€)':ldfun.column_sum(scendic, 'Consequences value (€)')}

def main():

    #Get the exposition maps paths from the expmaps folder and create the exposed system dic. We need the attribute keys
    #of the wanted attributes from the shapefile and the keys we want to use in the outputs.
    #AHORA SOLO TENEMOS UNO, HACEMOS COSAS A MANO (MODFICAR EN FUTURO)
    mapsexp=reading_shapefiles_exp()
    keystokeep=['edif_ID','valor_es_1']
    keys=['Exposed value (€)']
    expsystdic=ldfun.expshp_to_dic(mapsexp['manga_exposicion']['path'],keystokeep,keys)


    #Get the hazard scenarios maps paths from the hazmaps folder
    allscendic=reading_rasters_haz()

    #Create dic for the summary table
    summarydic = {}
    #Compute the risk analysys for all hazard scenarios and export the results to .csv files. Also add the aggregate
    #results to the summary dic
    for scen in allscendic.keys():
     scensum=scen_compute('manga_exposicion',mapsexp['manga_exposicion'], expsystdic, scen, allscendic[scen])
     summarydic[scen]=scensum

    #Export them to a .csv file.  FALTA ORDEN DE LA TABLA
    path = Path.cwd().parent.parent / 'results/csvs/manga_exposicion_summary.csv'
    ldfun.dicofddics_to_csv(summarydic, path)


if __name__ == "__main__":
    main()