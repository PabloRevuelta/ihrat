from pathlib import Path
import list_dics_functions as ldfun
import scen_compute
import input_reading
import damage_functions as dmfun
import outputs

def output_fields_keys(dic,fields,keysdic,keysoutputdic):
    fieldkeys = []
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            type = dic[list(dic.keys())[0]][keysdic['Type of system']]
            fieldkeys.append(keysoutputdic[field][type])
        else:
            fieldkeys.append(keysoutputdic[field])
    return fieldkeys

def main():

    #Get the exposition maps paths and crs from the expmaps folder files
    #and the hazard scenarios maps paths from the hazmaps folder files
    expsystdic = input_reading.reading_shapefiles_exp()
    scendic = input_reading.reading_folder_files(Path.cwd().parent.parent / 'hazmaps','.tif')

    partial_agg_flag = True

    # Create dic for the summary table and one for the partial aggregate table (if needed)
    summarydic = []
    if partial_agg_flag:
        partialaggdic = []

    #We define the keys all the inner dictionaries are going to work with. The input .shp files need to be
    #pre-processed to use the same keys are their attribute headers
    keysdic = {'Exposed system':'SYSTEM','Elements ID': 'BUILD_ID', 'Exposed value': 'EXP_VALUE',
               'Type of system': 'TYPE','Damage function': 'DAM_FUN', 'Section identificator':'CUSEC',
               'Hazard scenario': 'HAZ_SCEN','Impact value':'IMP_VAL','Damage fraction':'DAM_FRAC',
               'Impact damage': 'IMP_DAMAGE'}

    #Types of systems: BUILD, POP

    keysoutputdic = {'Exposed system': 'Exposed system', 'Elements ID': 'Building ID',
                     'Exposed value':{'BUILD':'Exposed value (€)','POP':'Exposed people (n)'},
                     'Type of system': 'Type of element', 'Damage function': 'Damage function',
                     'Section identificator': 'CUSEC', 'Hazard scenario': 'Hazard scenario',
                     'Impact value': 'Impact value (m)', 'Damage fraction': 'Damage fraction',
                     'Impact damage': {'BUILD':'Impact damage (€)','POP':'Impacted people (n)'}}

    #Main loop. Travel through every system exposed and compute the risk analysis for all hazard scenarios.
    #Then, export the results to individual .csv files and .shp files. Also add the aggregate
    #results to the summary dic
    for system in expsystdic.keys():

        #Create a dictionary of the exposed system from the shapefile. Each entry is a building, Building IDs
        #being the keys. Each building has the exposed system type, the exposed value, the damage function to apply
        #and the geometric coordinates of the polygon.
        system_dic = input_reading.shp_to_dic(expsystdic[system]['path'], keysdic['Elements ID'])

        print(system)

        for scen in scendic.keys():

            #Entry for the summary dictionary of this scenario. Add the file system name, the type of system and the
            #aggregated exposed value
            scensum={keysdic['Exposed system']:system, keysdic['Type of system']:system_dic[next(iter(system_dic))]['TYPE'],
                     keysdic['Exposed value']:ldfun.column_sum(system_dic, 'EXP_VALUE')}

            #Add the hazard scenario
            ldfun.add_value_to_dicofidcs(system_dic, keysdic['Hazard scenario'], scen)

            #Compute the mean value of the hazard raster map in each exposition polygon as the impact value on each
            #element of the system and add the results to the dictionary
            scen_compute.impact_mean_calc(expsystdic[system]['path'],scendic[scen],system_dic,keysdic['Impact value'])

            #Compute the damage fraction as a result of the impact value and add it to the dic. The damage fraction
            #is computed applying a damage curve selected in the input file for each individual element of the system
            for indiv_element_dic in system_dic.values():
                dmfun.apply_damage_fun(indiv_element_dic,keysdic['Damage function'],keysdic['Damage fraction'],
                                       keysdic['Impact value'])

            #Compute the economic value of the impact and add it to the dic.
            scen_compute.imp_damage_compute(system_dic,keysdic['Damage fraction'],
                                            keysdic['Exposed value'], keysdic['Impact damage'])

            #Export the results dic into a shapefile
            outputs.shapefile_output(system+scen,system_dic,keysdic,expsystdic[system]['crs'])

            #Export the results dic in a csv file
            outputs.csv_output(system + scen, system_dic, keysdic,keysoutputdic)

            #Add to the summary dictionary of this scenario the name of the scenario raster file and the aggregated
            #damage caused by the impact
            scensum[keysdic['Hazard scenario']]=scen
            scensum[keysdic['Impact damage']] = ldfun.column_sum(system_dic, keysdic['Impact damage'])
            #Add the summary dictionary of this scenario to the summary dictionary
            summarydic.append(scensum)

            #Aggregate the results into categories determined by the Section identificator column from the shapefile
            #data and add them to the partial aggregate dic (if needed)
            if partial_agg_flag:
                scen_compute.partial_aggregates(partialaggdic,system_dic,system,scen,keysdic)
            print(scen)

    #Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_output(system_dic,summarydic,keysdic,keysoutputdic)
    if partial_agg_flag:
        outputs.partial_agg_output(system_dic,partialaggdic,keysdic,keysoutputdic)


if __name__ == "__main__":
    main()