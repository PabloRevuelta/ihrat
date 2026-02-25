import rasterio as ras
import numpy as np

from rasterio.windows import from_bounds
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.coords import BoundingBox



def get_common_bounds(rasters_list,ref_crs):
    """
        Compute the common bounding box (intersection) of a list of rasters
        in a reference CRS.

        Steps:
        1. Transform each raster's bounds to the reference CRS.
        2. If all transformed bounds are identical, return that extent.
        3. Otherwise, compute the geometric intersection of all bounds
           and return the resulting BoundingBox.
        """
    # Transform bounds of all rasters to the reference CRS
    transformed_bounds = []
    for r in rasters_list:
        b = transform_bounds(r.crs, ref_crs, *r.bounds)
        transformed_bounds.append(BoundingBox(*b)) # type: ignore

    # If all bounds are identical after transformation, return any of them
    if all(b == transformed_bounds[0] for b in transformed_bounds):
        return transformed_bounds[0]
    # Otherwise, compute the geometric intersection of all bounds
    left = max(b.left for b in transformed_bounds)
    bottom = max(b.bottom for b in transformed_bounds)
    right = min(b.right for b in transformed_bounds)
    top = min(b.top for b in transformed_bounds)

    return BoundingBox(left, bottom, right, top)


def reproject_raster(raster_system,crs,shape,transform):
    """
        Reproject a raster to a target CRS, shape and transform.

        Parameters:
        - raster_system: input raster dataset
        - crs: target CRS
        - shape: (height, width) of the destination array
        - transform: affine transform for the destination raster

        Returns:
        - Reprojected raster as a NumPy array (float32).
        """
    # Allocate the destination array with the target shape
    raster_system_data = np.empty(shape, dtype=np.float32)

    # Reproject raster band 1 to the target CRS and grid
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
    """
        Clip a raster to common bounds and reproject it to match
        the reference raster grid.

        The function:
        1. Transforms the common bounds to the raster CRS.
        2. Extracts the overlapping window.
        3. Computes the original sum (pre-reprojection).
        4. Reprojects to the reference grid.
        5. Applies a correction ratio to preserve the aggregated value.

        Returns:
        - Reprojected and rescaled raster array.
        """
    # Transform common bounds to the raster CRS
    bounds_scen = BoundingBox(*transform_bounds(ref_raster.crs, raster.crs, *bounds))  # type: ignore
    # Extract window corresponding to the common bounds
    window = from_bounds(*bounds_scen, transform=raster.transform)
    raster_data = raster.read(1, window=window)
    # Replace nodata values with NaN
    raster_data = np.where(raster_data == raster.nodata, np.nan, raster_data)
    # Compute the sum before reprojection (used to preserve total value)
    pre_sum = np.nansum(raster_data)
    # Reproject raster to reference grid
    raster_data = reproject_raster(raster, ref_raster.crs, shape, transform)
    raster_data = np.where(raster_data == raster.nodata, np.nan, raster_data)
    # Compute correction ratio to preserve aggregated value
    ratio = pre_sum / np.nansum(raster_data) # type: ignore
    raster_scen_data = raster_data * ratio

    return raster_scen_data


def get_pixel_area(res):
    """
        Compute the pixel area from raster resolution.

        Parameters:
        - res: tuple (x_resolution, y_resolution)

        Returns:
        - Absolute pixel area (res_x * res_y).
        """
    return abs(res[0] * res[1])

def preprocess(raster_system, raster_scen_list):
    """
        Harmonize system and hazard rasters before risk calculation.

        This function:
        1. Selects the hazard raster with the highest resolution
           (smallest pixel area) as reference.
        2. Checks if CRS, resolution and bounds are consistent.
        3. If needed, reprojects and/or clips rasters to common bounds.
        4. Converts nodata values to NaN.
        5. Creates validity masks and a combined mask.

        Returns:
        - raster_system_data: processed system raster array
        - raster_scen_data_list: list of processed hazard raster arrays
        - mask_system: boolean mask of valid system pixels
        - combined_mask: boolean mask where all hazards are valid
        - kwargs: updated metadata for output raster writing
        """

    # Select hazard raster with the highest spatial resolution
    # (smallest pixel area) as the reference grid
    ref_raster = min(
        raster_scen_list,
        key=lambda r: get_pixel_area(r.res)
    )

    # Copy metadata from reference raster for output writing
    kwargs = ref_raster.meta.copy()

    # Check consistency of CRS, resolution and bounds
    same_crs = all(r.crs == ref_raster.crs for r in raster_scen_list+[raster_system])
    same_res = all(r.res == ref_raster.res for r in raster_scen_list+[raster_system])
    same_bounds = all(r.bounds == ref_raster.bounds for r in raster_scen_list+[raster_system])

    raster_scen_data_list=[]

    # Case 1: All rasters share CRS, resolution and bounds
    if all([same_res, same_crs, same_bounds]):

        # Directly read data without reprojection
        raster_system_data=raster_system.read(1)
        for r in raster_scen_list:
            raster_scen_data_list.append(r.read(1))

    # Case 2: Same CRS and bounds, different resolution
    elif same_crs and same_bounds and not same_res:

        # Reproject system raster if needed
        if raster_system.res==ref_raster.res:
            raster_system_data = raster_system.read(1)
        else:
            raster_system_data = reproject_raster(
                raster_system,
                ref_raster.crs,
                ref_raster.shape,
                ref_raster.transform
            )
        # Reproject hazard rasters if needed
        for r in raster_scen_list:
            if r.res==ref_raster.res:
                raster_scen_data_list.append(r.read(1))
            else:
                raster_scen_data_list.append(
                    reproject_raster(r,
                                     ref_raster.crs,
                                     ref_raster.shape,
                                     ref_raster.transform
                                     )
                )

    # Case 3: Different CRS and/or bounds
    else:
        # Compute the common spatial extent in reference CRS
        bounds=get_common_bounds(raster_scen_list+[raster_system],ref_raster.crs)
        # Compute target shape from common bounds and reference resolution
        x_res, y_res = ref_raster.res
        width = round((bounds.right - bounds.left) / x_res)
        height = round((bounds.top - bounds.bottom) / abs(y_res))
        shape = (height, width)
        # Define affine transform for common extent
        transform = from_origin(bounds.left, bounds.top, x_res, y_res)

        # Process hazard rasters
        for r in raster_scen_list:
            if bounds==r.bounds and r.res==ref_raster.res:
                raster_scen_data_list.append(r.read(1))
            elif bounds==r.bounds:
                raster_scen_data_list.append(
                    reproject_raster(r,
                                     ref_raster.crs,
                                     ref_raster.shape,
                                     ref_raster.transform
                                     )
                )
            else:
                raster_scen_data_list.append(
                    reproject_bounds(r,
                                     bounds,
                                     shape,
                                     transform,
                                     ref_raster
                                     )
                )

        # Process system raster
        if bounds == raster_system.bounds and raster_system.res == ref_raster.res:
            raster_system_data=raster_system.read(1)
        elif bounds == raster_system.bounds:
            raster_system_data=reproject_raster(
                raster_system,
                ref_raster.crs,
                ref_raster.shape,
                ref_raster.transform
            )
        else:
            raster_system_data=reproject_bounds(
                raster_system,
                bounds,
                shape,
                transform,
                ref_raster
            )

        # Update metadata to match the new grid
        height, width = shape
        kwargs.update({
            'crs': ref_raster.crs,
            'transform': transform,
            'width': width,
            'height': height
        })

    # Replace nodata values with NaN in system raster
    raster_system_data = np.where(
        raster_system_data == raster_system.nodata,
        np.nan,
        raster_system_data
    )

    # Create the system validity mask
    mask_system = (
        raster_system_data != raster_system.nodata
        if raster_system.nodata is not None
        else np.ones_like(raster_system_data, dtype=bool)
    )

    # Replace nodata and create hazard masks
    mask_scen_list=[]
    for i in range(len(raster_scen_data_list)):
        raster_scen_data_list[i] = np.where(
            raster_scen_data_list[i] == raster_scen_list[i].nodata,
            np.nan,
            raster_scen_data_list[i]
        )
        mask_scen_list.append(~np.isnan(raster_scen_data_list[i]))
    # Create the combined mask: valid only where all hazards are valid
    combined_mask = np.logical_and.reduce(mask_scen_list)

    return raster_system_data, raster_scen_data_list, mask_system, combined_mask, kwargs