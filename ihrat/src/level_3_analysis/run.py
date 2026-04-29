import level_3_analysis

if __name__ == "__main__":

    # =========================================================================================
    # 1. HAZARD_INPUT_DIC: Hazard indicators configuration
    # -----------------------------------------------------------------------------------------
    # - Each key (e.g., 'Flooding') defines a hazard.
    # - 'folder': Name of the subfolder within 'haz_input_data/' where files are located.
    # - 'extension': '.tif' for raster hazard maps or '.shp' for vector maps.
    # =========================================================================================
    hazard_input_dic = {
        'Flooding': {
            'folder': 'Escenarios',
            'extension': '.tif'
        }
    }

    # =========================================================================================
    # 2. PARAMS_DIC: Global execution configuration
    # -----------------------------------------------------------------------------------------
    # - 'scenarios': List of scenarios (e.g., ['RCP45', 'RCP85']). 
    #                Use [] if filenames do not depend on scenario.
    # - 'horizons': Time horizons (e.g., ['2030', '2050']). 
    #               Use [] if filenames do not depend on horizon.
    # - 'return periods': List of return periods (e.g., ['5', '10', '100']). 
    #                     Use [] if filenames do not depend on return period.
    # - The non-empty combination of the three above must match the file names.
    # - 'partial agg': Boolean (True/False). If True, generates results by territorial units
    #                  in addition to the global total.
    # - 'zonal stats method': (For .shp exposure only) 'centers' (uses pixel center) or 'all touched'.
    # - 'zonal stats value': (For .shp exposure only) Hazard statistic: 'mean' or 'max'.
    # =========================================================================================
    params_dic = {
        'scenarios': [],
        'horizons': [],
        'return periods': ['5'],
        'partial agg': True,
        'zonal stats method': 'centers',
        'zonal stats value': 'mean'
    }

    # =========================================================================================
    # 3. EXPOSURE_RASTER_INPUT_DIC: Metadata for RASTER (.tif) exposure systems
    # -----------------------------------------------------------------------------------------
    # - MANDATORY if you have .tif files in 'exp_input_data/'.
    # - The key must be the filename without the .tif extension.
    # - 'Type of system': Category (e.g., 'POP', 'AGR', 'ECO').
    # - 'Damage function': Name of the predefined damage function (e.g., 'pop_A').
    #                      Use 'file' to apply spatially variable functions defined 
    #                      in a shapefile inside 'inputs/dam_fun_files/'.
    # - 'Damage function file': (Optional) Name of the shapefile without extension,
    #                           required ONLY if 'Damage function' is set to 'file'.
    #                      For .shp exposure files, this is read from their own attributes.
    # =========================================================================================
    exposure_raster_input_dic = {
        'ury_ppp_2020_constrained': {
            'Type of system': 'POP',
            'Damage function': 'pop_A'
        }
    }

    # Execute Level 3 Analysis
    level_3_analysis.main(hazard_input_dic, params_dic, exposure_raster_input_dic)