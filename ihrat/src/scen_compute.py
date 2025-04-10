import list_dics_functions as ldfun
import damage_functions as dmfun
import rasterstats as rsts
from pathlib import Path

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