from .. import list_dics_functions as ldfun
import rasterstats as rsts

def impact_mean_calc(pathexp,pathscen,system_dic,key):
    # Obtain zonal stats for the hazard raster map into the exposition polygons and add them to the dic. We change the
    # None values by 0 and round the results to three decimals

    zonal_stats = rsts.zonal_stats(str(pathexp), str(pathscen), stats=['mean'])

    for item in zonal_stats:
        if item['mean'] is None:
            item['mean'] = 0
        item['mean'] = round(item['mean'], 3)

    ldfun.add_listofdics_to_dicofdics(system_dic, zonal_stats, [key])

def imp_damage_compute(system_dic,dmfrackey,expvalkey,impdamkey):
    #Compute the economic impact, multiplying the damage percentage by the value of each building of the system and
    #add it to the dic.
    ldfun.add_dic_to_dicofdics(system_dic, ldfun.product_columns_dic(system_dic, dmfrackey, expvalkey),
                               impdamkey)

def partial_aggregates(partialaggdic,system_dic,system,scen,keysdic):

    partial_dic = {}
    #Go through the result dic and aggregate the results in the different entries of the partial dic taking into account
    #the different values of the Section indicator.
    for value in system_dic.values():

        sec_ind=value[keysdic['Section identificator']]
        #If there's still no entry in the partial dic for the present section indicator, create a new one and initialize
        #the aggregation entries
        if sec_ind not in partial_dic:
            partial_dic[sec_ind] = ({keysdic['Exposed system']:system,
                                     keysdic['Type of system']: system_dic[next(iter(system_dic))]
                                     [keysdic['Type of system']],keysdic['Exposed value']:0,
                                     keysdic['Hazard scenario']:scen,keysdic['Impact damage']:0})
        #Add the values to the aggregation entries
        partial_dic[sec_ind][keysdic['Exposed value']]+=value[keysdic['Exposed value']]
        partial_dic[sec_ind][keysdic['Impact damage']] += value[keysdic['Impact damage']]

    partialaggdic.extend([{keysdic['Section identificator']: key, **value} for key, value in partial_dic.items()])