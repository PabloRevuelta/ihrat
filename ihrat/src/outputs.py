from pathlib import Path
import geopandas as gpd
import csv
import list_dics_functions as ldfun


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

    namefile = filename + '.csv'
    path = Path.cwd().parent.parent / 'results/csvs' / namefile

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
    #Export the content of a list of dictionaries to a .csv file. Each entry is in a single row.
    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        fieldnames=list[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames,delimiter=';')
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        writer.writerows(list)

def partial_csv_output(filename,dic,keysdic,scensum):

    #Create the dic for the data partial aggregation
    partial_dic={}
    #Go through the result dic and aggregate the results in the different entries of the partial dic taking into account
    #the different values of the Section indicator.
    for value in dic.values():

        sec_ind=value[keysdic['Section indentificator']]
        #If there's still no entry in the partial dic for the present section indicator, create a new one and initialize
        #the aggregation entries
        if sec_ind not in partial_dic:
            partial_dic[sec_ind] = ({keysdic['Exposed system']: scensum[keysdic['Exposed system']],
                                     keysdic['Type of system']: scensum[keysdic['Type of system']],
                                     keysdic['Exposed value']:0,
                                     keysdic['Hazard scenario']:scensum[keysdic['Hazard scenario']],
                                     keysdic['Impact damage']:0})
        #Add the values to the aggregation entries
        partial_dic[sec_ind][keysdic['Exposed value']]+=value[keysdic['Exposed value']]
        partial_dic[sec_ind][keysdic['Impact damage']] += value[keysdic['Impact damage']]

    #Define the saving file path
    namefile = filename+'_partial_aggregate' + '.csv'
    path = Path.cwd().parent.parent / 'results/csvs' / namefile

    #Export the dictionary into a csv file. The column order is pre-defined and each entry is saved in a row
    with open(path, mode='w', newline='') as file:
        fieldnames = [keysdic['Section indentificator'],keysdic['Exposed system'], keysdic['Type of system'], keysdic['Exposed value'],
                      keysdic['Hazard scenario'],keysdic['Impact damage']]
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
        #Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        #Write each row (each inner dictionary as a row)
        for key, sub_dict in partial_dic.items():
            row = {col: sub_dict.get(col, '') for col in fieldnames}
            #Add the dictionary key as an additional row entry
            row[keysdic['Section indentificator']] = key
            writer.writerow(row)