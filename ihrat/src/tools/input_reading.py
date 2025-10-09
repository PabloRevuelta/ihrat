import geopandas as gpd
import os
from pathlib import Path
import csv

def reading_folder_files(folder_name,extensions):
    folder_path=Path.cwd().parent.parent.parent/'inputs'/folder_name
    #Search for all the files with the extension in the folder and add their local path to the list
    files = [file for file in folder_path.rglob('*') if file.is_file() and file.name.endswith(extensions)]
    #Create a dictionary with the name of the file in the folder as the key and the absolute path as value
    files_dic = {}
    for file in files:
        key = file.stem  # filename without extension
        files_dic[key] = file.resolve()
    return files_dic

def reading_files(folder,extensions):

    #Get the exposition maps folder path
    files_dic = reading_folder_files(folder, extensions)
    #Add the crs to the dic
    extended_dic={}
    for name, path in files_dic.items():
        if path.suffix=='.shp':
            extended_dic[name]={'path':path, 'crs':gpd.read_file(path).crs, 'extension':path.suffix}
        else:
            extended_dic[name] = {'path': path, 'extension': path.suffix}
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

def reading_shp_to_dic(folder):
    files_dic =reading_folder_files(folder, '.shp')
    key = list(files_dic.keys())[0]
    file=files_dic[key]
    return shp_to_dic(file,['subarea_fu','geometry']),file

def shp_to_dic(file,keys):
    #Export the .shp file into a geo data frame and then into a dictionary. The input key has to match the header
    #of one of the arguments in the shapefile
    geodataframe = gpd.read_file(file)
    crs=geodataframe.crs
    dic = geodataframe[keys].set_index(keys[0]).T.to_dict('dict')
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

