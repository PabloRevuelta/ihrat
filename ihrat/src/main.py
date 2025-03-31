import geopandas as gpd
import rasterio as rst
import rasterio.plot as rstplot
import rasterstats as rsts
import matplotlib.pyplot as plt
import csv
import numpy as np



def main():

    # Introducir mapas de exposición y peligrosidad
    #Read the exposure file and transform it into a geodataframe
    mapexp=gpd.read_file("C:\\Users\\revueltaap\\PycharmProjects\\ihrat\\expmaps\\test_chiqui_WS84.shp")
    #Convertir gdf into dictonary
    mapexpdic=mapexp.set_index('ID_PARCELA').T.to_dict('dict') #cuidado, me cambia los ordenes de las columnas
    #Read the hazard map and transform it into a dataset
    maphaz=rst.open("C:\\Users\\revueltaap\\PycharmProjects\\ihrat\\hazmaps\\flood_2100_tr500_chiqui.tif")


    #Check crs de los dos archivos. Si alguno da error, no utilizar y marcar


    #Plotear mapas
    """fig, ax = plt.subplots()
    ax = rstplot.show(maphaz,ax=ax,)
    mapexp.plot(ax=ax, color="orange")
    plt.show()"""

    #Zonal stats
    #Para ello Read the raster values and get the affine
    #array = maphaz.read(1)
    #affine = maphaz.transform
    #Calculamos zonal stats
    zonal_stats= rsts.zonal_stats("C:\\Users\\revueltaap\\PycharmProjects\\ihrat\\expmaps\\test_chiqui_WS84.shp","C:\\Users\\revueltaap\\PycharmProjects\\ihrat\\hazmaps\\flood_2100_tr500_chiqui.tif", stats=['count','mean','min', 'max'])
    #Añadimos al diccionario del mapa de exp
    for i, j in zip(mapexpdic, zonal_stats):
        mapexpdic[i].update(j) #añade las columnas donde cuadra

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores
    impact_perc=[]
    for i in range(len(zonal_stats)):
        impact_perc.append(0.33*zonal_stats[i]["mean"])
    #Añadimos al diccionario
    for (clave, diccionario), valor in zip(mapexpdic.items(), impact_perc):
        diccionario['impact_perc'] = valor

    #Calculamos el impacto económico, multiplicando el porcentaje de impacto por el valor catastral
    impact_value_ind = {}
    for clave, subdiccionario in mapexpdic.items():
        multiplicacion = subdiccionario['impact_perc'] * subdiccionario['Valor_Cata']
        impact_value_ind[clave] = multiplicacion
    #Añadimos al diccionario
    for clave in mapexpdic:
            mapexpdic[clave]['impact_value_ind'] = impact_value_ind[clave]

    #Pasamos el diccionario a un csv
    # Open the CSV file in write mode
    with open("zonal_stats.csv", mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        fieldnames = set()
        for sub_dict in mapexpdic.values():
            fieldnames.update(sub_dict.keys())
        fieldnames = list(fieldnames)
        fieldnames.insert(0, 'Key')  # Include the 'Key' column if needed
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in mapexpdic.items():
            # Add the outer key as a column if needed
            sub_dict['Key'] = key  # Optionally include the outer key as a column
            writer.writerow(sub_dict)



if __name__ == "__main__":
    main()