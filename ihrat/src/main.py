from pathlib import Path
import input_reading
from ihrat.src.shape_raster import shape_raster as sr
from ihrat.src.raster_raster import raster_raster as rr


def output_fields_keys(dic,fields,keysdic,keysoutputdic):
    fieldkeys = []
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            type = dic[list(dic.keys())[0]][keysdic['Type of system']]
            fieldkeys.append(keysoutputdic[field][type])
        else:
            fieldkeys.append(keysoutputdic[field])
    return fieldkeys

def main():


    shape_raster_flag=False
    raster_raster_flag=True

    # We define the keys all the inner dictionaries are going to work with. In the case of a shape-raster approach,
    # the input .shp files need to be pre-processed to use the same keys are their attribute headers
    keysdic = {'Exposed system': 'SYSTEM', 'Elements ID': 'BUILD_ID', 'Exposed value': 'EXP_VALUE',
               'Type of system': 'TYPE', 'Damage function': 'DAM_FUN', 'Section identificator': 'CUSEC',
               'Hazard scenario': 'HAZ_SCEN', 'Impact value': 'IMP_VAL', 'Damage fraction': 'DAM_FRAC',
               'Impact damage': 'IMP_DAMAGE'}
    # Possible types of systems: BUILD, POP
    keysoutputdic = {'Exposed system': 'Exposed system', 'Elements ID': 'Building ID',
                     'Exposed value': {'BUILD': 'Exposed value (€)', 'POP': 'Exposed people (n)'},
                     'Type of system': 'Type of element', 'Damage function': 'Damage function',
                     'Section identificator': 'CUSEC', 'Hazard scenario': 'Hazard scenario',
                     'Impact value': 'Impact value (m)', 'Damage fraction': 'Damage fraction',
                     'Impact damage': {'BUILD': 'Impact damage (€)', 'POP': 'Impacted people (n)'}}

    if shape_raster_flag:

        # Get the exposition maps paths and crs from the expmaps folder files
        # and the hazard scenarios maps paths from the hazmaps folder files
        expsystdic = input_reading.reading_shapefiles_exp()
        scendic = input_reading.reading_folder_files(Path.cwd().parent.parent / 'hazmaps', '.tif')

        #Start the raster-raster analysis
        sr.shape_raster(expsystdic,scendic, keysdic,keysoutputdic,partial_agg_flag = True)
    elif raster_raster_flag:

        # Get the exposition maps paths and crs from the expmaps folder files
        # and the hazard scenarios maps paths from the hazmaps folder files
        expsystdic=input_reading.reading_tif_exp()
        scendic = input_reading.reading_folder_files(Path.cwd().parent.parent / 'hazmaps', '.tif')

        #Define the type of system in each input file and the damage functions used (NEED TO BE DONE BY HAND)
        damage_funs={'URY_I3_human_m2':'pop_A','ury_ppp_2020_constrainedCROPED2':'pop_A'}
        system_type = {'URY_I3_human_m2': 'POP','ury_ppp_2020_constrainedCROPED2': 'POP'}

        #Add the information to the systems dic
        for key,value in damage_funs.items():
            expsystdic[key]['Damage function']=value
        for key,value in system_type.items():
            expsystdic[key]['Type of system']=value


        rr.raster_raster(expsystdic,scendic,keysdic,keysoutputdic)



if __name__ == "__main__":
    main()