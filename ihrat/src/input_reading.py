import geopandas as gpd
import os
from pathlib import Path


def reading_folder_files(folder_name,extension):
    folder_path=Path.cwd().parent.parent/'inputs'/folder_name
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
    files_dic = reading_folder_files('expmaps', '.shp')
    #Add the crs to the dic
    extended_dic={}
    for name, path in files_dic.items():
        extended_dic[name]={'path':path, 'crs':gpd.read_file(path).crs}
    return extended_dic

def reading_tif_exp(): #Returns a dic with the abs path from all the .tif files in the expmaps folder

    #Get the exposition maps folder path
    filesdic = reading_folder_files('expmaps', '.tif')
    #Add the dic
    extended_dic={}
    for name, path in filesdic.items():
        extended_dic[name]={'path':path}
    return extended_dic

def shp_to_dic(file,key):
    #Export the .shp file into a geo data frame and then into a dictionary. The input key has to match the header
    #of one of the arguments in the shapefile
    geodataframe = gpd.read_file(file)
    dic = geodataframe.set_index(key).T.to_dict('dict')
    return dic