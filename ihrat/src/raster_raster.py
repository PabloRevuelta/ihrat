import outputs
import rasterio as ras
import numpy as np
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.coords import BoundingBox
from rasterio.windows import from_bounds
from rasterio.transform import from_origin
import damage_functions as damfun

def get_common_bounds(raster_system, raster_scen):

    #We know crs are different

    crs_system = raster_system.crs
    crs_scen = raster_scen.crs

    bounds_scen = raster_scen.bounds

    #Transform the system bounds into the scen crs
    bounds_system=BoundingBox(*transform_bounds(crs_system, crs_scen, *raster_system.bounds))

    #Check if they're the same. If not, look for the common bounds and return them
    if bounds_scen==bounds_system:
        return bounds_scen
    else:
        left = max(bounds_scen.left, bounds_system.left)
        bottom = max(bounds_scen.bottom, bounds_system.bottom)
        right = min(bounds_scen.right, bounds_system.right)
        top = min(bounds_scen.top, bounds_system.top)

    return BoundingBox(left, bottom, right, top)

def raster_process(raster_system, raster_scen):

    #We compare the resolution,crs, bounds from the input rasters
    same_res = raster_system.res == raster_scen.res
    same_crs = raster_system.crs == raster_scen.crs
    same_bounds = raster_system.bounds==raster_scen.bounds
    a=raster_system.bounds
    b=raster_scen.bounds

    #Get the metadata of the scen raster
    kwargs = raster_system.meta.copy()

    #If all of them are the same, read and output rasters
    if all([same_res, same_crs, same_bounds]):
        return raster_system.read(),raster_scen.read(), kwargs #OPTION 1 for both rasters (untouched)

    #Take the scen crs and res as reference
    crs = raster_scen.crs
    res = raster_scen.res

    if same_crs and same_bounds: #Same crs and bounds, but dif res, therefore, shape and transform

        raster_scen_data = raster_scen.read #OPTION 1 for scen raster (untouched)

        #Bounds, shape and transform as the scen raster
        shape = raster_scen.shape
        transform = raster_scen.transform
    else:
        bounds=get_common_bounds(raster_system, raster_scen)

        if bounds==raster_scen.bounds:

            raster_scen_data = raster_scen.read(1)  # OPTION 1 for scen raster (untouched)

            #Shape and transform as the scen raster
            shape = raster_scen.shape
            transform = raster_scen.transform
        else:

            window = from_bounds(*bounds, transform=raster_scen.transform)
            raster_scen_data=raster_scen.read(1,window=window) #OPTION 2 for scen raster (cropped to common window)

            #Compute the shape for the sytem reproject with the common bounds and the scen resol
            xres,yres=res
            width = round((bounds.right - bounds.left) / xres)
            height = round((bounds.top - bounds.bottom) / abs(yres))
            shape=(height,width)

            #Create the transform
            transform = from_origin(bounds.left, bounds.top, xres, yres)


    #Create an empty array for the reproject of the system raster
    raster_system_data= np.empty(shape, dtype=np.float32)

    #Reprpject the scen array
    reproject(
        source=ras.band(raster_system, 1),
        destination=raster_system_data,
        src_transform=raster_system.transform,
        src_crs=raster_system.crs,
        dst_transform=transform,
        dst_crs=crs,
        #dst_shape=shape,
        resampling=Resampling.nearest
    )

    #Update the kwargs
    height, width = shape
    kwargs.update({
        'crs': crs,
        'transform': transform,
        'width': width,
        'height': height
    })


    return raster_system_data, raster_scen_data,kwargs




def raster_raster(expsystdic,scendic,keysdic,keysoutputdic):

    #Create dic for the summary table
    summarydic =[]

    for system in expsystdic.keys():
        print(system)
        for scen in scendic.keys():
            print(scen)
            with ras.open(expsystdic[system]['path']) as raster_system, ras.open(scendic[scen]) as raster_scen:

                raster_system_data, raster_scen_data,kwargs=raster_process(raster_system, raster_scen)

                raster_system_data = np.where(raster_system_data == raster_system.nodata, np.nan, raster_system_data)
                mask_system = raster_system_data != raster_system.nodata if raster_system.nodata is not None else np.ones_like(
                    raster_system_data, dtype=bool)

                raster_scen_data = np.where(raster_scen_data == raster_scen.nodata, np.nan, raster_scen_data)
                mask_scen = ~np.isnan(raster_scen_data)

                #Entry for the summary dictionary of this scenario. Add the file system name  and the
                #aggregated exposed value
                scensum = {keysdic['Exposed system']: system,
                           keysdic['Exposed value']: round(np.nansum(raster_system_data))}


                raster_scen_data =damfun.apply_dam_fun_raster(raster_scen_data,mask_scen,
                                                              expsystdic[system]['Damage function'])

                final_mask = mask_scen & mask_system
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
    outputs.summary_raster_output(summarydic, keysdic, keysoutputdic)