import level_3_analysis
from ihrat.src.level_3_analysis.damage_functions.damage_functions import add_dam_fun

if __name__ == "__main__":

    # =========================================================================================
    # 1. HAZARD_INPUT_DIC: Hazard indicators configuration
    # -----------------------------------------------------------------------------------------
    # - Each key (e.g., 'Flooding') defines a hazard.
    # - 'folder': Name of the subfolder within 'haz_input_data/' where files are located.
    # - 'extension': '.tif' for raster hazard maps or '.shp' for vector maps.
    #
    # INPUT FILES FORMAT (Hazard):
    # - Raster (.tif): Pixel values represent the hazard magnitude (e.g., water depth).
    # - Vector (.shp): Must contain a numeric attribute representing the hazard magnitude.
    #   The attribute name must be defined in 'dictionaries.py' (default: 'IMP_VAL').
    #
    # FILENAME CONVENTION (for Hazard files):
    # - Files must be named as: "{scenario}_{horizon}_{return_period}.{extension}"
    # - If some lists are empty, those parts are omitted from the filename.
    # - If multiple hazards are used, the filenames must be the same for all of them
    #   but located in their respective folders.
    # - Example: if scenarios=['RCP45'] and return periods=['100'], filename: "RCP45_100.tif"
    #
    # - 'partial agg': Boolean (True/False). If True, generates results by territorial units
    #                  (e.g., municipalities) defined in 'inputs/adm_division/'.
    # - 'zonal stats method': (For .shp exposure only) 'centers' (uses pixel center) or 'all touched'.
    # - 'zonal stats value': (For .shp exposure only) Hazard statistic: 'mean' or 'max'.
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
    #                      Use 'file' to apply spatially variable functions.
    # - 'Damage function file': (Optional) Name of the shapefile without extension in 
    #                           'inputs/dam_fun_files/' if 'Damage function' is 'file'.
    #
    # INPUT FILES FORMAT (Exposure):
    # - Raster (.tif): Located in 'exp_input_data/'. Pixel values represent exposure 
    #   (e.g., population count, asset value).
    # - Vector (.shp): Located in 'exp_input_data/'. MUST have the following attributes:
    #     - 'BUILD_ID': Unique identifier for each element.
    #     - 'TYPE': Category of the element (e.g., 'RESIDENTIAL').
    #     - 'EXP_VALUE': Numeric value of the element (e.g., cost, people).
    #     - 'DAM_FUN': Name of the damage function to apply to this element.
    #     - 'DAM_FUN_F': (Optional) Filename for spatial damage functions.
    # =========================================================================================
    exposure_raster_input_dic = {
        'ury_ppp_2020_constrained': {
            'Type of system': 'POP',
            'Damage function': 'pop_A'
        }
    }

    # =========================================================================================
    # 4. ADDING DAMAGE FUNCTIONS TO THE LIBRARY (Optional)
    # -----------------------------------------------------------------------------------------
    # Damage functions are used to compute the damage fraction based on hazard impact values.
    # They are stored in 'damage_functions/damage_functions_dictionary.json'.
    #
    # You can add new functions by placing CSV files in 'inputs/dam_fun_files/'.
    # The 'add_dam_fun' function will read these CSVs and update the JSON dictionary.
    #
    # INPUT FILES FORMAT (Damage Functions .csv):
    # - A CSV file can contain one or more damage functions (one per row).
    # - Required columns:
    #     - 'name': Unique name of the damage function (e.g., 'residential_flood').
    #     - 'variables': Semicolon-separated variable names (e.g., 'x' or 'x;y').
    #     - 'values': Semicolon-separated output values (damage fraction, usually 0 to 1).
    #     - 'application': Type of application (e.g., 'Absolute', 'Relative').
    #     - 'type': Type of function (e.g., 'interpolation').
    #     - 'interpolation_type': Type of interpolation (e.g., 'linear').
    #     - '<variable_name>': For each variable in 'variables', a column with 
    #                          semicolon-separated input values.
    #     - 'units': Measurement units (e.g., '€/m2', '% damage').

    #
    # - Optional metadata columns:
    #     - 'origen': Source of the damage function.
    #     - 'region': Geographic area (e.g., 'Spain', 'Cuba').
    #     - 'property type': Category of the affected property (e.g., 'Residential building').
    #     - 'asset': Type of asset (e.g., 'Building Content', 'Building').
    #
    # - Example CSV row:
    #   name,variables,values,application,type,interpolation_type,x
    #   my_fun,x,0;0.5;1,Absolute,interpolation,linear,0;1;2
    # =========================================================================================
    add_dam_fun(overwrite=False)



    # Execute Level 3 Analysis
    level_3_analysis.main(hazard_input_dic, params_dic, exposure_raster_input_dic)