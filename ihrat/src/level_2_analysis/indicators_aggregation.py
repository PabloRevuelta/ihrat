import tools
from ihrat.src.tools import input_reading

def indicator_agg(
    risk_component,
    type_of_data,
    scen_hor_fields,
    agg_extras,
    indic_main_dic=None,
    geo_dic=None,
    external_data_entry_filenames=None
):
    """
    Aggregates data based on the specified risk component, type of data, and additional
    aggregation details. It processes input dictionaries organized by scenario-horizon fields and
    performs qualitative or quantitative aggregation depending on the data type.

    :param risk_component: The specific component of risk to aggregate in the data.
    :type risk_component: str
    :param type_of_data: Specifies the type of data to process; either 'qualitative' or 'quantitative'.
    :type type_of_data: str
    :param scen_hor_fields: Fields defining scenario-horizon grouping in the input data.
    :type scen_hor_fields: dict
    :param agg_extras: Parameters required for aggregation; can include value scales, combination
                       matrices for qualitative data, or formulas and weights for quantitative data.
    :type agg_extras: dict
    :param indic_main_dic: Optional. The main dictionary of indicators to process. If not provided,
                           it will be initialized as an empty dictionary and potentially populated
                           with external data.
    :type indic_main_dic: dict or None
    :param geo_dic: Optional. Dictionary with the geospatial data structure, used as a template
                     when external data in .csv format is being loaded.
    :type geo_dic: dict or None
    :param external_data_entry_filenames: Optional. List of filenames to be read as external
                                          indicator data from the corresponding risk component folder.
    :type external_data_entry_filenames: list of str or None
    :return: A dictionary rearranged according to scenario-horizon fields, containing aggregated
             results for each scenario.
    :rtype: dict
    """

    if indic_main_dic is None:
        indic_main_dic = {}
    if external_data_entry_filenames is not None:
        # Determine the folder corresponding to the selected risk component
        if risk_component == 'EXPOSURE':
            comp_folder = 'exp_input_data'
        elif risk_component == 'HAZARD':
            comp_folder = 'haz_input_data'
        elif risk_component == 'VULNERABILITY':
            comp_folder = 'vuln_input_data'
        for indic in external_data_entry_filenames:

            name = indic.split('.')[0]
            indic_indiv_dic=input_reading.reading_external_files(indic, comp_folder, geo_dic)
            
            # Store the individual indicator data in the main dictionary
            indic_main_dic[name] = indic_indiv_dic


    # Rearrange the input dictionary according to scenario-horizon fields
    scen_hor_dic = tools.rearranging_dics(indic_main_dic, scen_hor_fields)

    # Iterate over each scenario-horizon dictionary
    for dic in scen_hor_dic.values():
        # Extract indicator names (excluding geometry)
        values = list(next(iter(dic.values())).keys())
        values.remove('geometry')

        # Perform aggregation depending on data type
        if type_of_data == 'qualitative':
            tools.qualitative_aggregation_(
                dic,
                values,
                risk_component,
                agg_extras['value scale'],
                agg_extras['combination matrix']
            )

        elif type_of_data == 'quantitative':
            tools.quantitative_aggregation_(
                dic,
                values,
                risk_component,
                agg_extras['formula'],
                agg_extras['pond weights']
            )

    return scen_hor_dic
