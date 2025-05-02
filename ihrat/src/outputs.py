from pathlib import Path
import geopandas as gpd
import csv
import main
import rasterio as ras


def shapefile_output(filename,dic,keysdic,crs):
    #Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value

    namefile=filename+'.shp'
    path = Path.cwd().parent.parent / 'results/shps' / namefile

    #Transform dic of dics into dic of lists. Each list contains the values of a given key from all the subdics
    columnsdic = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    columnsdic[keysdic['Elements ID']]=[]
    for key,row in dic.items():
        columnsdic[keysdic['Elements ID']].append(key)
        for column, value in row.items():
            columnsdic[column].append(value)


    #Create a geodataframe from the dic of lists
    gdf = gpd.GeoDataFrame(columnsdic, geometry='geometry')
    gdf = gdf[[keysdic['Elements ID'], keysdic['Type of system'], keysdic['Section identificator'],
               keysdic['Exposed value'], keysdic['Hazard scenario'],keysdic['Impact value'], keysdic['Damage function'],
               keysdic['Damage fraction'], keysdic['Impact damage'],'geometry']]

    #Define the crs for the file
    gdf=gdf.set_crs(crs)

    #Save the gdf a shapefile
    gdf.to_file(path)

def csv_output(filename,dic,keysdic,keysoutputdic):
    #Export the dictionary with the results of the risk analysis to a .csv file. Each entry is in a single row,
    #they keys are in the first and the keys of the sub dictionaries are the headers.

    namefile = filename + '.csv'
    path = Path.cwd().parent.parent / 'results/csvs' / namefile

    fields = ['Elements ID', 'Type of system', 'Section identificator', 'Exposed value', 'Hazard scenario',
              'Impact value', 'Damage function', 'Damage fraction', 'Impact damage']
    newfieldnames = main.output_fields_keys(dic,fields,keysdic,keysoutputdic)

    with open(path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=newfieldnames, delimiter=';')
        # Write the header row (field output headers)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            row={}
            row[newfieldnames[0]] = key
            for i in range(1,len(newfieldnames)):
                row[newfieldnames[i]]=sub_dict[keysdic[fields[i]]]
            writer.writerow(row)

def tif_output(filename, results,kwargs):
    namefile = filename + '.tif'
    path = Path.cwd().parent.parent / 'results/tifs' / namefile
    with ras.open(path, 'w', **kwargs) as output:
        output.write(results, 1)

def listofddics_to_csv(list,fields,newfieldnames,path,keysdic):
    #Export the content of a list of dictionaries to a .csv file. Each entry is in a single row.

    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        writer = csv.DictWriter(file, fieldnames=newfieldnames,delimiter=';')
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        """writer.writerows(list)"""

        for dic in list:
            row = {}
            for i in range(len(newfieldnames)):
                row[newfieldnames[i]] = dic[keysdic[fields[i]]]
            writer.writerow(row)

def summary_sr_output(system_dic,summarydic,keysdic,keysoutputdic):

    path = Path.cwd().parent.parent / 'results/csvs/results_summary.csv'

    fields = ['Exposed system','Type of system','Exposed value', 'Hazard scenario','Impact damage']
    newfieldnames=main.output_fields_keys(system_dic,fields,keysdic,keysoutputdic)

    listofddics_to_csv(summarydic,fields,newfieldnames,path,keysdic)

def partial_agg_output(system_dic,summarydic,keysdic,keysoutputdic):

    path = Path.cwd().parent.parent / 'results/csvs/partial_agg_result.csv'

    fields = ['Exposed system', 'Type of system', 'Section identificator','Exposed value', 'Hazard scenario',
              'Impact damage']
    newfieldnames = main.output_fields_keys(system_dic, fields, keysdic, keysoutputdic)

    listofddics_to_csv(summarydic, fields, newfieldnames, path, keysdic)

def summary_rr_output(expsystdic,summarydic,keysdic,keysoutputdic):

    path = Path.cwd().parent.parent / 'results/csvs/results_summary.csv'

    fields = ['Exposed system','Type of system','Exposed value','Hazard scenario','Damage function','Impact damage']
    fieldkeys = []
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            fieldkeys.append(field)
        else:
            fieldkeys.append(keysoutputdic[field])
    listofddics_to_csv(summarydic,fields,fieldkeys,path,keysdic)



