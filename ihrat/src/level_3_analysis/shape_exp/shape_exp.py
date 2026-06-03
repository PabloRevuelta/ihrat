from ihrat.src.tools import input_reading
from ihrat.src.tools import list_dics_functions as ldfun
from ihrat.src.level_3_analysis.damage_functions import damage_functions as dmfun
from ihrat.src.tools import outputs
from ihrat.src.tools import dictionaries as dics
from ihrat.src.level_3_analysis import level_3_analysis
from ihrat.src.tools import compute_zonal_stats

def shape_exp(
        syst,
        scen_hor_rp,
        expsystdic,
        scen_hor_rp_dic,
        partial_agg_flag,
        zonal_stats_method='centers',
        zonal_stats_value='mean'
):
    """
    Perform risk analysis for a vectorial exposed system (shapefile)
    under a specific hazard scenario.

    The function:
    1. Loads exposed elements from the shapefile into a dictionary.
    2. Computes hazard impact values per element via zonal statistics
       (raster or vector hazard layers supported).
    3. Applies damage functions (Relative or Absolute) and calculates
       economic damage per element.
    4. Exports detailed results as shapefile and CSV.
    5. Returns scenario-level summary and optional partial aggregation.

    PARAMETERS
    ----------
    syst : str
        Name of the exposed system.

    scen_hor_rp : str
        Impact scenario identifier (combination of scenario, horizon,
        return period, and percentile).

    expsystdic : dict
        Metadata of the exposed system shapefile
        (path, CRS, extension, etc.).

    scen_hor_rp_dic : dict
        Dictionary of hazard layers for the given scenario, where each
        key is a hazard name and each value contains path and extension.

    partial_agg_flag : bool or str
        If True, compute and return partial aggregation results by
        territorial units. If 'external', additionally assigns section
        identifiers from an external zoning shapefile.

    zonal_stats_method : str, default 'centers'
        Method used for zonal statistics:
            - 'centers'    → uses element centroids
            - 'all touched' → uses all pixels touched by the geometry

    zonal_stats_value : str, default 'mean'
        Statistic extracted from hazard layer:
            - 'mean' → average hazard value within element
            - 'max'  → maximum hazard value within element

    RETURNS
    -------
    tuple
        (scensum, partial_agg)

        scensum : dict
            Scenario summary results including exposed value (if available),
            system type, impact scenario, damage function type, and total
            impact damage.

        partial_agg : dict or None
            Dictionary of partial aggregation results if partial_agg_flag
            is True, otherwise None.
    """
    # ------------------------------------------------------------------
    # 1. Load exposed system elements from shapefile into dictionary
    #    Required fields: Elements ID, Type of system, Damage function, geometry
    #    Optional fields: at least one of Exposed value or Area must be present
    # ------------------------------------------------------------------
    system_dic, _ = input_reading.shp_to_dic(
        expsystdic['path'],
        [
            dics.keysdic['Elements ID'],
            dics.keysdic['Type of system'],
            dics.keysdic['Damage function'],
            'geometry'
        ],
        optional_keys=[
            dics.keysdic['Exposed value'],
            dics.keysdic['Area']
        ]
    )
    # Add the current impact scenario identifier to each exposed element
    ldfun.add_value_to_dicofdics(system_dic, dics.keysdic['Impact scenario'], scen_hor_rp)

    # ------------------------------------------------------------------
    # 2. Initialize scenario summary
    #    If 'Exposed value' is present → Relative damage function
    #    If 'Exposed value' is absent  → Absolute damage function
    # ------------------------------------------------------------------
    if dics.keysdic['Exposed value'] in system_dic[next(iter(system_dic))].keys():
        scensum = {
            dics.keysdic['Exposed system']:        syst,
            dics.keysdic['Type of system']:        system_dic[next(iter(system_dic))][dics.keysdic['Type of system']],
            dics.keysdic['Exposed value']:         ldfun.column_sum(system_dic, dics.keysdic['Exposed value']),
            dics.keysdic['Impact scenario']:       scen_hor_rp,
            dics.keysdic['Type of damage function']: 'Relative'
        }
    else:
        scensum = {
            dics.keysdic['Exposed system']:        syst,
            dics.keysdic['Type of system']:        system_dic[next(iter(system_dic))][dics.keysdic['Type of system']],
            dics.keysdic['Impact scenario']:       scen_hor_rp,
            dics.keysdic['Type of damage function']: 'Absolute'
        }

    # Keep track of processed hazard names for CSV column ordering
    haz_keys = []

    # ------------------------------------------------------------------
    # 3. Compute hazard impact values for each hazard layer
    #    - Raster hazard (.tif) → zonal statistics over exposure polygons
    #    - Vector hazard (.shp) → spatial overlay statistics
    # ------------------------------------------------------------------
    for haz in scen_hor_rp_dic.keys():

        haz_keys.append(haz)

        if scen_hor_rp_dic[haz]['extension'] == '.tif':
            # Raster hazard: extract statistics per exposure element
            zonal_stats = compute_zonal_stats.shape_raster_zonal_stats(
                expsystdic['path'],
                scen_hor_rp_dic[haz]['path'],
                dics.keysdic['Elements ID'],
                zonal_stats_method,
                zonal_stats_value
            )
            ldfun.add_dic_to_dicofdics(system_dic, zonal_stats, haz)

        elif scen_hor_rp_dic[haz]['extension'] == '.shp':
            # Vector hazard: extract statistics from overlapping hazard polygons
            zonal_stats = compute_zonal_stats.shape_shape_zonal_stats(
                expsystdic['path'],
                scen_hor_rp_dic[haz]['path'],
                dics.keysdic['Elements ID'],
                dics.keysdic['Impact value'],
                zonal_stats_value
            )
            ldfun.add_dic_to_dicofdics(system_dic, zonal_stats, dics.keysdic['Impact value'])

    # ------------------------------------------------------------------
    # 4. Apply damage functions
    #    Relative → adds 'Damage fraction' and 'Impact damage' per element
    #    Absolute → adds 'Relative damage' and 'Impact damage' per element
    # ------------------------------------------------------------------
    dmfun.apply_damage_fun_shp(system_dic)

    # ------------------------------------------------------------------
    # 5. Export detailed outputs
    #    - Shapefile: enriched geometry with all computed fields
    #      (if partial_agg_flag='external', section identifiers are also
    #      assigned here, as this is the only point with geometries available)
    #    - CSV: tabular results with hazard and damage fields
    # ------------------------------------------------------------------
    outputs.shapefile_output(syst + scen_hor_rp, system_dic, expsystdic['crs'], partial_agg_flag)

    fields = [
        'Elements ID',
        'Type of system',
        'Exposed value',
        'Area',
        'Impact scenario',
        'Damage function',
        'Damage fraction',
        'Relative damage',
        'Impact damage'
    ]
    # Map internal field names → output column names
    new_field_names = level_3_analysis.output_fields_keys(fields, system_dic)
    # Insert hazard columns before damage-related fields
    new_field_names[5:5] = haz_keys
    fields[5:5] = haz_keys
    outputs.csv_output(syst + scen_hor_rp, fields, new_field_names, system_dic)

    # ------------------------------------------------------------------
    # 6. Update scenario summary with total aggregated impact damage
    # ------------------------------------------------------------------
    scensum[dics.keysdic['Impact damage']] = ldfun.column_sum(
        system_dic,
        dics.keysdic['Impact damage']
    )

    # ------------------------------------------------------------------
    # 7. Optional partial aggregation by territorial unit
    # ------------------------------------------------------------------
    if partial_agg_flag:
        return scensum, partial_aggregates(system_dic, syst, scen_hor_rp)

    return scensum, None


def partial_aggregates(
        system_dic,
        syst,
        scen_hor_rp
):
    """
    Aggregate exposed system results by Section identificator.

    For each unique section identifier in the system dictionary, this function:
    1. Creates a new entry in the partial dictionary (if it doesn't exist yet).
    2. Initializes the aggregation fields.
    3. Sums 'Exposed value' (if present) and 'Impact damage' across all
       elements belonging to that section.

    Supports both damage function types:
    - Relative: 'Exposed value' is present and aggregated.
    - Absolute: 'Exposed value' is absent; only 'Impact damage' is aggregated.

    PARAMETERS
    ----------
    system_dic : dict of dict
        Dictionary of system elements where each value contains:
        - Impact damage
        - Section identificator
        - Type of system
        - Exposed value (only for Relative damage functions)
        - Other metadata

    syst : str
        Name of the exposed system.

    scen_hor_rp : str
        Scenario identifier (combination of scenario, horizon,
        return period, and percentile).

    RETURNS
    -------
    dict
        Dictionary keyed by Section identificator, each containing
        aggregated values and metadata.
    """

    partial_dic = {}

    # Determine damage function type from first element
    first_element = system_dic[next(iter(system_dic))]
    is_relative = dics.keysdic['Exposed value'] in first_element

    # Iterate through all elements in the system
    for value in system_dic.values():

        # Identify the section for this element
        sec_ind = value[dics.keysdic['Section identificator']]

        # Initialize aggregation entry if not present
        if sec_ind not in partial_dic:
            partial_dic[sec_ind] = {
                dics.keysdic['Exposed system']:  syst,
                dics.keysdic['Type of system']:  first_element[dics.keysdic['Type of system']],
                dics.keysdic['Impact scenario']: scen_hor_rp,
                dics.keysdic['Impact damage']:   0
            }
            # Add 'Exposed value' only for Relative damage functions
            if is_relative:
                partial_dic[sec_ind][dics.keysdic['Exposed value']] = 0

        # Aggregate impact damage for all types
        partial_dic[sec_ind][dics.keysdic['Impact damage']] += value[dics.keysdic['Impact damage']]

        # Aggregate exposed value only if Relative
        if is_relative:
            partial_dic[sec_ind][dics.keysdic['Exposed value']] += value[dics.keysdic['Exposed value']]

    return partial_dic


