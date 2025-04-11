from pathlib import Path
import list_dics_functions as ldfun
import scen_compute
import input_reading
import damage_functions as dmfun
import outputs


def main():

    #Get the exposition maps paths and crs from the expmaps folder files
    #and the hazard scenarios maps paths from the hazmaps folder files
    expsystdic = input_reading.reading_shapefiles_exp()
    scendic = input_reading.reading_folder_files(Path.cwd().parent.parent / 'hazmaps','.tif')

    # Create dic for the summary table
    summarydic = []

    #We define the keys all the inner dictionaries are going to work with. The input .shp files need to be
    #pre-processed to use the same keys are their atribute headers
    keysdic = {'Exposed system':'SYSTEM','Elements ID': 'BUILD_ID', 'Exposed value': 'EXP_VALUE', 'Type of system': 'TYPE',
               'Damage function': 'DAM_FUN', 'Section indentificator':'CUSEC', 'Hazard scenario': 'HAZ_SCEN',
               'Impact value':'IMP_VAL','Damage fraction':'DAM_FRAC', 'Impact damage': 'IMP_DAMAGE'}

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
            outputs.csv_output(system + scen, system_dic, keysdic)

            #Add to the summary dictionary of this scenario the name of the scenario raster file and the aggregated
            #damage caused by the impact
            scensum[keysdic['Hazard scenario']]=scen
            scensum[keysdic['Impact damage']] = ldfun.column_sum(system_dic, keysdic['Impact damage'])

            #Export the results in a csv file with data aggregated in categories determined by the Section
            #indentificator column from the shapefile data
            outputs.partial_csv_output(system + scen, system_dic, keysdic, scensum)

            #Add the summary dictionary of this scenario to the summary dictionary
            summarydic.append(scensum)



            print(scen)

    #Export them to a .csv file.
    path = Path.cwd().parent.parent / 'results/csvs/manga_exposicion_summary.csv'
    outputs.listofddics_to_csv(summarydic, path)


if __name__ == "__main__":
    main()