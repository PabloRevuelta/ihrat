from pathlib import Path
import geopandas as gpd
import csv
import rasterio as ras

from . import dictionaries as dics
from . import input_reading
from ihrat.src.level_3_analysis import level_3_analysis


def shapefile_output(filename,dic,crs,partial_agg_flag):
    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value

    namefile=filename+'.shp'
    path = Path.cwd().parent.parent.parent / 'results/shps' / namefile

    #Transform dic of dics into dic of lists. Each list contains the values of a given key from all the subdics
    columns_dic = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    columns_dic[dics.keysdic['Elements ID']]=[]
    for key,row in dic.items():
        columns_dic[dics.keysdic['Elements ID']].append(key)
        for column, value in row.items():
            columns_dic[column].append(value)


    #Create a geodataframe from the dic of lists
    gdf = gpd.GeoDataFrame(columns_dic, geometry='geometry')

    keys_list=[dics.keysdic['Elements ID'], dics.keysdic['Type of system'],
               dics.keysdic['Exposed value'], dics.keysdic['Impact scenario'],
               dics.keysdic['Damage function'],dics.keysdic['Damage fraction'], dics.keysdic['Impact damage'],'geometry']

    haz_keys = [k for k in next(iter(dic.values())).keys() if k not in keys_list]

    keys_list[4:4] = haz_keys

    gdf = gdf[keys_list]

    #Define the crs for the file
    gdf=gdf.set_crs(crs)

    #Save the gdf a shapefile
    gdf.to_file(path)

    if partial_agg_flag:
        # --- 1. Cargar las zonas desde el shapefile ---
        partial_agg_map_path = input_reading.reading_folder_files('spatial_distribution_input', '.shp')
        key = list(partial_agg_map_path.keys())[0]
        partial_agg_map_path = partial_agg_map_path[key]
        zones = gpd.read_file(partial_agg_map_path)

        # Asegúrate de que el CRS de las zonas sea compatible con tus polígonos
        # (por ejemplo, EPSG:4326 o el que uses)
        zones = zones.to_crs(crs)

        # --- 4. Hacer el cruce espacial (spatial join) ---
        joined = gpd.sjoin(gdf, zones, how="left", predicate="within")

        # --- 5. Añadir el nombre de zona a cada subdiccionario ---
        column=dics.keysdic["Section identificator"]
        for key, row in joined.iterrows():
            dic[row.get(dics.keysdic['Elements ID'])][column] = row.get(column)

def csv_output(filename,fields,new_field_names,dic):
    #Export the dictionary with the results of the risk analysis to a .csv file. Each entry is in a single row,
    #they keys are in the first, and the keys of the sub dictionaries are the headers.

    namefile = filename + '.csv'
    path = Path.cwd().parent.parent.parent / 'results/csvs' / namefile

    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=new_field_names, delimiter=';')
        # Write the header row (field output headers)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            row= {new_field_names[0]: key}
            for i in range(1,len(new_field_names)):
                if (new_field_names[i] in dics.keysoutputdic.values()
                or new_field_names[i] in dics.keysoutputdic['Exposed value'].values()
                or new_field_names[i] in dics.keysoutputdic['Impact damage'].values()):
                    row[new_field_names[i]]=sub_dict[dics.keysdic[fields[i]]]
                else:
                    row[new_field_names[i]] = sub_dict[fields[i]]
            writer.writerow(row)

def tif_output(filename, results,kwargs):
    namefile = filename + '.tif'
    path = Path.cwd().parent.parent.parent / 'results/tifs' / namefile
    with ras.open(path, 'w', **kwargs) as output:
        output.write(results, 1)

def listofdics_to_csv(listofdics,fields,new_field_names,path):
    #Export the content of a list of dictionaries to a .csv file. Each entry is in a single row.

    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        writer = csv.DictWriter(file, fieldnames=new_field_names,delimiter=';')
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        """writer.writerows(list)"""

        for dic in listofdics:
            row = {}
            for i in range(len(new_field_names)):
                row[new_field_names[i]] = dic[dics.keysdic[fields[i]]]
            writer.writerow(row)

def summary_output(summarydic):

    path = Path.cwd().parent.parent.parent / 'results/csvs/results_summary.csv'

    fields = ['Exposed system', 'Type of system', 'Exposed value summary', 'Impact scenario',
              'Impact damage summary']
    new_field_names=level_3_analysis.output_fields_keys(fields,summarydic)

    listofdics_to_csv(summarydic,fields,new_field_names,path)

def partial_agg_output(partialaggdic):

    path = Path.cwd().parent.parent.parent / 'results/csvs/partial_agg_result.csv'

    fields = ['Exposed system', 'Type of system', 'Section identificator', 'Exposed value summary',
              'Impact scenario', 'Impact damage summary']
    new_field_names = level_3_analysis.output_fields_keys(fields,partialaggdic)

    listofdics_to_csv(partialaggdic, fields, new_field_names, path)

def simple_csv_output(filename,geo_data_polygon_id_field,dic):
    #Export the dictionary with the results of the risk analysis to a .csv file. Each entry is in a single row,
    #they keys are in the first, and the keys of the sub dictionaries are the headers.

    namefile = filename + '.csv'
    path = Path.cwd().parent.parent.parent / 'results/csvs' / namefile
    headers = list(next(iter(dic.values())).keys())
    headers.remove('geometry')
    headers = [geo_data_polygon_id_field] + headers

    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter=';')
        # Write the header row (field output headers)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            row = {geo_data_polygon_id_field: key, **sub_dict}
            row = {k: row.get(k, "") for k in headers}
            writer.writerow(row)

def simple_shapefile_output(filename,geo_data_polygon_id_field,dic,crs):
    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value

    namefile=filename+'.shp'
    path = Path.cwd().parent.parent.parent / 'results/shps' / namefile

    #Transform dic of dics into dic of lists. Each list contains the values of a given key from all the subdics
    columns_dic = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    columns_dic[geo_data_polygon_id_field]=[]
    for key,row in dic.items():
        columns_dic[geo_data_polygon_id_field].append(key)
        for column, value in row.items():
            columns_dic[column].append(value)

    #Create a geodataframe from the dic of lists
    gdf = gpd.GeoDataFrame(columns_dic, geometry='geometry')

    #Define the crs for the file
    gdf=gdf.set_crs(crs)

    #Save the gdf a shapefile
    gdf.to_file(path)

