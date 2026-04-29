from ihrat.src.tools import input_reading
from ihrat.src.tools import dictionaries as dics
from ihrat.src.tools import outputs

from ihrat.src.level_3_analysis.shape_exp import shape_exp
from ihrat.src.level_3_analysis.raster_raster import raster_raster as rr

state_counter=0

def main(hazard_input_dic: dict, params_dic: dict, scen_raster_dic: dict = None) -> None:
    """
    Processes hazard input data, exposed systems, and calculates risk analysis based on the provided
    parameters. The function integrates hazard data, vector and raster-based exposed systems, and 
    computes results for defined scenarios, horizons, and return periods.

    Data is categorized and processed with specific methods for both types of exposed systems 
    (vector and raster), performing zonal statistical analysis for vector data, and raster-to-raster 
    analysis for raster data. Results are ultimately outputted as summary statistics and, if enabled, 
    partial aggregation results.

    :param hazard_input_dic: (dict) Dictionary containing hazard input data. Each key represents a hazard
        type (e.g., 'Flooding'), and its value is a dictionary with:
        - 'folder' (str): Name of the subfolder within 'haz_input_data/' where files are located.
        - 'extension' (str): File extension ('.tif' for raster, '.shp' for vector).
    :param params_dic: (dict) Dictionary containing global execution parameters:
        - 'scenarios' (list): List of climate/risk scenarios (e.g., ['RCP45']). Use [] if filenames do not depend on a scenario.
        - 'horizons' (list): Time horizons (e.g., ['2030']). Use [] if filenames do not depend on a horizon.
        - 'return periods' (list): List of return periods (e.g., ['100']). Use [] if filenames do not depend on a return period.
        - 'partial agg' (bool): Whether to generate results by territorial units (True) or only global (False).
        - 'zonal stats method' (str): For vector systems; 'centers' or 'all touched'.
        - 'zonal stats value' (str): For vector systems; statistic to compute ('mean' or 'max').
    :param scen_raster_dic: (dict, optional) Dictionary with metadata for raster exposure systems.
        Keys are filenames (without .tif), and values are dictionaries with:
        - 'Type of system' (str): Category of the system (e.g., 'POP', 'AGR').
        - 'Damage function' (str): Name of the damage function to apply. Use 'file' to apply spatially 
          distributed functions defined in an external shapefile.
        - 'Damage function file' (str, optional): Name of the shapefile (without extension) in 
          'inputs/dam_fun_files/' if 'Damage function' is set to 'file'.
    :return: None
    """
    # Global counter used to track progress of processed scenarios
    global state_counter

    # ------------------------------------------------------------------
    # 1. Load hazard files for each hazard indicator with additional metadata: crs, extension...
    # ------------------------------------------------------------------
    for indicator_indiv_dic in hazard_input_dic.values():
        indicator_indiv_dic['files'] =input_reading.reading_files('haz_input_data/'+indicator_indiv_dic['folder'],indicator_indiv_dic['extension'])
    # Rearrange hazard dictionary according to scenarios, horizons, and return rates
    hazard_input_dic=rearranging_dics(hazard_input_dic,params_dic['scenarios'],params_dic['horizons'],params_dic['return periods'])

    # ------------------------------------------------------------------
    # 2. Load exposed systems (vector .shp and raster .tif)
    # ------------------------------------------------------------------
    expsystdic=input_reading.reading_files('exp_input_data', ('.shp','.tif'))

    # Containers for outputs
    summarydic = [] # Global summary results
    partialaggdic = [] # Partial aggregation results (optional)

    # ------------------------------------------------------------------
    # 3. Main processing loop over exposed systems
    # ------------------------------------------------------------------
    for syst, syst_dic in expsystdic.items():
        # --------------------------------------------------------------
        # CASE A: Vector exposed system (.shp)
        # --------------------------------------------------------------
        if syst_dic['extension'] == '.shp':

            for scen_hor_rp,scen_hor_rp_dic in hazard_input_dic.items():
                # Perform risk analysis using zonal statistics
                scensum,scen_partial_agg_dic=shape_exp.shape_exp(
                    syst,
                    scen_hor_rp,
                    syst_dic,
                    scen_hor_rp_dic,
                    params_dic['partial agg'],
                    params_dic['zonal stats method'],
                    params_dic['zonal stats value'])

                # Store results
                summarydic.append(scensum)
                if params_dic['partial agg']:
                    partialaggdic.append(scen_partial_agg_dic)

                print(scen_hor_rp)
                state_counter += 1
        # --------------------------------------------------------------
        # CASE B: Raster exposed system (.tif)
        # --------------------------------------------------------------
        elif syst_dic['extension']=='.tif':

            # Attach raster-specific metadata (system type and damage function)
            syst_dic['Type of system'] = scen_raster_dic[syst]['Type of system']
            syst_dic['Damage function'] = scen_raster_dic[syst]['Damage function']

            for scen, scen_dic in hazard_input_dic.items():

                # Perform raster-to-raster risk analysis
                scensum,scen_partial_agg_dic=rr.raster_raster(
                    syst,
                    scen,
                    syst_dic,
                    scen_dic,
                    params_dic['partial agg']
                )

                # Store results
                summarydic.append(scensum)
                if params_dic['partial agg']:
                    partialaggdic.append(scen_partial_agg_dic)

                # Progress tracking
                print(scen)
                state_counter += 1
        # Print processed system name
        print(syst)

    # Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_output(summarydic)
    if params_dic['partial agg']:
        outputs.partial_agg_output(partialaggdic)
def output_fields_keys(fields,dic):
    """
        Map output field names to internal keys used in a dictionary of system elements.

        For most fields, the mapping is direct using `dics.keysoutputdic`.
        For 'Exposed value' and 'Impact damage', the mapping depends on the
        system type of the first element in the dictionary.

        PARAMETERS
        ----------
        fields : list of str
            List of human-readable output field names.

        dic : dict of dict or list of dict
            Dict of system elements. Each element is a sub-dictionary
            containing 'Type of system' and other attributes.

        RETURNS
        -------
        list
            List of internal keys corresponding to each output field.
        """
    fieldkeys = []
    # Identify system type from the first element (assumes uniform type)
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            system_type = dic[list(dic.keys())[0]][dics.keysdic['Type of system']]
            # Map field based on system type
            fieldkeys.append(dics.keysoutputdic[field][system_type])
        else:
            # Direct mapping for other fields
            fieldkeys.append(dics.keysoutputdic[field])
    return fieldkeys

def rearranging_dics(hazard_input_dic, scenarios, horizons, return_rates):
    """
        Reorganize the hazard dictionary by grouping files according to
        scenario, time horizon, and return rate combinations.

        PARAMETERS
        ----------
        hazard_input_dic : dict
            Dictionary of hazard indicators. Each hazard contains a 'files'
            dictionary with filenames and metadata.

        scenarios : list or None
            Climate/risk scenarios to filter. If None or empty, treated as [''].

        horizons : list or None
            Time horizons to filter. If None or empty, treated as [''].

        return_rates : list or None
            Return periods to filter. If None or empty, treated as [''].

        RETURNS
        -------
        dict
            Nested dictionary structured as:
                { "scenario_horizon_return": { hazard_name : file_metadata } }
        """
    # Dictionary that will store the reorganized structure
    scen_hor_ret_dic = {}
    # ------------------------------------------------------------------
    # 1. Iterate through all combinations of scenarios, horizons, return periods
    #    If any list is empty/None, replace with [''] to allow matching
    # ------------------------------------------------------------------
    for scen in (scenarios or ['']):
        for hor in (horizons or ['']):
            for ret in (return_rates or ['']):
                # Build combined key, avoiding extra underscores if empty
                key = '_'.join(filter(None, [scen, hor, ret]))
                # Initialize dictionary for this combination
                scen_hor_ret_dic[key] = {}

                # ------------------------------------------------------
                # 2. Search matching files inside each hazard indicator
                # ------------------------------------------------------
                for haz, haz_dic in hazard_input_dic.items():
                    for file_name, file_dic in haz_dic['files'].items():
                        # Check that all non-empty filters appear in filename
                        if all(p in file_name for p in [scen, hor, ret] if p):
                            # Store the matching file under the hazard name
                            scen_hor_ret_dic[key][haz] = file_dic

    return scen_hor_ret_dic