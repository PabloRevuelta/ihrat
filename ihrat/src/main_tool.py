from . import input_reading
from . import dictionaries as dics

from ihrat.src.shape_exp import shape_exp
from ihrat.src.raster_raster import raster_raster as rr

state_counter=0


def shape_raster_tool(partial_agg_flag=False,zonal_stats_method='centers',zonal_stats_value='mean'):
    # Get the exposition maps paths and crs from the expmaps folder files,
    # and the impact scenarios maps paths from the impmaps folder files
    expsystdic = input_reading.reading_shapefiles_exp()
    scendic = input_reading.reading_folder_files('impmaps', '.tif')

    # Start the raster-raster analysis
    shape_exp.shape_exp('raster', expsystdic, scendic, partial_agg_flag, zonal_stats_method,
                        zonal_stats_value)

def raster_raster_tool(partial_agg_flag=False,dam_fun_file_flag=False):

    # Get the exposition maps paths and crs from the expmaps folder files,
    # and the impact scenarios maps paths from the impmaps folder files
    expsystdic = expsystdic = input_reading.reading_tif_exp()
    scendic = input_reading.reading_folder_files('impmaps', '.tif')

    # Define the type of system in each input file and the damage functions used (NEED TO BE DONE BY HAND)
    system_type = {'ury_ppp_2020_constrained': 'POP'}
    damage_funs = {'ury_ppp_2020_constrained': 'pop_A'}  # If dam_fun_file=False, function for each system; if dam_fun_file=True, file of damage functions distribution for each system

    # Add the information to the systems dic
    for key, value in system_type.items():
        expsystdic[key]['Type of system'] = value
    if dam_fun_file_flag:
        for key, value in damage_funs.items():
            expsystdic[key]['Damage function files'] = value
    else:
        for key, value in damage_funs.items():
            expsystdic[key]['Damage function'] = value

    rr.raster_raster(expsystdic, scendic, partial_agg_flag, dam_fun_file_flag)

def shape_shape_tool(partial_agg_flag=False,zonal_stats_value='mean'):

    # Get the exposition maps paths and crs from the expmaps folder files,
    # and the impact scenarios maps paths from the impmaps folder files
    expsystdic = input_reading.reading_shapefiles_exp()
    scendic = input_reading.reading_folder_files('impmaps', '.shp')

    # Start the raster-raster analysis
    shape_exp.shape_exp('shapefile', expsystdic, scendic, partial_agg_flag, zonal_stats_value)

def output_fields_keys( fields,dic):
    fieldkeys = []
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            system_type = dic[list(dic.keys())[0]][dics.keysdic['Type of system']]
            fieldkeys.append(dics.keysoutputdic[field][system_type])
        else:
            fieldkeys.append(dics.keysoutputdic[field])
    return fieldkeys