import geopandas as gpd
import rasterio as rst
import rasterio.plot as rstplot
import rasterstats as rsts
import matplotlib.pyplot as plt
import csv
import numpy as np
from pathlib import Path

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
def shp_to_dict(file):
    #Export the .shp file into a geo data frame and then into a dictionary
    geodataframe = gpd.read_file(file)
    dict = geodataframe.set_index('ID_PARCELA').T.to_dict('dict')
    return dict
def add_listofdics_to_dicofdics(dic,list):
    #Add to each entry of a dictionary of dictionaries the values stored in a list of dictionaries.
    #To each entry of the dictionary, add the corresponding dictionary from the list
    for i, j in zip(dic, list):
        dic[i].update(j)
def add_list_to_dicofdics(dic, list, subkey):
    # Add to each entry of a dictionary of dictionaries the values stored in a list.
    # To each entry of the dictionary, add the corresponding value from the list
    for (keydic, dicdic), value in zip(dic.items(), list):
        dicdic[subkey] = value
def add_dic_to_dicofdics(dicofdics,dic,key):
    # Add to each entry of a dictionary of dictionaries the values stored in a dictionary, with the same key.
    # To each entry of the dictionary od dictionaries, add the corresponding value from the dictionary
    for clave in dicofdics:
            dicofdics[clave][key] = dic[clave]
def product_columns_dic(dic,key1,key2):
    # Multiply two columns of a dic. Return a dictionary with the same keys and the products
    product_dic = {}
    for key, subdic in dic.items():
        product = subdic[key1] * subdic[key2]
        product_dic[key] = product
    return product_dic
def dictoddics_to_csv(dic,path):
    #Export the content of dictionary to a .csv file. Each entry is in a single row, they keys are in the first and
    #the keys of the sub dictionaries are the headers.
    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        fieldnames = set()
        for sub_dict in dic.values():
            fieldnames.update(sub_dict.keys())
        fieldnames = list(fieldnames)
        fieldnames.insert(0, 'Key')  # Include the 'Key' column if needed
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            # Add the outer key as a column if needed
            sub_dict['Key'] = key  # Optionally include the outer key as a column
            writer.writerow(sub_dict)
def main():

    #Get the exposition maps paths
    mapsexp=reading_shapefiles_exp()
    #De momento solo empezamos con uno, así que lo leemos y hacemos un diccionario con los valores (MODIFICAR)
    mapsexpdic=shp_to_dict(mapsexp[0])
    #Get the hazard maps
    mapshaz=reading_rasters_haz()

    #Plotear mapas
    """fig, ax = plt.subplots()
    ax = rstplot.show(maphaz,ax=ax,)
    mapexp.plot(ax=ax, color="orange")
    plt.show()"""

    #Obtain zonal stats for the hazard raster map into the exposition poligons
    zonal_stats= rsts.zonal_stats(str(mapsexp[0]),str(mapshaz[0]), stats=['count','mean','min', 'max'])
    #Add them to the dictionary of the exposed system
    add_listofdics_to_dicofdics(mapsexpdic, zonal_stats)

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores. (ESTO LO DEJAMOS ASÍ PORQUE
    #ES PROVISIONAL, YA QUE LUEGO HABRÁ QUE ELEGIR LAS FUNCIONES DE VULN DE UNA LISTA)
    damage_perc_list=[]
    for i in range(len(zonal_stats)):
        damage_perc_list.append(0.33*zonal_stats[i]["mean"])
    #Add the damage percentage to the dictionary of the exposed system
    add_list_to_dicofdics(mapsexpdic, damage_perc_list, "impact_perc")

    # Compute the economic impact, multiplying the damage percentage by the value of each building of the system.
    impact_value_dic=product_columns_dic(mapsexpdic,'impact_perc','Valor_Cata')
    #Add the value to the dictionary of the exposed system
    add_dic_to_dicofdics(mapsexpdic, impact_value_dic, 'impact_value_ind')

    #Export the dictionary of exposed systems to a .csv file
    path=Path.cwd().parent.parent / 'results/zonal_stats.csv'
    dictoddics_to_csv(mapsexpdic,path)

if __name__ == "__main__":
    main()