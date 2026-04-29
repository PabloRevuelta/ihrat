import components_aggregation as comp_agg
import indicators_aggregation as ind_agg
import indicators_obtention as ind_obt

from ihrat.src.tools import input_reading

if __name__ == "__main__":

    # =========================================================================
    # GLOBAL CONFIGURATION AND PARAMETERS EXPLANATION
    # =========================================================================
    
    # 1. Available methods for 'method' field in indicator dictionaries:
    # - 'zonal average centers': Average value of pixels whose centers fall within the polygon.
    # - 'zonal max centers': Maximum value of pixels whose centers fall within the polygon.
    # - 'zonal total addition centers': Sum of pixels whose centers fall within the polygon.
    # - 'zonal average all touched': Average of all pixels touched by the polygon.
    # - 'zonal max all touched': Maximum of all pixels touched by the polygon.
    # - 'zonal total addition all touched': Sum of all pixels touched by the polygon.
    # - 'zonal average index': Specifically for tabular data (CSV), computes the mean of an attribute.

    # 2. Available 'present comparisons' types:
    # - None: No comparison with present/baseline scenario.
    # - 'abs to relative differences': Computes (Future - Present).
    # - 'abs to variation %': Computes ((Future - Present) / Present) * 100.
    # - 'relative differences to variation %': Computes variation % based on relative differences.

    # 3. Normalization scales ('norm_scale'):
    # - References to predefined scales in tools.normalization_tool (e.g., 'norm_scale_1', 'norm_scale_2').
    # =========================================================================

    # --- Exposure Indicators Definition ---
    # folder: Subfolder inside 'inputs/exp_input_data'
    # method: Zonal statistics method to apply
    # norm_scale: Normalization rule for the resulting values
    exp_indics_main_dic={
        'Population':{
            'folder':'',
            'shp data field name':'field name',
            'method':'zonal total addition centers',
            "norm_scale": 'norm_scale_2',
            'present comparisons':None
        },
    }
    # --- Hazard Indicators Definition ---
    # present comparisons: Type of comparison against a baseline file
    # present file: The filename (without extension) used as the baseline for comparisons
    haz_indics_main_dic = {
        'Precipitation':{
            'folder':'pr',
            'shp data field name':'field name',
            'method':'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons':'relative differences to variation %',
            'present file':'AEMET-REJILLA-spain-historical-pr'
        },
        '24h max precipitation':{
            'folder':'prMax24h',
            'shp data field name':'field name',
            'method':'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons':'relative differences to variation %',
            'present file':'AEMET-REJILLA-spain-historical-prMax24h'
        },
        'Mean Temperature':{
            'folder':'tmean',
            'shp data field name':'field name',
            'method':'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons':'relative differences to variation %',
            'present file':'AEMET-REJILLA-spain-historical-tmean'
        },
        'Hot days number':{
            'folder':'tasmaxNap90',
            'shp data field name':'field name',
            'method':'zonal average centers',
            "norm_scale": 'norm_scale_1',
            'present comparisons':'relative differences to variation %',
            'present file':'AEMET-REJILLA-spain-historical-tasmaxNap90'
        }
    }
    # --- Vulnerability Indicators Definition ---
    # attribute key: The column name in the CSV file containing the data
    vuln_indics_main_dic = {
        'Nivel medio de renta por hogar':{
            'folder':'',
            'shp data field name':'field name',
            'method':'zonal average index',
            'attribute key':'Total',
            "norm_scale": 'norm_scale_3',
            'present comparisons':None
        }
    }

    # Define the unique ID field for polygons in the spatial distribution layer
    geo_data_polygon_id_field = 'subarea_fu'
    
    # Read the base spatial distribution shapefile and create a geographic dictionary (geo_dic)
    (geo_dic, crs), geo_data_file_path = input_reading.reading_shp_to_dic(
        'spatial_distribution_input',
        [geo_data_polygon_id_field]
    )

    # --- STEP 1: Compute Indicators ---
    # This processes all files in the respective folders, computes zonal stats, 
    # applies comparisons if defined, and normalizes the results.
    
    # Compute Exposure
    ind_obt.indicators_computation(
        'EXPOSURE',
        exp_indics_main_dic,
        geo_dic,
        geo_data_file_path,
        geo_data_polygon_id_field
    )
    # Compute Hazard
    ind_obt.indicators_computation(
        'HAZARD',
        haz_indics_main_dic,
        geo_dic,
        geo_data_file_path,
        geo_data_polygon_id_field
    )
    # Compute Vulnerability
    ind_obt.indicators_computation(
        'VULNERABILITY',
        vuln_indics_main_dic,
        geo_dic,
        geo_data_file_path,
        geo_data_polygon_id_field
    )

    # --- STEP 2: Aggregate Indicators into Scenarios and Horizons ---
    # This step groups individual indicator files into scenarios (e.g., ssp245) 
    # and horizons (e.g., 2050, 2100) and computes a weighted or unweighted aggregation.
    
    # Example for Qualitative configuration:
    """
    if type_of_data=='qualitative':
                agg_extras['value scale']=['low', 'medium', 'high']
                agg_extras['combination matrix']=np.array([
                    [[0, 0, 1], [0, 1, 1], [1, 1, 2]],
                    [[0, 1, 1], [1, 1, 2], [1, 2, 2]],
                    [[1, 1, 2], [1, 2, 2], [2, 2, 2]]
    """

    # Aggregate Exposure (usually single scenario/horizon)
    exp_indics_main_dic=ind_agg.indicator_agg(
        'EXPOSURE',
        'quantitative',
        {
            'scenarios':['single'],
            'horizons':['single']
        },
        {
            'formula':'mean',
            'pond weights':None
        },
        indic_main_dic=exp_indics_main_dic,
    )
    
    # Aggregate Hazard (multiple scenarios and horizons)
    haz_indics_main_dic=ind_agg.indicator_agg(
        'HAZARD',
        'quantitative',
        {
            'scenarios':['ssp245','ssp585'],
            'horizons':['70','100']
        },
        {
            'formula':'mean',
            'pond weights':None
        },
        indic_main_dic=haz_indics_main_dic,
    )
    
    # Aggregate Vulnerability
    vuln_indics_main_dic=ind_agg.indicator_agg(
        'VULNERABILITY',
        'quantitative',
        {
            'scenarios':['single'],
            'horizons':['single']
        },
        {
            'formula':'mean',
            'pond weights':None
        },
        indic_main_dic=vuln_indics_main_dic,
    )

    # --- STEP 3: Create Consolidated Dictionary of Components ---
    # Merges Exposure, Hazard, and Vulnerability results into a single structure.
    main_dic=comp_agg.components_dic_creation(
        exp_indics_main_dic,
        haz_indics_main_dic,
        vuln_indics_main_dic
    )

    # --- STEP 4: Final Risk Aggregation and Output Generation ---
    # Combines the three components into a final RISK indicator and 
    # saves the results as CSV and Shapefiles.
    comp_agg.components_agg_and_outputs(
        'quantitative',
        {
            'formula':'mean',
            'pond weights':''
        },
        geo_data_polygon_id_field,
        main_dic,
        crs=crs
    )


