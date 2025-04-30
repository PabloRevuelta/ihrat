import rasterio as ras
import numpy as np

from rasterio.windows import from_bounds
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.coords import BoundingBox



def get_common_bounds(raster_system, raster_scen):

    #Get scen bounds
    bounds_scen = raster_scen.bounds

    #Get system bounds transformed into the scen crs
    bounds_system=BoundingBox(*transform_bounds(raster_system.crs, raster_scen.crs, *raster_system.bounds))

    #Check if they're the same. If not, look for the common bounds and return them
    if bounds_scen==bounds_system:
        return bounds_scen
    else:
        left = max(bounds_scen.left, bounds_system.left)
        bottom = max(bounds_scen.bottom, bounds_system.bottom)
        right = min(bounds_scen.right, bounds_system.right)
        top = min(bounds_scen.top, bounds_system.top)

    return BoundingBox(left, bottom, right, top)

def reproject_raster(raster_system,crs,res,shape,transform):

    # Create an empty array for the reproject of the system raster
    raster_system_data = np.empty(shape, dtype=np.float32)

    # Reproject the scen array
    reproject(
        source=ras.band(raster_system, 1),
        destination=raster_system_data,
        src_transform=raster_system.transform,
        src_crs=raster_system.crs,
        dst_transform=transform,
        dst_crs=crs,
        # dst_shape=shape,
        resampling=Resampling.nearest
    )

    return raster_system_data

def preprocess(raster_system, raster_scen):

    #Get the metadata of the scen raster
    kwargs = raster_system.meta.copy()

    #Compare the resolution,crs, bounds from the input rasters
    same_res = raster_system.res == raster_scen.res
    same_crs = raster_system.crs == raster_scen.crs
    same_bounds = raster_system.bounds==raster_scen.bounds

    #1. If all of them are the same, read both rasters
    if all([same_res, same_crs, same_bounds]):
        raster_system_data=raster_system.read()
        raster_scen_data = raster_scen.read()
    #2. If same crs and bounds, but dif res, therefore, shape and transform. Read scen raster and reproject system raster
    #to macht scen res, shape and transform
    elif same_crs and same_bounds and not same_res:

        raster_scen_data = raster_scen.read
        raster_system_data=reproject_raster(raster_system,raster_scen.crs,raster_scen.res,
                                            raster_scen.shape,raster_scen.transform)

    #3. If different crs or bounds. Get common bounds, cut the scen raster and resample system raster to common bounds
    #and scen res
    else:
        bounds=get_common_bounds(raster_system, raster_scen)
        if bounds==raster_scen.bounds:
            raster_scen_data = raster_scen.read(1)
        else:

            #Cut scen raster to common bounds
            window = from_bounds(*bounds, transform=raster_scen.transform)
            raster_scen_data=raster_scen.read(1,window=window)

            #Compute the shape for the system reproject with the common bounds and the scen resol
            x_res,y_res=raster_scen.res
            width = round((bounds.right - bounds.left) / x_res)
            height = round((bounds.top - bounds.bottom) / abs(y_res))
            shape=(height,width)

            #Create the transform
            transform = from_origin(bounds.left, bounds.top, x_res, y_res)

            #Reproject system raster
            raster_system_data = reproject_raster(raster_system,raster_scen.crs, raster_scen.res, shape,transform)

            #Update the kwargs
            height, width = shape
            kwargs.update({
                'crs': raster_scen.crs,
                'transform': transform,
                'width': width,
                'height': height
            })

    #Change the no-data and create no-data masks for both rasters
    raster_system_data = np.where(raster_system_data == raster_system.nodata, np.nan, raster_system_data)
    mask_system = raster_system_data != raster_system.nodata if raster_system.nodata is not None else np.ones_like(
        raster_system_data, dtype=bool)
    raster_scen_data = np.where(raster_scen_data == raster_scen.nodata, np.nan, raster_scen_data)
    mask_scen = ~np.isnan(raster_scen_data)

    return raster_system_data, raster_scen_data, mask_system, mask_scen, kwargs