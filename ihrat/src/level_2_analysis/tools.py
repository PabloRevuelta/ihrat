import statistics as stats
import numpy as np
import copy
import norm_scales_dics

def rearranging_dics(indic_main_dic, scen_hor_fields):
    """
    Rearrange indicator dictionaries by scenario-horizon combinations.

    This function reorganizes a nested dictionary of indicators into a new
    structure grouped by scenario and time horizon. For each combination of
    scenario and horizon, it builds a dictionary of spatial units containing
    geometry and corresponding indicator values.

    Parameters
    ----------
    indic_main_dic : dict
        Dictionary containing indicator data. Expected structure:
        {
            indicator_name: {
                'dic': {
                    spatial_unit: {
                        'geometry': geometry_object,
                        scen_hor_key: value,
                        ...
                    },
                    ...
                }
            },
            ...
        }

    scen_hor_fields : dict
        Dictionary defining scenarios and horizons. Expected structure:
        {
            'scenarios': list of str,
            'horizons': list of str
        }

    Returns
    -------
    scen_hor_dic : dict
        Dictionary organized by scenario-horizon combinations:
        {
            'scenario_horizon': {
                spatial_unit: {
                    'geometry': geometry_object,
                    indicator_name: value,
                    ...
                },
                ...
            },
            ...
        }

    Notes
    -----
    - The function assumes that all indicators share the same spatial units.
    - Geometry is preserved and copied into each scenario-horizon dictionary.
    - Matching of scenario and horizon is done using substring checks
      (`scen in scen_hor` and `hor in scen_hor`).
    - A special case is handled when both scenario and horizon are 'single'.
    """

    # Initialize output dictionary
    scen_hor_dic = {}

    # Extract spatial units and their geometries from the first indicator
    spatial_units_dic = {
        spatial_unit: {'geometry': spatial_unit_dic['geometry']}
        for spatial_unit, spatial_unit_dic
        in indic_main_dic[next(iter(indic_main_dic))]['dic'].items()
    }

    # Loop over all scenario and horizon combinations
    for scen in scen_hor_fields['scenarios']:
        for hor in scen_hor_fields['horizons']:

            # Initialize dictionary for this scenario-horizon combination
            scen_hor_dic[scen + '_' + hor] = copy.deepcopy(spatial_units_dic)

            # Iterate over all indicators
            for indic, indic_dic in indic_main_dic.items():

                # Iterate over spatial units
                for spatial_unit, spatial_unit_dic in indic_dic['dic'].items():

                    # Iterate over scenario-horizon values
                    for scen_hor, value in spatial_unit_dic.items():

                        # Assign value if scenario and horizon match
                        if scen in scen_hor and hor in scen_hor:
                            scen_hor_dic[scen + '_' + hor][spatial_unit][indic] = value

                        # Special case: single scenario and horizon
                        if scen == 'single' and hor == 'single':
                            scen_hor_dic[scen + '_' + hor][spatial_unit][indic] = value

    return scen_hor_dic

def quantitative_aggregation_(dic,keys,new_field,formula,pond_list):
    """
    Performs quantitative aggregation on a given dictionary of spatial units. 
    Allows operations such as mean, geometric mean, maximum, weighted mean, 
    and weighted geometric mean to compute a new field based on the specified formula.

    :param dic: The dictionary containing spatial units with associated values to be aggregated.
    :type dic: dict
    :param keys: The keys within each spatial unit's dictionary whose values will be aggregated.
    :type keys: list of str
    :param new_field: is The name of the new field to store the resulting aggregated value.
    :type new_field: str
    :param formula: The aggregation formula to use. Options include 'mean', 'geom_mean', 'max', 
        'pond_mean', and 'pond_geom_mean'.
    :type formula: str
    :param pond_list: A list of weights corresponding to the keys provided, used for weighted
        means and geometric means. This parameter is ignored for other formulas.
    :type pond_list: list of float

    :return: None
        The input dictionary is modified in place, where each spatial unit's dictionary will
        have a new field with the aggregated value.
    """
    # Iterate over each spatial unit in the dictionary
    for spatial_unit_dic in dic.values():
        # Extract values corresponding to the specified keys for this unit
        values = [spatial_unit_dic[key] for key in keys]
        
        if formula=='mean':
            # Calculation of simple arithmetic mean
            spatial_unit_dic[new_field] = round(
                stats.mean(values))
        elif formula=='geom_mean':
            # Calculation of geometric mean
            spatial_unit_dic[new_field] = round(stats.geometric_mean(values))
        elif formula=='max':
            # Selection of the maximum value among the indicators
            spatial_unit_dic[new_field] = max(values)
        elif formula == 'pond_mean':
            # Calculation of weighted arithmetic mean using numpy
            spatial_unit_dic[new_field] = round(
                np.average(values,weights=pond_list))
        elif formula == 'pond_geom_mean':
            # Calculation of weighted geometric mean: 
            # (x1^w1 * x2^w2 * ... * xn^wn) ^ (1 / sum(weights))
            pond_product = 1
            weights_sum = sum(pond_list)
            for x, w in zip(values, pond_list):
                pond_product *= x ** w
            spatial_unit_dic[new_field] = round(pond_product ** (1 / weights_sum))

def qualitative_aggregation_(dic,agg_fields,new_field,value_scale,combination_matrix):
    """
    Aggregates qualitative data fields into a new field by applying a mapping matrix
    based on specified value scales.

    This function is designed to process data within a dictionary structure, using
    specific qualitative fields and mapping their combinations via a combination
    matrix. A new qualitative field is computed and added to the data structure
    based on the specified value scale and combination matrix.

    :param dic: Dictionary containing the data to be processed. Each key corresponds 
        to a spatial unit, and the value is another dictionary containing the fields 
        to be aggregated.
    :type dic: dict
    :param agg_fields: List of fields in the dictionary to be aggregated. The values 
        of these fields will be used to look up the combination matrix.
    :type agg_fields: list
    :param new_field: Name of the new field to be added to each spatial unit, which 
        will store the aggregated result.
    :type new_field: str
    :param value_scale: Dictionary mapping qualitative values to their respective 
        ranks. This scale is used for facilitating the calculations.
    :type value_scale: dict
    :param combination_matrix: Dictionary representing a combination matrix. Keys 
        are tuples of value ranks (according to the value scale), and values are the 
        resulting ranks to be converted back to qualitative values.
    :type combination_matrix: dict
    :return: None
    :rtype: NoneType
    """
    # Convert the value scale into a reverse dictionary for easier lookup (rank -> label)
    values_corr_dic={}
    for i in value_scale:
        values_corr_dic[value_scale[i]]=i

    # Iterate over each spatial unit in the dictionary to perform aggregation
    for spatial_unit in dic.values():

        # Map current qualitative field values to their corresponding ranks
        value_coords = [values_corr_dic[spatial_unit[field]] for field in agg_fields]
        
        # Retrieve the new rank from the combination matrix and map it back to a qualitative label
        spatial_unit[new_field]=value_scale[combination_matrix[tuple(value_coords)]]

def normalization_tool(dic, normalization_scale):
    """
    Apply normalization to indicator values based on predefined thresholds.

    This function assigns each value in the input dictionary to a category
    defined in a normalization scale. The scale is retrieved dynamically
    from a module containing normalization dictionaries.

    Parameters
    ----------
    dic : dict
        Dictionary where keys are spatial units and values are numeric
        indicator values. This dictionary is modified in place.
    normalization_scale : str
        Name of the normalization scale to use. This must correspond to
        an attribute in the 'norm_scales_dics' module.

    Returns
    -------
    None
        The input dictionary is updated in place with normalized category values.

    Notes
    -----
    - Categories are assigned based on threshold comparisons.
    - Assumes thresholds are ordered from lowest to highest.
    - If a value exceeds all thresholds, it is assigned to the highest category + 1.
    """
    # Retrieve the normalization scale dictionary dynamically
    normalization_scale_dic = getattr(norm_scales_dics, normalization_scale)

    # Extract category keys (assumed ordered)
    normalization_scale_categories = list(normalization_scale_dic.keys())

    # Iterate over each spatial unit and its indicator value
    for spatial_unit, ind_value in dic.items():
        assigned = False
        counter = 0

        # Iterate through categories until a matching threshold is found
        while not assigned and counter < len(normalization_scale_categories):
            # Check if the value is below the current category threshold
            if ind_value < normalization_scale_dic[normalization_scale_categories[counter]]:
                # Assign a category to the spatial unit
                dic[spatial_unit] = normalization_scale_categories[counter]
                assigned = True
            counter += 1

        # If no category was assigned, assign the highest category + 1
        if not assigned:
            dic[spatial_unit] = normalization_scale_categories[counter - 1] + 1

def present_comp_tool(present_dic, zonal_stats_dic, present_comp):
    """
    Computes and updates zonal statistical values based on a specified comparison type relative to
    present data. The function modifies the `zonal_stats_dic` dictionary in place based on the
    provided `present_dic` values and the selected `present_comp` method option. 

    :param present_dic: Dictionary containing reference present values for comparison.
        Keys represent data identifiers, and values are numerical data to compare against.
    :type present_dic: dict

    :param zonal_stats_dic: Dictionary containing zonal statistical values to be compared
        and updated. Keys represent data identifiers matching those in `present_dic`,
        and values are numerical data to be modified.
    :type zonal_stats_dic: dict

    :param present_comp: String specifying the type of comparison to apply. Supported
        options are:
        - 'relative differences to variation %': Computes the percentage of the future value 
          relative to the present (Future / Present * 100).
        - 'abs to variation %': Computes the percentage variation or relative change 
          ((Future - Present) / Present * 100).
        - 'abs to relative differences': Computes the absolute difference 
          (Future - Present).
    :type present_comp: str

    :return: None. The function modifies `zonal_stats_dic` directly.
    :rtype: None
    """
    # Iterate over each key in the zonal statistics dictionary to compare with present data
    for key in zonal_stats_dic.keys():

        if present_comp == 'relative differences to variation %':
            # Percentage of the future value relative to the present
            zonal_stats_dic[key] = zonal_stats_dic[key] * 100 / present_dic[key]
        elif present_comp == 'abs to variation %':
            # Percentage variation (relative change) from the present value
            zonal_stats_dic[key] = (zonal_stats_dic[key]-present_dic[key]) * 100 / present_dic[key]
        elif present_comp == 'abs to relative differences':
            # Absolute difference compared to the present value
            zonal_stats_dic[key] = zonal_stats_dic[key] - present_dic[key]
