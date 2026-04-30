from ihrat.src.tools import outputs
import tools
from ihrat.src.tools import input_reading
import copy

def components_dic_creation(dic_exp=None,dic_haz=None,dic_vuln=None,
                            exp_file=None,haz_file=None,vuln_file=None,scen_hor_fields=None,geo_dic=None,
                            geo_data_polygon_id_field=None
):
    """
    Creates a consolidated dictionary by merging multiple component dictionaries (Exposure, Hazard, Vulnerability).
    If any component dictionary is not provided, it reads the data from external files using the specified
    filenames and folder structures.

    The function merges these dictionaries by deep-copying the largest one as the base structure and
    subsequently updating it with the contents of the others, ensuring alignment of keys and subkeys
    representing scenarios and horizons.

    :param dic_exp: Optional. Pre-existing dictionary containing exposure data.
    :type dic_exp: dict or None
    :param dic_haz: Optional. Pre-existing dictionary containing hazard data.
    :type dic_haz: dict or None
    :param dic_vuln: Optional. Pre-existing dictionary containing vulnerability data.
    :type dic_vuln: dict or None
    :param exp_file: Optional. Filename of the external exposure data (CSV/SHP).
    :type exp_file: str or None
    :param haz_file: Optional. Filename of the external hazard data (CSV/SHP).
    :type haz_file: str or None
    :param vuln_file: Optional. Filename of the external vulnerability data (CSV/SHP).
    :type vuln_file: str or None
    :param scen_hor_fields: Fields defining scenario-horizon grouping for rearranging dictionaries.
    :type scen_hor_fields: dict
    :param geo_dic: Geographic dictionary template required for reading external CSV files.
    :type geo_dic: dict
    :param geo_data_polygon_id_field: The field name in the geospatial file is used to identify
        individual polygons for external input additions.
    :type geo_data_polygon_id_field: str or None
    :return: A consolidated dictionary merging all risk components across scenarios and horizons.
    :rtype: dict
    """
    # Load Exposure data if not provided
    if dic_exp is None:
        dic_exp={}
        comp_folder = 'exp_input_data'
        dic_exp['EXPOSURE'] = input_reading.reading_external_files(exp_file, comp_folder,geo_data_polygon_id_field, geo_dic)
        dic_exp = tools.rearranging_dics(dic_exp, scen_hor_fields)

    # Load Hazard data if not provided
    if dic_haz is None:
        dic_haz={}
        comp_folder = 'haz_input_data'
        dic_haz['HAZARD'] = input_reading.reading_external_files(haz_file, comp_folder,geo_data_polygon_id_field, geo_dic)
        dic_haz = tools.rearranging_dics(dic_haz, scen_hor_fields)

    # Load Vulnerability data if not provided
    if dic_vuln is None:
        dic_vuln={}
        comp_folder = 'vuln_input_data'
        dic_vuln['VULNERABILITY'] = input_reading.reading_external_files(vuln_file, comp_folder,geo_data_polygon_id_field, geo_dic)
        dic_vuln = tools.rearranging_dics(dic_vuln, scen_hor_fields)

    # Identify the base structure (biggest dictionary) to ensure all keys are preserved
    dics=[dic_exp,dic_haz,dic_vuln]
    biggest_dic = max(dics, key=lambda s: len(s))
    scen_hor_dic = copy.deepcopy(biggest_dic)

    # Merge remaining dictionaries into the base structure
    for d in dics:
        if d is biggest_dic:
            continue
        # If the dictionary has only one main key (component), distribute its subkeys
        if len(d) == 1:
            # Get the single subdictionary
            only_dic = d[list(d.keys())[0]]

            # Iterate through all scenario/horizon subdictionaries of the base
            for subkey, subdic in scen_hor_dic.items():
                # Update base subdictionaries with the corresponding data
                for key, only_dic_subdic in only_dic.items():
                    subdic[key].update(only_dic_subdic)
        else:
            # Multi-component merge: iterate and update matching sub-structures
            for sub_key, subdic in d.items():
                # Merge sub-subdictionaries (polygons/results) into the corresponding scenario
                for subsub_key, subsub_val in subdic.items():
                        scen_hor_dic[sub_key][subsub_key].update(subsub_val)

    return scen_hor_dic

def components_agg_and_outputs(
        type_of_data,
        agg_extras,
        geo_data_polygon_id_field,
        main_dic,
        crs=None):
    """
    Computes the final Risk aggregation by combining Hazard, Exposure, and Vulnerability components
    and exports the results to CSV and Shapefile formats for each scenario.

    :param type_of_data: Specifies whether the analysis is 'qualitative' or 'quantitative'.
    :type type_of_data: str
    :param agg_extras: Dictionary containing aggregation parameters (scales, matrices, formulas, weights).
    :type agg_extras: dict
    :param geo_data_polygon_id_field: Field name used to identify unique polygons in outputs.
    :type geo_data_polygon_id_field: str
    :param main_dic: Consolidated dictionary containing all component data per scenario.
    :type main_dic: dict
    :param crs: Coordinate Reference System for spatial outputs (Shapefiles).
    :type crs: str or None
    :return: None
    """

    # Iterate through each scenario/horizon in the main dictionary
    for key, dic in main_dic.items():
        # Perform qualitative aggregation (matrix-based)
        if type_of_data == 'qualitative':
            tools.qualitative_aggregation_(
                dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK',
                agg_extras['value scale'], agg_extras['combination matrix']
            )
        # Perform quantitative aggregation (formula-based)
        elif type_of_data == 'quantitative':
            tools.quantitative_aggregation_(
                dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK',
                agg_extras['formula'], agg_extras['pond weights']
            )

        # Export results to a simple CSV table
        outputs.simple_csv_output(key, geo_data_polygon_id_field, dic)

        # Export results to a Shapefile including polygonal geometry
        outputs.simple_shapefile_output(key, geo_data_polygon_id_field, dic, crs)






