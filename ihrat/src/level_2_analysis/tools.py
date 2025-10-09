import statistics as stats
import numpy as np

import norm_scales_dics

def quantitative_aggregation_(dic,keys,new_field,formula,pond_list):

    for spatial_unit_dic in dic.values():
        values = [spatial_unit_dic[key] for key in keys]
        if formula=='mean':
            spatial_unit_dic[new_field] = round(
                stats.mean(values))
        elif formula=='geom_mean':
            spatial_unit_dic[new_field] = round(stats.geometric_mean(values))
        elif formula=='max':
            spatial_unit_dic[new_field] = max(values)
        elif formula == 'pond_mean':
            spatial_unit_dic[new_field] = round(
                np.average(values,weights=pond_list))
        elif formula == 'pond_geom_mean':
            pond_product = 1
            weights_sum = sum(pond_list)
            for x, w in zip(values, pond_list):
                pond_product *= x ** w
            spatial_unit_dic[new_field] = round(pond_product ** (1 / weights_sum))

#Salidas: tabla con con los indicadores para distintos escenarios, mapas con los indicadores para distintos escenarios
def qualitative_aggregation_(dic,agg_fields,new_field,value_scale,combination_matrix):

    #Convertimos la escala a un diccionario de asociaciones, para facilitar el cálculo:
    values_corr_dic={}
    for i in value_scale:
        values_corr_dic[value_scale[i]]=i

    #ver como calculamos: matriz de combinaciones
    for spatial_unit in dic.values():

        value_coords = [values_corr_dic[spatial_unit[field]] for field in agg_fields]
        spatial_unit[new_field]=value_scale[combination_matrix[tuple(value_coords)]]

def normalitation_tool(dic,normalization_scale):
    normalization_scale_dic = getattr(norm_scales_dics, normalization_scale)
    normalization_scale_categories=list(normalization_scale_dic.keys())
    for spatial_unit,ind_value in dic.items():
        assigned=False
        counter=0
        while not assigned and counter<len(normalization_scale_categories):
            if ind_value<normalization_scale_dic[normalization_scale_categories[counter]]:
                dic[spatial_unit]=normalization_scale_categories[counter]
                assigned=True
            counter+=1
        if not assigned:
            dic[spatial_unit] = normalization_scale_categories[counter-1]+1

def present_comp_tool(present_dic,zonal_stats_dic, present_comp):
    for key in zonal_stats_dic.keys():
        if present_comp=='relative differences to variation %':
            zonal_stats_dic[key]=zonal_stats_dic[key]*100/present_dic[key]

