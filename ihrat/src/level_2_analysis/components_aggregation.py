from ihrat.src.tools import outputs
import tools
from ihrat.src.tools import input_reading

def components_dic_creation(dic_exp,dic_haz,dic_vuln):
    main_dic={}
    main_dic.update(dic_exp)
    for index in main_dic.keys():
        main_dic[index].update(dic_haz[index])
        main_dic[index].update(dic_vuln[index])
    return main_dic

def components_agg_and_outputs(type_of_data,agg_extras,name=None,main_dic=None,external_data_entry_type=None,geom_input_type=None,crs=None):

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
    if type_of_data == 'qualitative':
        tools.qualitative_aggregation_(main_dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK', agg_extras['value scale'], agg_extras['combination matrix'])
    elif type_of_data == 'quantitative':
        tools.quantitative_aggregation_(main_dic, ['HAZARD', 'EXPOSURE', 'VULNER'], 'RISK', agg_extras['formula'], agg_extras['pond weights'])

    # Producimos tabla
    outputs.csv_output(name, main_dic)

    # Producimos mapas. Diccionario con los mismos id que el main_dic y la información poligonal. Le añadimos los datos y exportamos
    if geom_input_type == 'internal':
        outputs.shapefile_output(name, main_dic, crs)
    elif geom_input_type == 'new_file':
        geom_dic, crs = input_reading.reading_input('geometry_output_data', '.shp')
        for index in geom_dic.keys():
            geom_dic[index].update(main_dic[index])
        outputs.shapefile_output(name, geom_dic, crs)
    #external_data_entry_type=internal, mantiene el crs que metemos y los datos geom del main_dic
    #external, los coge nuevos de un archivo externo
    # None, no damos output de mapa






