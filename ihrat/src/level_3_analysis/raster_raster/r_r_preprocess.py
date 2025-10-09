import rasterio as ras
import numpy as np

from rasterio.windows import from_bounds
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.coords import BoundingBox



def get_common_bounds(rasters_list,ref_crs):

    #Obtiene los bounds comunes (intersección) de todos los rasters en el CRS dado.

    transformed_bounds = []
    for r in rasters_list:
        b = transform_bounds(r.crs, ref_crs, *r.bounds)
        transformed_bounds.append(BoundingBox(*b)) # type: ignore

    #Check if they're the same. If not, look for the common bounds and return them
    if all(b == transformed_bounds[0] for b in transformed_bounds):
        return transformed_bounds[0]
    else:
        left = max(b.left for b in transformed_bounds)
        bottom = max(b.bottom for b in transformed_bounds)
        right = min(b.right for b in transformed_bounds)
        top = min(b.top for b in transformed_bounds)

    return BoundingBox(left, bottom, right, top)


def reproject_raster(raster_system,crs,shape,transform):

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

def reproject_bounds(raster,bounds,shape,transform,ref_raster):
    # Cut the system raster to common bounds to get the aggregated value in the study area
    bounds_scen = BoundingBox(*transform_bounds(ref_raster.crs, raster.crs, *bounds))  # type: ignore
    window = from_bounds(*bounds_scen, transform=raster.transform)
    raster_data = raster.read(1, window=window)
    raster_data = np.where(raster_data == raster.nodata, np.nan, raster_data)
    pre_sum = np.nansum(raster_data)

    raster_data = reproject_raster(raster, ref_raster.crs, shape, transform)
    raster_data = np.where(raster_data == raster.nodata, np.nan, raster_data)
    ratio = pre_sum / np.nansum(raster_data) # type: ignore
    raster_scen_data = raster_data * ratio

    return raster_scen_data


def get_pixel_area(res):
    #Devuelve el área del píxel (res_x * res_y) para medir resolución.
    return abs(res[0] * res[1])

def preprocess(raster_system, raster_scen_list):


    #Devuelve el raster de hazard con la mayor resolución (menor tamaño de píxel).
    ref_raster = min(raster_scen_list, key=lambda r: get_pixel_area(r.res))

    # Get the metadata of the scen raster
    kwargs = ref_raster.meta.copy()

    # 1️⃣ Verificar si todos tienen el mismo CRS, resolución y bounds
    same_crs = all(r.crs == ref_raster.crs for r in raster_scen_list+[raster_system])
    same_res = all(r.res == ref_raster.res for r in raster_scen_list+[raster_system])
    same_bounds = all(r.bounds == ref_raster.bounds for r in raster_scen_list+[raster_system])

    raster_scen_data_list=[]
    #1. If all of them are the same, read both rasters
    if all([same_res, same_crs, same_bounds]):
        raster_system_data=raster_system.read()
        for i in range(len(raster_scen_list)):
            raster_scen_data_list.append(raster_scen_list[i].read())

    #2. If same crs and bounds, but dif res, therefore, shape and transform. Read scen raster and reproject system raster
    #to macht scen res, shape and transform
    elif same_crs and same_bounds and not same_res:

        if raster_system.res==ref_raster.res:
            raster_system_data = raster_system.read()
        else:
            raster_system_data = reproject_raster(raster_system, ref_raster.crs,
                                                  ref_raster.shape, ref_raster.transform)
        for i in range(len(raster_scen_list)):
            if raster_scen_list[i].res==ref_raster.res:
                raster_scen_data_list.append(raster_scen_list[i].read())
            else:
                raster_scen_data_list.append(reproject_raster(raster_scen_list[i], ref_raster.crs,ref_raster.shape, ref_raster.transform))

    #3. If different crs or bounds. Get common bounds, cut the scen raster and resample system raster to common bounds
    #and scen res
    else:
        bounds=get_common_bounds(raster_scen_list+[raster_system],ref_raster.crs)
        # Compute the shape for the system reproject with the common bounds and the scen resol
        x_res, y_res = ref_raster.res
        width = round((bounds.right - bounds.left) / x_res)
        height = round((bounds.top - bounds.bottom) / abs(y_res))
        shape = (height, width)
        # Create the transform
        transform = from_origin(bounds.left, bounds.top, x_res, y_res)

        for i in range(len(raster_scen_list)):
            if bounds==raster_scen_list[i].bounds and raster_scen_list[i].res==ref_raster.res:
                raster_scen_data_list.append(raster_scen_list[i].read())
            elif bounds==raster_scen_list[i].bounds:
                raster_scen_data_list.append(
                    reproject_raster(raster_scen_list[i], ref_raster.crs, ref_raster.shape, ref_raster.transform))
            else:
                raster_scen_data_list.append(reproject_bounds(raster_scen_list[i],bounds,shape,transform,ref_raster))

        if bounds == raster_system.bounds and raster_system.res == ref_raster.res:
            raster_system_data=raster_system.read()
        elif bounds == raster_system.bounds:
            raster_system_data=reproject_raster(raster_system, ref_raster.crs, ref_raster.shape, ref_raster.transform)
        else:
            raster_system_data=reproject_bounds(raster_system, bounds, shape, transform, ref_raster)


        #Update the kwargs
        height, width = shape
        kwargs.update({
            'crs': ref_raster.crs,
            'transform': transform,
            'width': width,
            'height': height
        })

    #Change the no-data and create no-data masks for both rasters
    raster_system_data = np.where(raster_system_data == raster_system.nodata, np.nan, raster_system_data)
    mask_system = raster_system_data != raster_system.nodata if raster_system.nodata is not None else np.ones_like(
        raster_system_data, dtype=bool)
    mask_scen_list=[]
    for i in range(len(raster_scen_data_list)):
        raster_scen_data_list[i] = np.where(raster_scen_data_list[i] == raster_scen_list[i].nodata, np.nan, raster_scen_data_list[i])
        mask_scen_list.append(~np.isnan(raster_scen_data_list[i]))
    # 2️⃣ Crear máscara combinada: True solo donde todas las entradas son válidas
    combined_mask = np.logical_and.reduce(mask_scen_list)


    return raster_system_data, raster_scen_data_list, mask_system, combined_mask, kwargs