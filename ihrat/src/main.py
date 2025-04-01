import geopandas as gpd
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
    expfolderpath=Path.cwd().parent.parent / 'expmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in expfolderpath.rglob('*.shp') if file.is_file()]
    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return files
def reading_rasters_haz(): #Returns a list with the path from all the .shp files in the expmaps folder
    #Get the exposition maps folder path
    expfolderpath=Path.cwd().parent.parent / 'hazmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in expfolderpath.rglob('*.tif') if file.is_file()]
    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return files

def main():

    #Get the exposition maps paths
    mapsexp=reading_shapefiles_exp()
    #De momento solo empezamos con uno, así que lo leemos y hacemos un diccionario con los valores de las columnas
    # que nos interesen (MODIFICAR). #Introducir/seleccionar los nombres de las columnas de datos de los atributos
    # del shpfile sobre los que se va a hacer el análisis de daños. De momento, los pondermos a mano (MODIFICAR).
    # También seleccionamos los nombres que queremos darles a las entradas
    keystokeep=['Valor_Cata']
    keys=['Exposed value (€)']
    mapsexpdic=ldfun.expshp_to_dic(mapsexp[0],keystokeep,keys)
    #Get the hazard maps
    mapshaz=reading_rasters_haz()



    #Plotear mapas
    """fig, ax = plt.subplots()
    ax = rstplot.show(maphaz,ax=ax,)
    mapexp.plot(ax=ax, color="orange")
    plt.show()"""

    #Obtain zonal stats for the hazard raster map into the exposition poligons
    zonal_stats= rsts.zonal_stats(str(mapsexp[0]),str(mapshaz[0]), stats=['mean'])
    #Add them to the dictionary of the exposed system
    ldfun.add_listofdics_to_dicofdics(mapsexpdic, zonal_stats,['Impact value (m)'])

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores. (ESTO LO DEJAMOS ASÍ PORQUE
    #ES PROVISIONAL, YA QUE LUEGO HABRÁ QUE ELEGIR LAS FUNCIONES DE VULN DE UNA LISTA)
    damage_perc_list=[]
    for i in range(len(zonal_stats)):
        damage_perc_list.append(0.33*zonal_stats[i]['mean'])
    #Add the damage percentage to the dictionary of the exposed system
    ldfun.add_list_to_dicofdics(mapsexpdic, damage_perc_list, 'Damage fraction')

    # Compute the economic impact, multiplying the damage percentage by the value of each building of the system.
    impact_value_dic=ldfun.product_columns_dic(mapsexpdic,'Damage fraction','Exposed value (€)')
    #Add the value to the dictionary of the exposed system
    ldfun.add_dic_to_dicofdics(mapsexpdic, impact_value_dic, 'Consequences value (€)')

    #Export the dictionary of exposed systems to a .csv file. FALTA ORDEN DE LA TABLA Y CAMPO DEL ESCENARIO
    path=Path.cwd().parent.parent / 'results/zonal_stats.csv'
    ldfun.dictoddics_to_csv(mapsexpdic,path)

if __name__ == "__main__":
    main()