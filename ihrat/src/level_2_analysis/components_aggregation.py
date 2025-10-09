from ihrat.src.tools import outputs
import tools
from ihrat.src.tools import input_reading

import copy

def components_dic_creation(dic_exp,dic_haz,dic_vuln):
    dics=[dic_exp,dic_haz,dic_vuln]
    biggest_dic = max(dics, key=lambda d: len(d))
    scen_hor_dic = copy.deepcopy(biggest_dic)

    for d in dics:
        if d is biggest_dic:
            continue
        # Contar subdiccionarios en el diccionario actual
        if len(d) == 1:
            # Obtener el único subdiccionario
            only_dic = d[list(d.keys())[0]]

            # Recorrer todos los subdiccionarios de nuevo_dic
            for subkey, subdic in scen_hor_dic.items():
                # Recorrer los subsubdiccionarios y copiar valores
                for key, only_dic_subdic in only_dic.items():
                    subdic[key].update(only_dic_subdic)
        else:
            # Caso: diccionarios con varios subdiccionarios
            for sub_key, subdic in d.items():
                # sub_key existe en nuevo_dic, fusionamos subsubdiccionarios correspondientes
                for subsub_key, subsub_val in subdic.items():
                        scen_hor_dic[sub_key][subsub_key].update(subsub_val)

    return scen_hor_dic

def components_agg_and_outputs(type_of_data,agg_extras,geo_data_polygon_id_field,main_dic=None,external_data_entry_type=None,geom_input_type=None,crs=None):

    # external_data_entry_type==None, mantiene el main_dic como entra. Si no, lo cambia por uno leído externo
    if external_data_entry_type == 'csv':
        name, main_dic = input_reading.reading_input('components_data', '.csv')
    elif external_data_entry_type == 'shapefile':
        name, main_dic, crs = input_reading.reading_input('components_data', '.shp')

    """agg_extras, cosas adicionales para la agregación, en funcion del tipo de variable
    if type_of_data=='qualitative':
        agg_extras['value scale']
        agg_extras['combination matrix']
        ])
    elif type_of_data=='quantitative':
        agg_extras['formula']='geom_mean' or ...
        agg_extras['pond weights'], puede tener o no"""


    #Calculo de la agregación de los indicadores compuestos de las componentes.
    #agg_extras es un diccionario con las cosas necesarias para calcular las agregaciones en ambos casos
    for key, dic in main_dic.items():
        if type_of_data == 'qualitative':
            tools.qualitative_aggregation_(dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK', agg_extras['value scale'], agg_extras['combination matrix'])
        elif type_of_data == 'quantitative':
            tools.quantitative_aggregation_(dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK', agg_extras['formula'], agg_extras['pond weights'])

    # Producimos tabla

        outputs.simple_csv_output(key,geo_data_polygon_id_field, dic)

        # Producimos mapas. Diccionario con los mismos id que el main_dic y la información poligonal. Le añadimos los datos y exportamos
        if geom_input_type == 'internal':
            outputs.simple_shapefile_output(key, geo_data_polygon_id_field,dic, crs)
        elif geom_input_type == 'new_file':
            geom_dic, crs = input_reading.reading_input('geometry_output_data', '.shp')
            for index in geom_dic.keys():
                geom_dic[index].update(main_dic[index])
            outputs.simple_shapefile_output(key, geo_data_polygon_id_field,geom_dic, crs)
        #external_data_entry_type=internal, mantiene el crs que metemos y los datos geom del main_dic
        #external_data_entry_type=new_file, los coge nuevos de un archivo externo
        # None, no damos output de mapa






