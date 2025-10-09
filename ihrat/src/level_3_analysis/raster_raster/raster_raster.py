import rasterio as ras
import numpy as np
import rasterstats as rsts

from .r_r_preprocess import preprocess
from ihrat.src.tools import outputs
from ihrat.src.level_3_analysis.damage_functions import damage_functions as dmfun
from ihrat.src.tools import dictionaries as dics
from ihrat.src.tools import input_reading
from ihrat.src.tools import list_dics_functions as ldfun


def raster_raster(syst, scen,expsystdic,scendic,partial_agg_flag):

    #Loop for every exposed system and every scen
    raster_scen_list = [ras.open(scendic[haz]['path']) for haz in scendic.keys()]

    with ras.open(expsystdic['path']) as raster_system:

        #Pre-process both rasters and get masks for both rasters non-values and metadata for saving the result
        raster_system_data, raster_scen_data_list, mask_system, combined_mask, kwargs=preprocess(raster_system, raster_scen_list)

    for r in raster_scen_list:
        r.close()

    a=0

    if expsystdic['Damage function']=='file':
        raster_vuln_data =dmfun.apply_dam_fun_file(raster_scen_data_list,combined_mask,
                                                   expsystdic['Damage function file'],kwargs)
    else:
        #Apply the damage function to the scen raster
        raster_vuln_data =dmfun.apply_dam_fun_raster(raster_scen_data_list,combined_mask,
                                                    expsystdic['Damage function'])

    #Multiply the damage raster (scen*damage function) and the system raster to get the risk result raster
    final_mask = combined_mask & mask_system #Combine scen and system no-data masks
    results =np.where(final_mask, raster_system_data * raster_vuln_data, np.nan)

    #Create the entry for summary dictionary for this system and this scenario and add it to the summary dic
    scensum=scensum_dic(syst,expsystdic, raster_system_data,scen,results)

    #Export the results array into a .tif file
    outputs.tif_output(syst + scen, results,kwargs)

    if partial_agg_flag:
        return (scensum,
                partial_aggregates(syst,expsystdic, raster_system_data,scen,results,kwargs['transform']))

    return scensum

def scensum_dic(system,expsystdic, raster_system_data,scen,results):
    return {dics.keysdic['Exposed system']: system,
           dics.keysdic['Type of system']: expsystdic['Type of system'],
           dics.keysdic['Damage function']: expsystdic['Damage function'],
           dics.keysdic['Exposed value']: round(np.nansum(raster_system_data)),
           dics.keysdic['Impact scenario']:scen,dics.keysdic['Impact damage']:round(np.nansum(results))}

def partial_aggregates(system,expsystdic,raster_system_data,scen,results,transform):

    partialaggdic=[]

    partial_agg_map_path=input_reading.reading_folder_files('spatial_distribution_input', '.shp')
    key = list(partial_agg_map_path.keys())[0]
    partial_agg_map_path=partial_agg_map_path[key]

    partial_agg_secs_dic,crs=input_reading.shp_to_dic(partial_agg_map_path, [dics.keysdic['Section identificator']])
    partial_agg_results=rsts.zonal_stats(str(partial_agg_map_path), results, nodata=np.nan,
                                         affine=transform,stats=['sum'])
    ldfun.add_listofdics_to_dicofdics(partial_agg_secs_dic, partial_agg_results, [dics.keysdic['Impact damage']])

    for sec in partial_agg_secs_dic.keys():
        partial_indiv_dic={dics.keysdic['Exposed system']: system,
               dics.keysdic['Type of system']: expsystdic['Type of system'],
               dics.keysdic['Section identificator']: sec,
               dics.keysdic['Damage function']: expsystdic['Damage function'],
               dics.keysdic['Exposed value']: round(np.nansum(raster_system_data)),
               dics.keysdic['Impact scenario']:scen,
               dics.keysdic['Impact damage']:round(partial_agg_secs_dic[sec][dics.keysdic['Impact damage']])}
        partialaggdic.append(partial_indiv_dic)
    return partialaggdic