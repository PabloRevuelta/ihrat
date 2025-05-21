from .. import input_reading
from .. import list_dics_functions as ldfun
from .. import damage_functions as dmfun
from .. import outputs
from .. import dictionaries as dics

import geopandas as gpd

from . import s_exp_scen_compute as scen_compute

def shape_exp(impact_format,expsystdic,scendic,partial_agg_flag,zonal_stats_method='centers',zonal_stats_value='mean'):

    # zonal_stats_method='centers' or 'all touched'
    # partial_agg_flag = False or True
    # impact_format= 'raster' or 'shapefile'
    # zonal_stats_value = 'mean' or 'max'

    #Create dic for the summary table and one for the partial aggregate table (if needed)
    summarydic = []
    if partial_agg_flag:
        partialaggdic = []

    # Main loop. Travel through every system exposed and compute the risk analysis for all impact scenarios.
    # Then, export the results to individual .csv files and .shp files. Also add the aggregate
    # results to the summary dic
    for system in expsystdic.keys():

        # Create a dictionary of the exposed system from the shapefile. Each entry is a building, Building IDs
        # being the keys. Each building has the exposed system type, the exposed value, the damage function to apply
        # and the geometric coordinates of the polygon.
        if impact_format=='raster':
            system_dic = input_reading.shp_to_dic(expsystdic[system]['path'], dics.keysdic['Elements ID'])
        elif impact_format=='shapefile':
            # Also import the system shapefile into a geodataframe
            system_gdf = gpd.read_file(expsystdic[system]['path'])

            system_dic = system_gdf.set_index(dics.keysdic['Elements ID']).T.to_dict('dict')

        print(system)

        for scen in scendic.keys():

            # Entry for the summary dictionary of this scenario. Add the file system name, the type of system and the
            # aggregated exposed value
            scensum = {dics.keysdic['Exposed system']: system,
                       dics.keysdic['Type of system']: system_dic[next(iter(system_dic))]['TYPE'],
                       dics.keysdic['Exposed value']: ldfun.column_sum(system_dic, 'EXP_VALUE')}

            # Add the impact scenario
            ldfun.add_value_to_dicofdics(system_dic, dics.keysdic['Impact scenario'], scen)

            if impact_format == 'raster':
                # Compute the mean value of the impact raster map in each exposition polygon as the impact value on each
                # element of the system and add the results to the dictionary
                scen_compute.s_r_impact_mean_calc(expsystdic[system]['path'], scendic[scen], system_dic,
                                                  zonal_stats_method,zonal_stats_value)
            elif impact_format == 'shapefile':
                # Compute the mean value of the impact raster map in each exposition polygon as the impact value on each
                # element of the system and add the results to the dictionary
                scen_compute.s_s_impact_mean_calc(system_gdf, scendic[scen], system_dic,zonal_stats_value)

            # Compute the damage fraction as a result of the impact value and add it to the dic. The damage fraction
            # is computed applying a damage curve selected in the input file for each element of the system
            for indiv_element_dic in system_dic.values():
                dmfun.apply_damage_fun_shp(indiv_element_dic)

            # Compute the economic value of the impact and add it to the dic.
            scen_compute.imp_damage_compute(system_dic)

            # Export the results dic into a shapefile
            outputs.shapefile_output(system + scen, system_dic, expsystdic[system]['crs'])

            # Export the results dic in a csv file
            outputs.csv_output(system + scen, system_dic)

            # Add to the summary dictionary of this scenario the name of the scenario raster file and the aggregated
            # damage caused by the impact
            scensum[dics.keysdic['Impact scenario']] = scen
            scensum[dics.keysdic['Impact damage']] = ldfun.column_sum(system_dic, dics.keysdic['Impact damage'])
            # Add the summary dictionary of this scenario to the summary dictionary
            summarydic.append(scensum)

            # Aggregate the results into categories determined by the Section identificator column from the shapefile
            # data and add them to the partial aggregate dic (if needed)
            if partial_agg_flag:
                scen_compute.partial_aggregates(partialaggdic, system_dic, system, scen)
            print(scen)

    # Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_output(system_dic, summarydic)
    if partial_agg_flag:
        outputs.partial_agg_output(system_dic, partialaggdic)


