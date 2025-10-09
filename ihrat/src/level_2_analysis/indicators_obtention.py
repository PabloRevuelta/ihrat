from ihrat.src.tools import input_reading
from ihrat.src.tools import compute_zonal_stats

import tools
import copy
import pandas as pd

def indicators_computation(risk_component,comp_indics_main_dic,geo_dic,geo_data_file_path,geo_data_polygon_id_field):
    """data_file_type,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None"""

    if risk_component=='EXPOSURE':
        comp_folder='exp_input_data'
    elif risk_component=='HAZARD':
        comp_folder = 'haz_input_data'
    elif risk_component=='VULNERABILITY':
        comp_folder = 'vuln_input_data'

    for indicator,indicator_indiv_dic in comp_indics_main_dic.items():
        folder=comp_folder+'//'+indicator_indiv_dic['folder']
        indicator_indiv_dic['files'] = input_reading.reading_files(folder,('.shp','.tiff','.tif','.csv'))
        indicator_indiv_dic['dic']=copy.deepcopy(geo_dic)

        present_comp = indicator_indiv_dic['present comparisons']
        if present_comp:
            present_dic={}

        for data_file,data_file_info_dic in indicator_indiv_dic['files'].items():
            if data_file_info_dic['extension']=='.csv':

                df = pd.read_csv(data_file_info_dic['path'], sep=";",encoding="latin-1")
                df[indicator_indiv_dic['atribute key']] = pd.to_numeric(df[indicator_indiv_dic['atribute key']], errors="coerce")
                averages = df.groupby(geo_data_polygon_id_field)[indicator_indiv_dic['atribute key']].mean()
                zonal_stats_dic = averages.to_dict()
            else:
                zonal_stats_dic=zonal_stats_obtention(data_file_info_dic['extension'],indicator_indiv_dic['method'],data_file_info_dic['path'],geo_data_file_path,geo_data_polygon_id_field)

            if present_comp:
                if data_file==indicator_indiv_dic['present file']:
                    present_dic=zonal_stats_dic
                else:
                    tools.present_comp_tool(present_dic,zonal_stats_dic, present_comp)

            norm_scale = indicator_indiv_dic['norm_scale']
            if norm_scale:
                    if present_comp and data_file==indicator_indiv_dic['present file']:
                        pass
                    else:
                        tools.normalitation_tool(zonal_stats_dic,norm_scale)

            for polygon,value in zonal_stats_dic.items():
                indicator_indiv_dic['dic'][polygon][data_file]=value

def zonal_stats_obtention(data_file_type,method,data_file,geo_data_file_path,geo_data_polygon_id_field):

    if method in ['zonal average centers', 'zonal average all touched']:
        zonal_stats_value = 'mean'
    elif method in ['zonal max centers', 'zonal max all touched']:
        zonal_stats_value = 'max'
    elif method in ['zonal total addition centers','zonal total addition all touched']:
        zonal_stats_value = 'sum'
    if method in ['zonal average centers', 'zonal max centers','zonal total addition centers']:
        zonal_stats_method = 'centers'
    elif method in ['zonal average all touched', 'zonal max all touched','zonal total addition all touched']:
        zonal_stats_method = 'all touched'

    if data_file_type=='.tif' or data_file_type=='.tiff':
        indicator_dic = compute_zonal_stats.shape_raster_zonal_stats(str(geo_data_file_path), str(data_file),geo_data_polygon_id_field,
                                                                     zonal_stats_method,zonal_stats_value)
    elif data_file_type=='.shp':
        indicator_dic = compute_zonal_stats.shape_shape_zonal_stats (geo_data_file_path, data_file, zonal_stats_value)
    return indicator_dic