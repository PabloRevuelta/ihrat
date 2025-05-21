import rasterio as ras
import numpy as np
import rasterstats as rsts

from .r_r_preprocess import preprocess
from .. import outputs
from .. import damage_functions as dmfun
from .. import dictionaries as dics
from .. import input_reading
from .. import list_dics_functions as ldfun


def raster_raster(expsystdic,scendic,partial_agg_flag,dam_fun_file):

    # Create dic for the summary table and one for the partial aggregate table (if needed)
    summarydic = []
    if partial_agg_flag:
        partialaggdic = []

    #Loop for every exposed system and every scen
    for system in expsystdic.keys():
        print(system)
        for scen in scendic.keys():
            print(scen)

            #Open system and scen rasters
            with (ras.open(expsystdic[system]['path']) as raster_system, ras.open(scendic[scen]) as raster_scen):

                #Pre-process both rasters and get masks for both rasters non-values and metadata for saving the result
                raster_system_data, raster_scen_data, mask_system,mask_scen,kwargs=preprocess(raster_system, raster_scen)

                if dam_fun_file:
                    raster_scen_data =dmfun.apply_dam_fun_file(raster_scen_data,mask_scen,
                                                               expsystdic[system]['Damage function file'])
                else:
                    #Apply the damage function to the scen raster
                    raster_scen_data =dmfun.apply_dam_fun_raster(raster_scen_data,mask_scen,
                                                                expsystdic[system]['Damage function'])

                #Multiply the damage raster (scen*damage function) and the system raster to get the risk result raster
                final_mask = mask_scen & mask_system #Combine scen and system no-data masks
                results =np.where(final_mask, raster_system_data * raster_scen_data, np.nan)

                #Create the entry for summary dictionary for this system and this scenario and add it to the summary dic
                scensum_dic(system,expsystdic, raster_system_data,scen,results,summarydic)

                if partial_agg_flag:
                    partial_aggregates(system,expsystdic, raster_system_data,scen,results,kwargs['transform'],partialaggdic)

            #Export the results array into a .tif file
            outputs.tif_output(system + scen, results,kwargs)

    # Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_output('raster_exp',expsystdic,summarydic)
    if partial_agg_flag:
        outputs.partial_agg_output('raster_exp',expsystdic, partialaggdic)

def scensum_dic(system,expsystdic, raster_system_data,scen,results,summarydic):
    scensum = {dics.keysdic['Exposed system']: system,
               dics.keysdic['Type of system']: expsystdic[system]['Type of system'],
               dics.keysdic['Damage function']: expsystdic[system]['Damage function'],
               dics.keysdic['Exposed value']: round(np.nansum(raster_system_data)),
               dics.keysdic['Impact scenario']:scen,dics.keysdic['Impact damage']:round(np.nansum(results))}

    summarydic.append(scensum)

def partial_aggregates(system,expsystdic,raster_system_data,scen,results,transform,partialaggdic):

    partial_agg_map_path=input_reading.reading_folder_files('partial_agg_map', '.shp')
    key = list(partial_agg_map_path.keys())[0]
    partial_agg_map_path=partial_agg_map_path[key]

    partial_agg_secs_dic=input_reading.shp_to_dic(partial_agg_map_path, dics.keysdic['Section identificator'])
    partial_agg_results=rsts.zonal_stats(str(partial_agg_map_path), results, nodata=np.nan,
                                         affine=transform,stats=['sum'])
    key = dics.keysdic['Impact damage']
    ldfun.add_listofdics_to_dicofdics(partial_agg_secs_dic, partial_agg_results, [key])

    for sec in partial_agg_secs_dic.keys():
        partial_indiv_dic={dics.keysdic['Exposed system']: system,
               dics.keysdic['Type of system']: expsystdic[system]['Type of system'],
               dics.keysdic['Section identificator']: sec,
               dics.keysdic['Damage function']: expsystdic[system]['Damage function'],
               dics.keysdic['Exposed value']: round(np.nansum(raster_system_data)),
               dics.keysdic['Impact scenario']:scen,
               dics.keysdic['Impact damage']:round(partial_agg_secs_dic[sec][dics.keysdic['Impact damage']])}
        partialaggdic.append(partial_indiv_dic)