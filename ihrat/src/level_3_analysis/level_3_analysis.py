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

    Data is categorized and processed with specific methods for both types of exposed systems:
    - Vector systems (.shp, .geojson): zonal statistics are applied to extract hazard values
      at element locations, followed by damage function application.
    - Raster systems (.tif): raster-to-raster analysis is performed pixel-wise using the
      specified damage function, which can be uniform or spatially distributed via a shapefile.

    Damage functions support two application types:
    - Relative: returns a damage fraction [0-1] multiplied by the exposed value.
    - Absolute: returns a damage value in monetary units multiplied by the exposed value.

    Results are exported as summary statistics and, if enabled, partial aggregation results
    by territorial units.

    :param hazard_input_dic: (dict) Dictionary containing hazard input data. Each key represents a hazard
        type (e.g., 'Flooding'), and its value is a dictionary with:
        - 'folder' (str): Name of the subfolder within 'haz_input_data/' where files are located.
        - 'extension' (str): File extension ('.tif' for raster, '.shp' for vector).
    :param params_dic: (dict) Dictionary containing global execution parameters:
    - 'scenarios' (list): List of climate/risk scenarios (e.g., ['RCP45']). Use [] if filenames do not depend on a scenario.
    - 'horizons' (list): Time horizons (e.g., ['2030']). Use [] if filenames do not depend on a horizon.
    - 'return periods' (list): List of return periods (e.g., ['100']). Use [] if filenames do not depend on a return period.
    - 'percentiles' (list): List of percentiles (e.g., ['50', '95']). Use [] if filenames do not depend on a percentile.
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
    # Rearrange hazard dictionary according to scenarios, horizons, return rates and percentiles
    hazard_input_dic=rearranging_dics(hazard_input_dic,params_dic['scenarios'],params_dic['horizons'],params_dic['return periods'],params_dic['percentiles'])

    # ------------------------------------------------------------------
    # 2. Load exposed systems (vector .shp, .geojson and raster .tif)
    # ------------------------------------------------------------------
    expsystdic=input_reading.reading_files('exp_input_data', ('.shp','.geojson','.tif'))

    # Containers for outputs
    summarydic = [] # Global summary results
    partialaggdic = [] # Partial aggregation results (optional)

    # ------------------------------------------------------------------
    # 3. Main processing loop over exposed systems
    # ------------------------------------------------------------------
    for syst, syst_dic in expsystdic.items():
        # --------------------------------------------------------------
        # CASE A: Vector exposed system (.shp,.geojson)
        # --------------------------------------------------------------
        if syst_dic['extension'] == '.shp' or syst_dic['extension'] == '.geojson':

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

def parse_file_params(file_name):
    """
    Extract hazard file parameters from a filename by position from the end.

    Expected filename format: {type}_{location}_{RP}_{SCENARIO}_{PERCENTILE}_{HORIZON}
    Example: 'flooding_Martil_RP100_RCP45_50_2050'

    PARAMETERS
    ----------
    file_name : str
        Filename without extension.

    RETURNS
    -------
    dict or None
        Dictionary with keys 'rp', 'scenario', 'percentile', 'horizon'
        extracted from the last 4 tokens. Returns None if the filename
        does not have the expected minimum number of tokens.
    """
    tokens = file_name.split('_')

    # Minimum 6 tokens required: type + location + RP + SCENARIO + PERCENTILE + HORIZON
    if len(tokens) >= 6:
        return {
            'rp':         tokens[-4],
            'scenario':   tokens[-3],
            'percentile': tokens[-2],
            'horizon':    tokens[-1]
        }
    return None


def rearranging_dics(hazard_input_dic, scenarios, horizons, return_rates, percentiles):
    """
    Reorganize the hazard input dictionary by scenario, horizon, return period,
    and percentile combinations.

    For each combination of the provided parameters, the function searches all
    hazard files and assigns those whose filename matches the combination to the
    corresponding key in the output dictionary.

    PARAMETERS
    ----------
    hazard_input_dic : dict
        Dictionary of hazard indicators. Each value contains a 'files' sub-dictionary
        where keys are filenames and values are file metadata dictionaries.
    scenarios : list of str
        List of climate scenarios (e.g., ['RCP45', 'RCP85']). Use [] or None if
        filenames do not depend on a scenario.
    horizons : list of str
        List of time horizons (e.g., ['2030', '2050']). Use [] or None if
        filenames do not depend on a horizon.
    return_rates : list of str
        List of return periods (e.g., ['10', '100']). Use [] or None if
        filenames do not depend on a return period.
    percentiles : list of str
        List of percentiles (e.g., ['50', '95']). Use [] or None if
        filenames do not depend on a percentile.

    RETURNS
    -------
    dict
        Dictionary where:
        - Keys are strings combining the active parameters joined by '_'
          (e.g., 'RCP45_2050_100_50').
        - Values are dictionaries mapping each hazard indicator to its
          corresponding file metadata for that combination.
    """
    scen_hor_ret_dic = {}

    # Iterate over all parameter combinations
    # Empty string ('') is used as placeholder when a parameter is not active
    for scen in (scenarios or ['']):
        for hor in (horizons or ['']):
            for ret in (return_rates or ['']):
                for pct in (percentiles or ['']):

                    # Build combination key, ignoring empty placeholders
                    key = '_'.join(filter(None, [scen, hor, ret, pct]))
                    scen_hor_ret_dic[key] = {}

                    # Search all hazard files for those matching this combination
                    for haz, haz_dic in hazard_input_dic.items():
                        for file_name, file_dic in haz_dic['files'].items():

                            # Extract parameters from filename
                            p = parse_file_params(file_name)
                            if p is None:
                                continue

                            # Assign file to combination if all parameters match
                            if (p['scenario']   == scen and
                                p['horizon']     == hor  and
                                p['rp']          == ret  and
                                p['percentile']  == pct):
                                scen_hor_ret_dic[key][haz] = file_dic

    return scen_hor_ret_dic