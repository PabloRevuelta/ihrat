from collections import defaultdict

from ihrat.src.tools import input_reading
from ihrat.src.tools import dictionaries as dics
from ihrat.src.tools import outputs

from ihrat.src.level_3_analysis.shape_exp import shape_exp
from ihrat.src.level_3_analysis.raster_raster import raster_raster as rr

state_counter=0

def main(hazscendic,params_dic,scen_raster_dic=None):
    global state_counter

    for indicator_indiv_dic in hazscendic.values():
        indicator_indiv_dic['files'] =input_reading.reading_files('haz_input_data/'+indicator_indiv_dic['folder'],indicator_indiv_dic['extension'])

    hazscendic=rearranging_dics(hazscendic,params_dic['scenarios'],params_dic['horizons'],params_dic['return rate'])

    expsystdic=input_reading.reading_files('exp_input_data', ('.shp','.tif'))

    summarydic = []
    if params_dic['partial agg']:
        partialaggdic = []

    for syst, syst_dic in expsystdic.items():
        # Main loop. Travel through every system exposed and compute the risk analysis for all impact scenarios.
        # Then, export the results to individual .csv files and .shp files. Also add the aggregate
        # results to the summary dic
        if syst_dic['extension'] == '.shp':



            for scen,scen_dic in hazscendic.items():

                scensum,scen_partial_agg_dic=shape_exp.shape_exp(syst,scen,syst_dic, scen_dic, params_dic['partial agg'],
                                    params_dic['zonal stats method'],params_dic['zonal stats value'])
                summarydic.append(scensum)
                if params_dic['partial agg']:
                    partialaggdic.append(scen_partial_agg_dic)

                print(scen)
                state_counter += 1

        elif syst_dic['extension']=='.tif':

            syst_dic['Type of system'] = scen_raster_dic[syst]['Type of system']
            syst_dic['Damage function'] = scen_raster_dic[syst]['Damage function']

            for scen, scen_dic in hazscendic.items():

                scensum,scen_partial_agg_dic=rr.raster_raster(syst,scen,syst_dic, scen_dic, params_dic['partial agg'])

                summarydic.append(scensum)
                if params_dic['partial agg']:
                    partialaggdic.append(scen_partial_agg_dic)

                print(scen)
                state_counter += 1
        print(syst)

    # Export the summary dictionary and the aggregated partial dictionary (if needed) to a .csv file.
    outputs.summary_output(summarydic)
    if params_dic['partial agg']:
        outputs.partial_agg_output(partialaggdic)
def output_fields_keys(fields,dic):
    fieldkeys = []
    for field in fields:
        if field == 'Exposed value' or field == 'Impact damage':
            system_type = dic[list(dic.keys())[0]][dics.keysdic['Type of system']]
            fieldkeys.append(dics.keysoutputdic[field][system_type])
        else:
            fieldkeys.append(dics.keysoutputdic[field])
    return fieldkeys

def rearranging_dics(hazscendic, scenarios, horizons, return_rates):
    scen_hor_ret_dic = {}
    for scen in (scenarios or ['']):
        for hor in (horizons or ['']):
            for ret in (return_rates or ['']):
                key = '_'.join(filter(None, [scen, hor, ret]))  # evita "__" si alguno está vacío
                scen_hor_ret_dic[key] = {}

                for haz, haz_dic in hazscendic.items():
                    for file_name, file_dic in haz_dic['files'].items():
                        if all(p in file_name for p in [scen, hor, ret] if p):  # ignora vacíos
                            scen_hor_ret_dic[key][haz] = file_dic

    return scen_hor_ret_dic