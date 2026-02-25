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
    """
        Perform raster–raster impact assessment.

        The function:
        1. Loads hazard scenario raster(s).
        2. Loads exposed system raster.
        3. Preprocesses rasters (alignment, masks, metadata).
        4. Applies the selected damage function.
        5. Computes impact results (exposure × damage).
        6. Exports the resulting raster.
        7. Computes summary results.
        8. Optionally computes partial spatial aggregation.

        PARAMETERS
        ----------
        syst : str
            Name of the exposed system.

        scen : str
            Name of the hazard scenario.

        expsystdic : dict
            Dictionary describing the exposed system (path, damage function, etc.).

        scendic : dict
            Dictionary containing hazard raster information.

        partial_agg_flag : bool
            If True, compute and return partial aggregation results.

        RETURNS
        -------
        tuple
            If partial_agg_flag is True:
                (scensum, partial_agg_dic)

            If partial_agg_flag is False:
                (scensum, None)
        """

    # --------------------------------------------------------------
    # 1. Open hazard scenario rasters
    # --------------------------------------------------------------
    raster_scen_list = [
        ras.open(scendic[haz]['path'])
        for haz in scendic.keys()
    ]

    # --------------------------------------------------------------
    # 2. Open exposed system raster and preprocess
    # --------------------------------------------------------------
    with ras.open(expsystdic['path']) as raster_system:

        # Preprocess:
        # - Align rasters
        # - Extract data arrays
        # - Create no-data masks
        # - Retrieve metadata for output writing
        raster_system_data, raster_scen_data_list, mask_system, \
        combined_mask, kwargs=preprocess(
            raster_system,
            raster_scen_list
        )
    # Close hazard rasters
    for r in raster_scen_list:
        r.close()

    # --------------------------------------------------------------
    # 3. Apply damage function
    # --------------------------------------------------------------
    if expsystdic['Damage function']=='file':

        # Damage function applied in each pixel defined by external shapefile
        raster_vuln_data =dmfun.apply_dam_fun_file(
            raster_scen_data_list,
            combined_mask,
            expsystdic['Damage function file'],
            kwargs
        )
    else:
        # The same damage function for every pixel defined by the input parameter
        raster_vuln_data =dmfun.apply_dam_fun_raster(
            raster_scen_data_list,
            combined_mask,
            expsystdic['Damage function']
        )

    # --------------------------------------------------------------
    # 4. Compute impact results
    #    Impact = Exposure × Damage fraction
    # --------------------------------------------------------------
    final_mask = combined_mask & mask_system
    results =np.where(
        final_mask,
        raster_system_data * raster_vuln_data,
        np.nan
    )

    # --------------------------------------------------------------
    # 5. Compute scenario summary
    # --------------------------------------------------------------
    scensum=scensum_dic(
        syst,
        expsystdic,
        raster_system_data,
        scen,
        results
    )

    # --------------------------------------------------------------
    # 6. Export result raster
    # --------------------------------------------------------------
    outputs.tif_output(syst + scen, results,kwargs)

    # --------------------------------------------------------------
    # 7. Return results
    # --------------------------------------------------------------
    if partial_agg_flag:
        return (
            scensum,
            partial_aggregates(
                syst,
                expsystdic,
                raster_system_data,
                scen,
                results,
                kwargs['transform']
            )
        )

    return scensum, None

def scensum_dic(system,expsystdic, raster_system_data,scen,results):
    """
        Build the summary dictionary for a given system and impact scenario.

        The function aggregates:
        - Total exposed value (sum of system raster).
        - Total impact damage (sum of damage results raster).

        Parameters:
        - system: name of the exposed system.
        - expsystdic: dictionary containing system metadata.
        - raster_system_data: NumPy array of exposed values.
        - scen: name of the impact scenario.
        - results: NumPy array of computed impact damages.

        Returns:
        - Dictionary containing summary information for reporting/output.
        """
    return {
        dics.keysdic['Exposed system']: system,
        dics.keysdic['Type of system']: expsystdic['Type of system'],
        # Total exposed value (ignoring NaNs)
        dics.keysdic['Exposed value']: round(np.nansum(raster_system_data)),
        dics.keysdic['Impact scenario']:scen,
        # Total impact damage (ignoring NaNs)
        dics.keysdic['Impact damage']:round(np.nansum(results))
    }

def partial_aggregates(system,expsystdic,raster_system_data,scen,results,transform):
    """
        Compute partial (section-based) aggregated damages using zonal statistics.

        The function:
        1. Reads the spatial aggregation shapefile.
        2. Computes zonal statistics (sum) over the damage raster.
        3. Builds a list of dictionaries containing section-level results.

        Parameters:
        - system: name of the exposed system.
        - expsystdic: dictionary containing system metadata.
        - raster_system_data: NumPy array of exposed values.
        - scen: name of the impact scenario.
        - results: NumPy array of computed impact damages.
        - transform: affine transform of the results' raster.

        Returns:
        - List of dictionaries with section-level aggregated results.
        """
    partialaggdic=[]
    # Retrieve the path of the spatial aggregation shapefile
    partial_agg_map_path=input_reading.reading_folder_files(
        'spatial_distribution_input',
        '.shp')
    # Extract the first shapefile found in the folder
    key = list(partial_agg_map_path.keys())[0]
    partial_agg_map_path=partial_agg_map_path[key]
    # Convert shapefile to dictionary indexed by section identifier
    partial_agg_secs_dic,crs=input_reading.shp_to_dic(
        partial_agg_map_path,
        [dics.keysdic['Section identificator']]
    )
    # Compute zonal statistics of results and exposed value (sum of damages per polygon)
    partial_agg_results=rsts.zonal_stats(
        str(partial_agg_map_path),
        results,
        nodata=np.nan,
        affine=transform,
        stats=['sum']
    )
    exposed_value_partial=rsts.zonal_stats(
        str(partial_agg_map_path),
        raster_system_data,
        nodata=np.nan,
        affine=transform,
        stats=['sum']
    )
    # Add zonal statistics results and exposed value to the section dictionary
    ldfun.add_listofdics_to_dicofdics(
        partial_agg_secs_dic,
        partial_agg_results,
        [dics.keysdic['Impact damage']]
    )
    ldfun.add_listofdics_to_dicofdics(
        partial_agg_secs_dic,
        exposed_value_partial,
        [dics.keysdic['Exposed value']]
    )

    # Build the output dictionary for each section
    for sec in partial_agg_secs_dic.keys():
        partial_indiv_dic={
            dics.keysdic['Exposed system']: system,
            dics.keysdic['Type of system']: expsystdic['Type of system'],
            dics.keysdic['Section identificator']: sec,
            # Total exposed value (same for all sections in the current implementation)
            dics.keysdic['Exposed value']:
                round(partial_agg_secs_dic[sec][dics.keysdic['Exposed value']]),
            dics.keysdic['Impact scenario']:scen,
            # Section-level aggregated damage
            dics.keysdic['Impact damage']:
                round(partial_agg_secs_dic[sec][dics.keysdic['Impact damage']])
        }
        partialaggdic.append(partial_indiv_dic)
    return partialaggdic