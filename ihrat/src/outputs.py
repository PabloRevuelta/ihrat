from pathlib import Path
import geopandas as gpd
import csv
from . import main_tool
import rasterio as ras

from . import dictionaries as dics


def shapefile_output(filename,dic,crs):
    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value

    namefile=filename+'.shp'
    path = Path.cwd().parent.parent / 'results/shps' / namefile

    #Transform dic of dics into dic of lists. Each list contains the values of a given key from all the subdics
    columns_dic = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    columns_dic[dics.keysdic['Elements ID']]=[]
    for key,row in dic.items():
        columns_dic[dics.keysdic['Elements ID']].append(key)
        for column, value in row.items():
            columns_dic[column].append(value)


    #Create a geodataframe from the dic of lists
    gdf = gpd.GeoDataFrame(columns_dic, geometry='geometry')
    gdf = gdf[[dics.keysdic['Elements ID'], dics.keysdic['Type of system'], dics.keysdic['Section identificator'],
               dics.keysdic['Exposed value'], dics.keysdic['Impact scenario'],dics.keysdic['Impact value'],
               dics.keysdic['Damage function'],dics.keysdic['Damage fraction'], dics.keysdic['Impact damage'],'geometry']]

    #Define the crs for the file
    gdf=gdf.set_crs(crs)

    #Save the gdf a shapefile
    gdf.to_file(path)

def csv_output(filename,dic):
    #Export the dictionary with the results of the risk analysis to a .csv file. Each entry is in a single row,
    #they keys are in the first, and the keys of the sub dictionaries are the headers.

    namefile = filename + '.csv'
    path = Path.cwd().parent.parent / 'results/csvs' / namefile

    fields = ['Elements ID', 'Type of system', 'Section identificator', 'Exposed value', 'Impact scenario',
              'Impact value', 'Damage function', 'Damage fraction', 'Impact damage']
    new_field_names = main_tool.output_fields_keys(fields,dic)

    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=new_field_names, delimiter=';')
        # Write the header row (field output headers)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            row= {new_field_names[0]: key}
            for i in range(1,len(new_field_names)):
                row[new_field_names[i]]=sub_dict[dics.keysdic[fields[i]]]
            writer.writerow(row)

def tif_output(filename, results,kwargs):
    namefile = filename + '.tif'
    path = Path.cwd().parent.parent / 'results/tifs' / namefile
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

def summary_output(imp_format,system_dic,summarydic):

    path = Path.cwd().parent.parent / 'results/csvs/results_summary.csv'

    if imp_format=='shapefile':
        fields = ['Exposed system', 'Type of system', 'Exposed value summary', 'Impact scenario', 'Damage function',
                  'Impact damage summary']
    elif imp_format=='raster':
        fields = ['Exposed system','Type of system','Exposed value summary', 'Impact scenario','Impact damage summary']
    new_field_names=main_tool.output_fields_keys(fields,system_dic)

    listofdics_to_csv(summarydic,fields,new_field_names,path)

def partial_agg_output(exp_format,system_dic,summarydic):

    path = Path.cwd().parent.parent / 'results/csvs/partial_agg_result.csv'


    if exp_format=='shapefile':
        fields = ['Exposed system', 'Type of system', 'Section identificator', 'Exposed value summary',
                  'Impact scenario', 'Damage function', 'Impact damage summary']
    elif exp_format=='raster':
        fields = ['Exposed system', 'Type of system', 'Section identificator', 'Exposed value summary',
                  'Impact scenario', 'Impact damage summary']
    new_field_names = main_tool.output_fields_keys(fields,system_dic)

    listofdics_to_csv(summarydic, fields, new_field_names, path)



