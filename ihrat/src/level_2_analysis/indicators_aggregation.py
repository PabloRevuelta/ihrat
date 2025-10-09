import tools
from ihrat.src.tools import input_reading

import copy

#Entrada: datos de un indicador en varias variables

#Salida: indicador agregado

#Puede ser lo mismo, en csv o en shpapefile o venir de antes. Aquí entra en diccionario

def indicator_agg(risk_component,type_of_data,scen_hor_fields,agg_extras,indic_main_dic=None,folder=None,external_data_entry_type=None):

    # external_data_entry_type==None, mantiene el main_dic como entra. Si no, lo cambia por uno leído externo
    if external_data_entry_type == 'csv':
        name, main_dic = input_reading.reading_input(folder, '.csv')
    elif external_data_entry_type == 'shapefile':
        name, main_dic, crs = input_reading.reading_input(folder, '.shp')

    scen_hor_dic=rearranging_dics(indic_main_dic,scen_hor_fields)
    for dic in scen_hor_dic.values():
        values= list(next(iter(dic.values())).keys())
        values.remove('geometry')
        if type_of_data == 'qualitative':
            tools.qualitative_aggregation_(dic,values, risk_component, agg_extras['value scale'],
                                           agg_extras['combination matrix'])
        elif type_of_data == 'quantitative':
            tools.quantitative_aggregation_(dic,values, risk_component, agg_extras['formula'],
                                            agg_extras['pond weights'])

    return scen_hor_dic

    """if type_of_data=='qualitative':
            agg_extras['value scale']=['low', 'medium', 'high']
            agg_extras['combination matrix']=np.array([
                [[0, 0, 1], [0, 1, 1], [1, 1, 2]],
                [[0, 1, 1], [1, 1, 2], [1, 2, 2]],
                [[1, 1, 2], [1, 2, 2], [2, 2, 2]]"""

def rearranging_dics(indic_main_dic,scen_hor_fields):
    scen_hor_dic={}
    spatial_units_dic={spatial_unit:{'geometry':spatial_unit_dic['geometry']} for spatial_unit,spatial_unit_dic in indic_main_dic[next(iter(indic_main_dic))]['dic'].items()}
    for scen in scen_hor_fields['scenarios']:
        for hor in scen_hor_fields['horizons']:
            scen_hor_dic[scen+'_'+hor]=copy.deepcopy(spatial_units_dic)
            for indic,indic_dic in indic_main_dic.items():
                for spatial_unit,spatial_unit_dic in indic_dic['dic'].items():
                    for scen_hor,value in spatial_unit_dic.items():
                        if scen in scen_hor and  hor in scen_hor:
                            scen_hor_dic[scen + '_' + hor][spatial_unit][indic]=value
                        if scen=='single' and hor=='single':
                            scen_hor_dic[scen + '_' + hor][spatial_unit][indic]=value
    return scen_hor_dic