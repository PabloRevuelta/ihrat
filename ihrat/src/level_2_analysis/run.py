import components_aggregation as comp_agg
import indicators_aggregation as ind_agg
import indicators_obtention as ind_obt

from ihrat.src.tools import input_reading

if __name__ == "__main__":

    # =========================================================================
    # LEVEL 2: RISK ANALYSIS BY INDICATORS
    # =========================================================================

    # =========================================================================
    # STAGE 1: Indicators Obtention (ind_obt.indicators_computation)
    # -------------------------------------------------------------------------
    # Processes individual files to compute zonal statistics, 
    # comparisons with the base scenario (present), and normalization, if needed in both cases.
    #
    # Parameters for indicator dictionaries (Exp, Haz, Vuln):
    # - 'folder': Subfolder within 'inputs/[component]_input_data/'.
    # - 'method': Zonal statistics method.
    # - 'data field name': (Only for .shp or .csv) Name of the field/column with the numeric value.
    # - 'norm_scale': Normalization scale, if required (defined in norm_scales_dic).
    # - 'present comparisons': Type of difference calculation relative to the present, if required.
    # - 'present file': File name (without extension) used as the present base, if required.
    #
    # INPUT FILE FORMAT:
    # - Raster (.tif/.tiff): Pixel values represent the size of the indicator.
    # - Vector (.shp): Must contain a numeric attribute defined in 'data field name'.
    # - Tabular (.csv): Semicolon-separated (";") with 'latin-1' encoding. Must include
    #   the 'data field name' and 'geo_data_polygon_id_field' columns for spatial linking of each column to a zone.
    #
    # PARAMETERS EXPLANATION
    #
    # 1. Available methods for the 'method' field in indicator dictionaries:
    # - 'zonal average centers': Average value of pixels whose centers fall within the polygon.
    # - 'zonal max centers': Maximum value of pixels whose centers fall within the polygon.
    # - 'zonal total addition centers': Sum of pixels whose centers fall within the polygon.
    # - 'zonal average all touched': Average of all pixels touched by the polygon.
    # - 'zonal max all touched': Maximum of all pixels touched by the polygon.
    # - 'zonal total addition all touched': Sum of all pixels touched by the polygon.
    # - 'zonal average index': Specifically for tabular data (CSV), computes the mean of an attribute.
    #
    # If the input is a shapefile or a csv, only the calculation of average, max, or total addition matters.
    #
    # 2. Available 'present comparisons' types:
    # - 'abs to relative differences': Computes (Future - Present).
    # - 'abs to variation %': Computes ((Future - Present) / Present) * 100.
    # - 'relative differences to variation %': Computes variation % based on relative differences.
    # =========================================================================

    # Define the unique ID field for polygons in the spatial distribution layer
    geo_data_polygon_id_field = 'subarea_fu'
    # Read the base spatial distribution shapefile and create a geographic dictionary (geo_dic)
    (geo_dic, crs), geo_data_file_path = input_reading.reading_shp_to_dic(
        'spatial_distribution_input',
        [geo_data_polygon_id_field])

    # 1.1 Compute Exposure
    exp_indics_main_dic = {
        'Population': {
            'folder': '',
            'data field name': 'field name',
            'method': 'zonal total addition centers',
            "norm_scale": 'norm_scale_2',
            'present comparisons': None
        },
    }
    ind_obt.indicators_computation('EXPOSURE',exp_indics_main_dic,geo_dic,geo_data_file_path,geo_data_polygon_id_field)

    # 1.2 Compute Hazard

    haz_indics_main_dic = {
        'Precipitation': {
            'folder': 'pr',
            'data field name': 'field name',
            'method': 'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons': 'relative differences to variation %',
            'present file': 'AEMET-REJILLA-spain-historical-pr'
        },
        '24h max precipitation': {
            'folder': 'prMax24h',
            'data field name': 'field name',
            'method': 'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons': 'relative differences to variation %',
            'present file': 'AEMET-REJILLA-spain-historical-prMax24h'
        },
        'Mean Temperature': {
            'folder': 'tmean',
            'data field name': 'field name',
            'method': 'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons': 'relative differences to variation %',
            'present file': 'AEMET-REJILLA-spain-historical-tmean'
        },
        'Hot days number': {
            'folder': 'tasmaxNap90',
            'data field name': 'field name',
            'method': 'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons': 'relative differences to variation %',
            'present file': 'AEMET-REJILLA-spain-historical-tasmaxNap90'
        }
    }
    ind_obt.indicators_computation('HAZARD',haz_indics_main_dic,geo_dic,geo_data_file_path,geo_data_polygon_id_field)

    # 1.3 Compute Vulnerability
    vuln_indics_main_dic = {
        'Average household income level': {
            'folder': '',
            'data field name': 'Total',
            'method': 'zonal average index',
            "norm_scale": 'norm_scale_3',
            'present comparisons': None
        }
    }
    ind_obt.indicators_computation('VULNERABILITY',vuln_indics_main_dic,geo_dic,geo_data_file_path,geo_data_polygon_id_field)

    # =========================================================================
    # STAGE 2: Indicators Aggregation (ind_agg.indicator_agg)
    # -------------------------------------------------------------------------
    # Groups processed indicators into scenarios and time horizons.
    # Parameters:
    # - 'type_of_data': 'quantitative' (uses formulas) or 'qualitative' (uses matrices).
    # - 'scenarios' / 'horizons': Lists defining how files are grouped.
    #   File names must contain these tags (e.g., "ssp245_2050_pr.tif").
    # - Parameters in 'agg_extras' (4th argument):
    #     - For 'quantitative':
    #         - 'formula': 'mean', 'max', 'sum' to combine indicators.
    #         - 'pond weights': Weights to weight indicators (None for equal weights).
    #     - For 'qualitative':
    #         - 'value scale': List of labels (e.g., ['low', 'medium', 'high']).
    #         - 'combination matrix': Matrix (numpy array) defining the combination result.
    #
    # EXTERNAL FILES:
    # It is possible to add indicators directly from files (.csv or .shp) without going through Stage 1.
    # - 'external_data_entry_filenames': List of file names (with extension) in the component's folder.
    # - 'geo_dic': Required if external .csv files are loaded to map data to geometry.
    # - 'geo_data_polygon_id_field': Field name serving as ID to link external data.
    # Example: ind_agg.indicator_agg(..., external_data_entry_filenames=['ext_ind.csv'], geo_dic=geo_dic, geo_data_polygon_id_field=geo_data_polygon_id_field)
    #
    # EXTERNAL FILES FORMAT:
    # - Shapefile (.shp): Must be in the 'inputs/[component]_input_data/' folder. 
    #   MUST contain a column whose name matches 'geo_data_polygon_id_field' for linking.
    #   Other numeric columns will be treated as indicators.
    # - CSV (.csv): Must be in the 'inputs/[component]_input_data/' folder.
    #   Encoding: UTF-8 recommended. Delimiter: ','.
    #   The FIRST column must contain the IDs (matching those of the base geometry).
    #   Other columns must be numeric (indicator values).
    # =========================================================================

    # Qualitative configuration example:
    """
    exp_indics_main_dic = ind_agg.indicator_agg(
        'EXPOSURE',
        'qualitative',
        {'scenarios':['single'], 'horizons':['single']},
        {
            'value scale': ['low', 'medium', 'high'],
            'combination matrix': np.array([
                [[0, 0, 1], [0, 1, 1], [1, 1, 2]],
                [[0, 1, 1], [1, 1, 2], [1, 2, 2]],
                [[1, 1, 2], [1, 2, 2], [2, 2, 2]]
            ])
        },
        indic_main_dic=exp_indics_main_dic,
        geo_data_polygon_id_field=geo_data_polygon_id_field
    )
    """

    # Aggregate Exposure (usually single scenario/horizon)
    exp_indics_main_dic = ind_agg.indicator_agg(
        'EXPOSURE',
        'quantitative',
        {'scenarios': ['single'],'horizons': ['single']},
        {'formula': 'mean','pond weights': None},
        indic_main_dic=exp_indics_main_dic,
        geo_data_polygon_id_field=geo_data_polygon_id_field
    )

    # Aggregate Hazard (multiple scenarios and horizons)
    haz_indics_main_dic = ind_agg.indicator_agg(
        'HAZARD',
        'quantitative',
        {'scenarios': ['ssp245', 'ssp585'],'horizons': ['70', '100']},
        {'formula': 'mean','pond weights': None},
        indic_main_dic=haz_indics_main_dic,
        geo_data_polygon_id_field=geo_data_polygon_id_field
    )

    # Aggregate Vulnerability
    vuln_indics_main_dic = ind_agg.indicator_agg(
        'VULNERABILITY',
        'quantitative',
        {'scenarios': ['single'],'horizons': ['single']},
        {'formula': 'mean','pond weights': None},
        indic_main_dic=vuln_indics_main_dic,
        geo_data_polygon_id_field=geo_data_polygon_id_field
    )
    # =========================================================================
    # STAGE 3: Components Consolidation (comp_agg.components_dic_creation)
    # -------------------------------------------------------------------------
    # Merges Exposure, Hazard, and Vulnerability dictionaries 
    # into a single structure indexed by scenario and horizon.
    #
    # EXTERNAL FILES IN STAGE 3:
    # If some dictionaries were not computed in previous stages, they can be loaded directly:
    # - 'exp_file' / 'haz_file' / 'vuln_file': External file names for each component.
    # - 'scen_hor_fields': Scenario/horizon structure to organize external data.
    # - 'geo_dic' / 'geo_data_polygon_id_field': Required for spatial linking (same as in Stage 2).
    #
    # Example usage with external files:
    # main_dic = comp_agg.components_dic_creation(
    #     exp_file='ext_exp.csv', haz_file='ext_haz.shp', scen_hor_fields={'scenarios':['ssp245'],'horizons':['present']},
    #     geo_dic=geo_dic, geo_data_polygon_id_field=geo_data_polygon_id_field
    # )
    # =========================================================================

    main_dic=comp_agg.components_dic_creation(
        exp_indics_main_dic,
        haz_indics_main_dic,
        vuln_indics_main_dic
    )

    # =========================================================================
    # STAGE 4: Final Risk and Outputs (comp_agg.components_agg_and_outputs)
    # -------------------------------------------------------------------------
    # Calculates the final RISK indicator by combining the 3 components (E, H, V)
    # and generates final results.
    #
    # Parameters:
    # - 'formula' / 'pond weights': Same as in Stage 2, for E-H-V combination.
    #
    # OUTPUT FORMAT:
    # - .csv: Results table by territorial unit.
    # - .shp: Geographic layer with all indicators and final risk.
    # =========================================================================

    comp_agg.components_agg_and_outputs(
        'quantitative',
        {'formula':'mean','pond weights':None},
        geo_data_polygon_id_field,
        main_dic,
        crs=crs
    )


