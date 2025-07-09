import geopandas as gpd
import os
from pathlib import Path
import csv


def reading_folder_files(folder_name,extension):
    folder_path=Path.cwd().parent.parent.parent/'inputs'/folder_name
    #Search for all the files with the extension in the folder and add their local path to the list
    files = [file for file in folder_path.rglob('*'+extension) if file.is_file()]
    #Create a dictionary with the name of the file in the folder as the key and the absolute path as value
    files_dic = {}
    for file in files:
        files_dic[os.path.splitext(os.path.relpath(file, folder_path))[0]] = file
    return files_dic

def reading_shapefiles_exp():
    #Returns a dic with the abs path and crs from all the .shp files in the expmaps folder

    #Get the exposition maps folder path
    files_dic = reading_folder_files('exp_input_data', '.shp')
    #Add the crs to the dic
    extended_dic={}
    for name, path in files_dic.items():
        extended_dic[name]={'path':path, 'crs':gpd.read_file(path).crs, 'extension':'.shp'}
    return extended_dic

def reading_tif_exp(): #Returns a dic with the abs path from all the .tif files in the expmaps folder

    #Get the exposition maps folder path
    filesdic = reading_folder_files('exp_input_data', '.tif')
    #Add the dic
    extended_dic={}
    for name, path in filesdic.items():
        extended_dic[name]={'path':path,'extension':'.tif'}
    return extended_dic

def reading_input(folder,extension):
    files_dic =reading_folder_files(folder, extension)
    key = list(files_dic.keys())[0]
    file_path = files_dic[key]
    if extension=='.csv':
        return key, csv_to_dic(file_path)
    elif extension=='.shp':
        return key, shp_to_dic(file_path,key)
    return None

def reading_shp_to_gdf(folder):
    files_dic =reading_folder_files(folder, '.shp')
    key = list(files_dic.keys())[0]
    return gpd.read_file(files_dic[key])

def shp_to_dic(file,key):
    #Export the .shp file into a geo data frame and then into a dictionary. The input key has to match the header
    #of one of the arguments in the shapefile
    geodataframe = gpd.read_file(file)
    crs=geodataframe.crs
    dic = geodataframe.set_index(key).T.to_dict('dict')
    return dic,crs

def csv_to_dic(file):
    main_dic = {}
    with open(file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = row[reader.fieldnames[0]]  # Use the first column as the key
            # Remove the key from the value dictionary
            value = {k: v for k, v in row.items() if k != reader.fieldnames[0]}
            main_dic[key] = value
    return main_dic

