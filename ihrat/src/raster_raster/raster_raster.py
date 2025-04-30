from .r_r_preprocess import preprocess
from .. import outputs
import rasterio as ras
import numpy as np
from .. import damage_functions as damfun


def raster_raster(expsystdic,scendic,keysdic,keysoutputdic):

    #Create dic for the summary table
    summarydic =[]

    #Loop for every exposed system and every scen
    for system in expsystdic.keys():
        print(system)
        for scen in scendic.keys():
            print(scen)

            #Open system and scen rasters
            with (ras.open(expsystdic[system]['path']) as raster_system, ras.open(scendic[scen]) as raster_scen):

                #Pre-process both rasters and get masks for both rasters nonn-values and metadata for saving the result
                raster_system_data, raster_scen_data, mask_system,mask_scen,kwargs=preprocess(raster_system, raster_scen)

                #Entry for the summary dictionary of this scenario. Add the file system name, the type of system exposed,
                # the aggregated exposed value and the damage function to apply
                scensum = {keysdic['Exposed system']: system,
                           keysdic['Type of system']: expsystdic[system]['Type of system'],
                           keysdic['Damage function']: expsystdic[system]['Damage function'],
                           keysdic['Exposed value']: round(np.nansum(raster_system_data))}

                #Apply the damage function to the scen raster
                raster_scen_data =damfun.apply_dam_fun_raster(raster_scen_data,mask_scen,
                                                              expsystdic[system]['Damage function'])

                #Multiply the damage raster (scen*damage function) and the system raster to get the risk result raster
                final_mask = mask_scen & mask_system #Combine scen and system no-data masks
                results =np.where(final_mask, raster_system_data * raster_scen_data, np.nan)


                # Add to the summary dictionary of this scenario the name of the scenario raster file and the aggregated
                # damage caused by the impact
                scensum[keysdic['Hazard scenario']] = scen
                raster_system_data = np.where(raster_system_data == raster_system.nodata, np.nan, raster_system_data)
                scensum[keysdic['Impact damage']] = round(np.nansum(results))

                # Add the summary dictionary of this scenario to the summary dictionary
                summarydic.append(scensum)
                

            #Export the results array into a .tif file
            outputs.tif_output(system + scen, results,kwargs)

    # Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_rr_output(expsystdic,summarydic, keysdic, keysoutputdic)