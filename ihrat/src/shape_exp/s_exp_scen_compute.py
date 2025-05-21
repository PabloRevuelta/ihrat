import rasterstats as rsts
import geopandas as gpd

from .. import dictionaries as dics
from .. import list_dics_functions as ldfun

def s_r_impact_mean_calc(path_exp,path_scen,system_dic,zonal_stats_method,zonal_stats_value):
    # Get zonal stats for the impact raster map into the exposition polygons and add them to the dic. We change the
    # None values by 0 and round the results to three decimals

    if zonal_stats_method=='centers':
        zonal_stats = rsts.zonal_stats(str(path_exp), str(path_scen), stats=[zonal_stats_value])
    elif zonal_stats_method=='all touched':
        zonal_stats = rsts.zonal_stats(str(path_exp), str(path_scen), all_touched=True,stats=[zonal_stats_value])
    for item in zonal_stats:
        if item[zonal_stats_value] is None:
            item[zonal_stats_value] = 0
        item[zonal_stats_value] = round(item[zonal_stats_value], 3)
    key=dics.keysdic['Impact value']
    ldfun.add_listofdics_to_dicofdics(system_dic, zonal_stats, [key])

def s_s_impact_mean_calc(system_gdf,path_scen,system_dic,zonal_stats_value):

    scen_gdf=gpd.read_file(path_scen)

    for index, building in system_gdf.iterrows():
        print(str(index)+ '/' + str(len(system_gdf)))
        intersections = []
        for index2, polygon in scen_gdf.iterrows():
            if zonal_stats_value=='mean':
                if building['geometry'].intersects(polygon['geometry']):
                    intersections.append([building['geometry'].intersection(polygon['geometry']).area,
                                 polygon[dics.keysdic['Impact value']]])
                if sum(x for x,y in intersections)==0:
                    system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']]=0
                else:
                    system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']]=(
                    sum(x * y for x, y in intersections)/sum(x for x,y in intersections))
            if zonal_stats_value == 'max':
                if building['geometry'].intersects(polygon['geometry']):
                    intersections.append([polygon[dics.keysdic['Impact value']]])
                if sum(x for x in intersections)==0:
                    system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']]=0
                else:
                    system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']]=max(intersections)



        print(system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']])

def imp_damage_compute(system_dic):
    #Compute the economic impact, multiplying the damage percentage by the value of each building of the system and
    #add it to the dic.
    ldfun.add_dic_to_dicofdics(system_dic, ldfun.product_columns_dic(system_dic, dics.keysdic['Damage fraction'],
                                                                     dics.keysdic['Exposed value']),
                               dics.keysdic['Impact damage'])

def partial_aggregates(partialaggdic,system_dic,system,scen):

    partial_dic = {}
    #Go through the result dic and aggregate the results in the different entries of the partial dic taking into account
    #the different values of the Section indicator.
    for value in system_dic.values():

        sec_ind=value[dics.keysdic['Section identificator']]
        #If there's still no entry in the partial dic for the present section indicator, create a new one and initialize
        #the aggregation entries
        if sec_ind not in partial_dic:
            partial_dic[sec_ind] = ({dics.keysdic['Exposed system']:system,
                                     dics.keysdic['Type of system']: system_dic[next(iter(system_dic))]
                                     [dics.keysdic['Type of system']],dics.keysdic['Exposed value']:0,
                                     dics.keysdic['Impact scenario']:scen,dics.keysdic['Impact damage']:0})
        #Add the values to the aggregation entries
        partial_dic[sec_ind][dics.keysdic['Exposed value']]+=value[dics.keysdic['Exposed value']]
        partial_dic[sec_ind][dics.keysdic['Impact damage']] += value[dics.keysdic['Impact damage']]

    partialaggdic.extend([{dics.keysdic['Section identificator']: key, **value} for key, value in partial_dic.items()])