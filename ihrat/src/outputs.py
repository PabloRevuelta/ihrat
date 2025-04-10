from pathlib import Path
import geopandas as gpd
import csv

def shapefile_output(filename,dic,keysdic,crs):
    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value

    namefile_shp=filename+'.shp'
    path = Path.cwd().parent.parent / 'results/shps' / namefile_shp

    #Transform dic of dics into dic of lists. Each list contains the values of a given key from all the subdics
    columnsdic = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    columnsdic[keysdic['Elements ID']]=[]
    for key,row in dic.items():
        columnsdic[keysdic['Elements ID']].append(key)
        for column, value in row.items():
            columnsdic[column].append(value)


    #Create a geodataframe from the dic of lists
    gdf = gpd.GeoDataFrame(columnsdic, geometry='geometry')
    gdf = gdf[[keysdic['Elements ID'], keysdic['Type of system'], keysdic['Exposed value'], keysdic['Hazard scenario'],
               keysdic['Impact value'], keysdic['Damage function'], keysdic['Damage fraction'], keysdic['Impact damage'],
               'geometry']]

    #Define the crs for the file
    gdf=gdf.set_crs(crs)

    #Save the gdf a shapefile
    gdf.to_file(path)

def csv_output(filename,dic,keysdic):
    #Export the dictionary with the results of the risk analysis to a .csv file. Each entry is in a single row,
    #they keys are in the first and the keys of the sub dictionaries are the headers.

    namefile_csv = filename + '.csv'
    path = Path.cwd().parent.parent / 'results/csvs' / namefile_csv

    with open(path, mode='w', newline='') as file:
        fieldnames = [keysdic['Elements ID'], keysdic['Type of system'], keysdic['Exposed value'],
                      keysdic['Hazard scenario'], keysdic['Impact value'], keysdic['Damage function'],
                      keysdic['Damage fraction'], keysdic['Impact damage']]
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            row = {col: sub_dict.get(col, '') for col in fieldnames}
            row[keysdic['Elements ID']] = key
            writer.writerow(row)

def listofddics_to_csv(list,path):
    #Export the content of a list of dictionaries to a .csv file. Each entry is in a single row. (ORDENAR FALTA)
    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        fieldnames=list[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames,delimiter=';')
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        writer.writerows(list)