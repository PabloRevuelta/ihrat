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

def main():

    #Get the exposition maps paths
    mapsexp=reading_shapefiles_exp()
    #De momento solo empezamos con uno, así que lo leemos y hacemos un diccionario con los valores de las columnas
    # que nos interesen (MODIFICAR). #Introducir/seleccionar los nombres de las columnas de datos de los atributos
    # del shpfile sobre los que se va a hacer el análisis de daños. De momento, los pondermos a mano (MODIFICAR).
    # También seleccionamos los nombres que queremos darles a las entradas
    keystokeep=['Valor_Cata']
    keys=['Exposed value (€)']
    expsystdic=ldfun.expshp_to_dic(mapsexp['test_chiqui_WS84']['path'],keystokeep,keys)
    #Get the hazard maps
    mapshaz=reading_rasters_haz()
    #Add the hazard scenario to the dictionary. EN EL FUTURO, LO HAREMOS CON LOS DISTINTOS ESCENARIOS

    ldfun.add_value_to_dicofidcs(expsystdic, 'Hazard scenario', 'flood_2100_tr500_chiqui')



    #Plotear mapas
    """fig, ax = plt.subplots()
    ax = rstplot.show(maphaz,ax=ax,)
    mapexp.plot(ax=ax, color="orange")
    plt.show()"""

    #Obtain zonal stats for the hazard raster map into the exposition poligons
    zonal_stats= rsts.zonal_stats(str(mapsexp['test_chiqui_WS84']['path']),str(mapshaz['flood_2100_tr500_chiqui']), stats=['mean'])
    #Add them to the dictionary of the exposed system
    ldfun.add_listofdics_to_dicofdics(expsystdic, zonal_stats,['Impact value (m)'])

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores. (ESTO LO DEJAMOS ASÍ PORQUE
    #ES PROVISIONAL, YA QUE LUEGO HABRÁ QUE ELEGIR LAS FUNCIONES DE VULN DE UNA LISTA)
    damage_perc_list=[]
    for i in range(len(zonal_stats)):
        damage_perc_list.append(0.33*zonal_stats[i]['mean'])
    #Add the damage percentage to the dictionary of the exposed system
    ldfun.add_list_to_dicofdics(expsystdic, damage_perc_list, 'Damage fraction')

    # Compute the economic impact, multiplying the damage percentage by the value of each building of the system.
    impact_value_dic=ldfun.product_columns_dic(expsystdic,'Damage fraction','Exposed value (€)')
    #Add the value to the dictionary of the exposed system
    ldfun.add_dic_to_dicofdics(expsystdic, impact_value_dic, 'Consequences value (€)')

    #Export the dictionary of exposed systems to a .csv file. FALTA ORDEN DE LA TABLA
    path=Path.cwd().parent.parent / 'results/zonal_stats.csv'
    ldfun.dictoddics_to_csv(expsystdic,path)

    #Add the values to the summary table
    summarydic={}
    summarydic['Exposed value (€)']=ldfun.column_sum(expsystdic, 'Exposed value (€)')
    summarydic['Hazard scenario']='flood_2100_tr500_chiqui'
    summarydic['Consequences value (€)']=ldfun.column_sum(expsystdic, 'Consequences value (€)')

    #Export them to a .csv file.  FALTA ORDEN DE LA TABLA
    path = Path.cwd().parent.parent / 'results/zonal_stats_summary.csv'
    ldfun.dic_to_csv(summarydic, path)

    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value
    path = Path.cwd().parent.parent / 'results/risk_analysis_1.shp'
    ldfun.dic_to_shp(expsystdic,path,mapsexp['test_chiqui_WS84']['crs'])

if __name__ == "__main__":
    main()