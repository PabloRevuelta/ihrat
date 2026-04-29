from ihrat.src.tools import input_reading
from ihrat.src.tools import compute_zonal_stats

import tools
import copy
import pandas as pd

def indicators_computation(risk_component, comp_indics_main_dic, geo_dic, geo_data_file_path, geo_data_polygon_id_field):
    """
    Compute the defined indicators for a given risk component by processing input data,
    performing zonal statistics, implementing comparisons, and applying normalization.

    :param risk_component: Determines the risk component being analyzed; expected values are
        'EXPOSURE', 'HAZARD', or 'VULNERABILITY'.
    :type risk_component: str
    :param comp_indics_main_dic: Dictionary defining the main parameters, configurations,
        and files associated with each indicator. Each indicator is represented as a key in the dictionary,
        mapped to its individual configuration sub-dictionary.
    :type comp_indics_main_dic: dict
    :param geo_dic: Geographic data structure that will be used to initialize the
        computation for each indicator. The final computed values are appended to this dictionary.
    :type geo_dic: dict
    :param geo_data_file_path: Path to the file containing geographic data (e.g., shapefiles,
        rasters, or CSVs) that supports zonal statistics computation.
    :type geo_data_file_path: str
    :param geo_data_polygon_id_field: Field within the geographic data that uniquely identifies
        polygons (e.g., ID or name). This is required to aggregate statistics.
    :type geo_data_polygon_id_field: str
    :return: The method does not return any value but updates the `comp_indics_main_dic`
        in-place by embedding computed indicator statistics within corresponding dictionaries.
    :rtype: None
    """
    # Determine the folder corresponding to the selected risk component
    if risk_component == 'EXPOSURE':
        comp_folder = 'exp_input_data'
    elif risk_component == 'HAZARD':
        comp_folder = 'haz_input_data'
    elif risk_component == 'VULNERABILITY':
        comp_folder = 'vuln_input_data'

    # Iterate over each indicator definition
    for indicator, indicator_indiv_dic in comp_indics_main_dic.items():
        # Build a full folder path for the indicator
        folder = comp_folder + '//' + indicator_indiv_dic['folder']

        # Read input files (shapefile, raster, CSV, etc.)
        indicator_indiv_dic['files'] = input_reading.reading_files(
            folder, ('.shp', '.tiff', '.tif', '.csv')
        )

        # Initialize the result dictionary using geographic structure
        indicator_indiv_dic['dic'] = copy.deepcopy(geo_dic)

        # Check if a present comparison is required
        present_comp = indicator_indiv_dic['present comparisons']
        if present_comp:
            present_dic = {}

        # Process each data file associated with the indicator
        for data_file, data_file_info_dic in indicator_indiv_dic['files'].items():

            # Compute zonal statistics for spatial data (raster/vector)
            zonal_stats_dic = zonal_stats_obtention(
                indicator_indiv_dic,
                data_file_info_dic,
                geo_data_file_path,
                geo_data_polygon_id_field
            )

            # Apply the present comparison if enabled
            if present_comp:
                if data_file == indicator_indiv_dic['present file']:
                    # Store reference (present) data
                    present_dic = zonal_stats_dic
                else:
                    # Compare current data against present scenario
                    tools.present_comp_tool(present_dic, zonal_stats_dic, present_comp)

            # Apply normalization if required
            norm_scale = indicator_indiv_dic['norm_scale']
            if norm_scale:
                # Skip normalization for the present file when comparison is active
                if present_comp and data_file == indicator_indiv_dic['present file']:
                    pass
                else:
                    tools.normalization_tool(zonal_stats_dic, norm_scale)

            # Store computed values in the indicator dictionary per polygon
            for polygon, value in zonal_stats_dic.items():
                indicator_indiv_dic['dic'][polygon][data_file] = value

def zonal_stats_obtention(indicator_indiv_dic, data_file_info_dic, geo_data_file_path, geo_data_polygon_id_field):
    """
    Compute zonal statistics based on given geospatial and input data.

    This function determines the appropriate statistical operation (e.g., mean, max, sum) and the
    pixel inclusion method (e.g., considering only centers or all touched pixels) based on the input parameters.
    It computes zonal statistics for raster-based (.tif, .tiff), vector-based (.shp), or tabular-based (.csv) data.

    :param indicator_indiv_dic: Dictionary specifying the method and associated parameters for zonal
        statistics computation, including the statistical operation and attribute field.
    :type indicator_indiv_dic: dict
    :param data_file_info_dic: Dictionary containing information about the input data file, such as
        file extension and path.
    :type data_file_info_dic: dict
    :param geo_data_file_path: Path to the geospatial file (e.g., shapefile) that contains the
        polygons for which zonal statistics are computed.
    :type geo_data_file_path: str
    :param geo_data_polygon_id_field: The field name in the geospatial file is used to identify
        individual polygons for statistical computation.
    :type geo_data_polygon_id_field: str
    :return: A dictionary containing the computed zonal statistics for each polygon identified
        in the geospatial file.
    :rtype: dict
    """


    # Extract method and file information
    method = indicator_indiv_dic['method']
    data_file_type = data_file_info_dic['extension']
    data_file = data_file_info_dic['path']

    # Determine the statistical operation (mean, max, sum)
    if method in ['zonal average centers', 'zonal average all touched']:
        zonal_stats_value = 'mean'
    elif method in ['zonal max centers', 'zonal max all touched']:
        zonal_stats_value = 'max'
    elif method in ['zonal total addition centers', 'zonal total addition all touched']:
        zonal_stats_value = 'sum'

    # Determine the pixel inclusion method
    if method in ['zonal average centers', 'zonal max centers', 'zonal total addition centers']:
        zonal_stats_method = 'centers'
    elif method in ['zonal average all touched', 'zonal max all touched', 'zonal total addition all touched']:
        zonal_stats_method = 'all touched'

    # Apply zonal statistics depending on the input data type
    if data_file_type == '.tif' or data_file_type == '.tiff':
        # Raster-based zonal statistics
        indicator_dic = compute_zonal_stats.shape_raster_zonal_stats(
            geo_data_file_path,
            data_file,
            geo_data_polygon_id_field,
            zonal_stats_method,
            zonal_stats_value
        )

    elif data_file_type == '.shp':
        # Vector-based zonal statistics (using the attribute field)
        indicator_dic = compute_zonal_stats.shape_shape_zonal_stats(
            geo_data_file_path,
            data_file,
            geo_data_polygon_id_field,
            indicator_indiv_dic['shp data field name'],
            zonal_stats_value
        )
    elif data_file_type == '.csv':
        # Read CSV with specific delimiter and encoding
        df = pd.read_csv(data_file_info_dic['path'], sep=";", encoding="latin-1")
        # Convert attribute column to numeric values
        df[indicator_indiv_dic['attribute key']] = pd.to_numeric(
            df[indicator_indiv_dic['attribute key']], errors="coerce"
        )
        polygon_values = df.groupby(geo_data_polygon_id_field)[
            indicator_indiv_dic['attribute key']
        ].agg(zonal_stats_value)

        # Convert result to dictionary
        indicator_dic = polygon_values.to_dict()



    return indicator_dic