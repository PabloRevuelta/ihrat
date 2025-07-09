import tools

from ihrat.src.tools import input_reading

#Entrada: datos de un indicador en varias variables

#Salida: indicador agregado

#Puede ser lo mismo, en csv o en shpapefile o venir de antes. Aquí entra en diccionario

def indicator_agg(risk_component,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None):

    # external_data_entry_type==None, mantiene el main_dic como entra. Si no, lo cambia por uno leído externo
    if external_data_entry_type == 'csv':
        name, main_dic = input_reading.reading_input(folder, '.csv')
    elif external_data_entry_type == 'shapefile':
        name, main_dic, crs = input_reading.reading_input(folder, '.shp')

    if type_of_data == 'qualitative':
        tools.qualitative_aggregation_(main_dic, agg_fields, risk_component, agg_extras['value scale'],
                                       agg_extras['combination matrix'])
    elif type_of_data == 'quantitative':
        tools.quantitative_aggregation_(main_dic, agg_fields, risk_component, agg_extras['formula'],
                                        agg_extras['pond weights'])

    """if type_of_data=='qualitative':
            agg_extras['value scale']=['low', 'medium', 'high']
            agg_extras['combination matrix']=np.array([
                [[0, 0, 1], [0, 1, 1], [1, 1, 2]],
                [[0, 1, 1], [1, 1, 2], [1, 2, 2]],
                [[1, 1, 2], [1, 2, 2], [2, 2, 2]]"""