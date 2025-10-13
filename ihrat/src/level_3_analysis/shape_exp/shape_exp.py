from ihrat.src.tools import input_reading
from ihrat.src.tools import list_dics_functions as ldfun
from ihrat.src.level_3_analysis.damage_functions import damage_functions as dmfun
from ihrat.src.tools import outputs
from ihrat.src.tools import dictionaries as dics
from ihrat.src.level_3_analysis import level_3_analysis
from ihrat.src.tools import compute_zonal_stats

import geopandas as gpd

def shape_exp(syst,scen,expsystdic,scendic,partial_agg_flag,zonal_stats_method='centers',zonal_stats_value='mean'):

    # zonal_stats_method='centers' or 'all touched'
    # partial_agg_flag = False or True
    # impact_format= 'raster' or 'shapefile'
    # zonal_stats_value = 'mean' or 'max'

    # Main loop. Travel through every system exposed and compute the risk analysis for all impact scenarios.
    # Then, export the results to individual .csv files and .shp files. Also add the aggregate
    # results to the summary dic

    # Create a dictionary of the exposed system from the shapefile. Each entry is a building, Building IDs
    # being the keys. Each building has the exposed system type, the exposed value, the damage function to apply
    # and the geometric coordinates of the polygon.
    system_dic,_ = input_reading.shp_to_dic(expsystdic['path'],
                                          [dics.keysdic['Elements ID'],dics.keysdic['Type of system'],
                                           dics.keysdic['Exposed value'],dics.keysdic['Damage function'],'geometry'])
    # Add the impact scenario
    ldfun.add_value_to_dicofdics(system_dic, dics.keysdic['Impact scenario'], scen)

    # Entry for the summary dictionary of this scenario. Add the file system name, the type of system and the
    # aggregated exposed value
    scensum = {dics.keysdic['Exposed system']: syst,
               dics.keysdic['Type of system']: system_dic[next(iter(system_dic))][dics.keysdic['Type of system']],
               dics.keysdic['Exposed value']: ldfun.column_sum(system_dic, dics.keysdic['Exposed value']),
               dics.keysdic['Impact scenario']: scen}
    haz_keys=[]
    for haz in scendic.keys():

        haz_keys.append(haz)

        if scendic[haz]['extension'] == '.tif':
            # Compute the mean value of the impact raster map in each exposition polygon as the impact value on each
            # element of the system and add the results to the dictionary
            s_r_impact_mean_calc(haz,expsystdic['path'], scendic[haz]['path'], system_dic,
                                              zonal_stats_method,zonal_stats_value)
        elif scendic[haz]['extension'] == '.shp':
            # Compute the mean value of the impact raster map in each exposition polygon as the impact value on each
            # element of the system and add the results to the dictionary
            s_s_impact_mean_calc(expsystdic['path'], scendic[haz]['path'], system_dic,zonal_stats_value)

    # Compute the damage fraction as a result of the impact value and add it to the dic. The damage fraction
    # is computed applying a damage curve selected in the input file for each element of the system
    dmfun.apply_damage_fun_shp(system_dic)

    # Compute the economic value of the impact and add it to the dic.
    imp_damage_compute(system_dic)

    # Export the results dic into a shapefile
    outputs.shapefile_output(syst+scen, system_dic, expsystdic['crs'],partial_agg_flag)

    # Export the results dic in a csv file
    fields=['Elements ID', 'Type of system', 'Exposed value', 'Impact scenario', 'Damage function', 'Damage fraction',
            'Impact damage']
    new_field_names = level_3_analysis.output_fields_keys(fields, system_dic)
    new_field_names[4:4] = haz_keys
    fields[4:4] = haz_keys

    outputs.csv_output(syst + scen,fields,new_field_names,system_dic)

    # Add to the summary dictionary of this scenario the name of the scenario raster file and the aggregated
    # damage caused by the impact
    scensum[dics.keysdic['Impact damage']] = ldfun.column_sum(system_dic, dics.keysdic['Impact damage'])

    # Aggregate the results into categories determined by the Section identificator column from the shapefile
    # data and add them to the partial aggregate dic (if needed)
    if partial_agg_flag:
        return scensum,partial_aggregates(system_dic,syst,scen)


    return scensum

def s_r_impact_mean_calc(haz,path_exp, path_scen, system_dic, zonal_stats_method, zonal_stats_value):
    # Get zonal stats for the impact raster map into the exposition polygons and add them to the dic. We change the
    # None values by 0 and round the results to three decimals

    zonal_stats = compute_zonal_stats.shape_raster_zonal_stats(path_exp, path_scen, dics.keysdic['Elements ID'],
                                                               zonal_stats_method,zonal_stats_value)
    ldfun.add_dic_to_dicofdics(system_dic, zonal_stats, haz)

def s_s_impact_mean_calc(path_system, path_scen, system_dic, zonal_stats_value):

    zonal_stats = compute_zonal_stats.shape_shape_zonal_stats(path_system, path_scen, dics.keysdic['Elements ID'],
                                                              dics.keysdic['Impact value'], zonal_stats_value)
    ldfun.add_dic_to_dicofdics(system_dic, zonal_stats, dics.keysdic['Impact value'])

def imp_damage_compute(system_dic):
    #Compute the economic impact, multiplying the damage percentage by the value of each building of the system and
    #add it to the dic.
    ldfun.add_dic_to_dicofdics(system_dic, ldfun.product_columns_dic(system_dic, dics.keysdic['Damage fraction'],
                                                                     dics.keysdic['Exposed value']),
                               dics.keysdic['Impact damage'])

def partial_aggregates(system_dic,syst,scen):

    partial_dic = {}
    #Go through the result dic and aggregate the results in the different entries of the partial dic taking into account
    #the different values of the Section indicator.
    for value in system_dic.values():

        sec_ind=value[dics.keysdic['Section identificator']]
        #If there's still no entry in the partial dic for the present section indicator, create a new one and initialize
        #the aggregation entries
        if sec_ind not in partial_dic:
            partial_dic[sec_ind] = ({dics.keysdic['Exposed system']:syst,
                                     dics.keysdic['Type of system']: system_dic[next(iter(system_dic))]
                                     [dics.keysdic['Type of system']],dics.keysdic['Exposed value']:0,
                                     dics.keysdic['Impact scenario']:scen,dics.keysdic['Impact damage']:0})
        #Add the values to the aggregation entries
        partial_dic[sec_ind][dics.keysdic['Exposed value']]+=value[dics.keysdic['Exposed value']]
        partial_dic[sec_ind][dics.keysdic['Impact damage']] += value[dics.keysdic['Impact damage']]

    return partial_dic


