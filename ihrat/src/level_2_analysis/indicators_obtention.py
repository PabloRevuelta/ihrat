from ihrat.src.tools import input_reading
import rasterstats as rsts
from ihrat.src.tools import compute_zonal_stats

def indicators_computation(risk_component,method,spacial_distrib_gdf):
    """"data_file_type,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None"""
    indicators_dic={}
    if risk_component=='EXPOSURE':
        indicators_dic=input_reading.reading_shapefiles_exp()
        indicators_dic.update(input_reading.reading_tif_exp())

    for indicator_file in indicators_dic.values():
        if indicator_file['extension']=='.shp':
            indicator_dic=indicator_obtention('shapefile',method,indicator_file['path'],spacial_distrib_gdf,norm_scale=None)
        if indicator_file['extension']=='.tif':
            indicator_dic=indicator_obtention('raster',method,indicator_file['path'],spacial_distrib_gdf,norm_scale=None)
    """if risk_component=='HAZARD':
        indicators_dic=input_reading.reading_folder_files('exp_input_data','.shp')
        indicators_dic.update(input_reading.reading_folder_files('exp_input_data','.tif'))
    if risk_component=='VULNERABILITY':
        indicators_dic=input_reading.reading_folder_files('exp_input_data','.shp')
        indicators_dic.update(input_reading.reading_folder_files('exp_input_data','.tif'))"""
    a=0

def indicator_obtention(data_file_type,method,data_file,spacial_distrib_gdf,norm_scale=None):

    if data_file_type=='raster':

        if method in ['zonal average centers','zonal average all touched',]:
            zonal_stats_value='mean'
        elif method in ['zonal max centers','zonal max all touched']:
            zonal_stats_value = 'max'
        if method in ['zonal average centers','zonal max centers']:
            zonal_stats_method='centers'
        elif method in ['zonal average all touched','zonal max all touched']:
            zonal_stats_method='all touched'
        indicator_dic = compute_zonal_stats.shape_raster_zonal_stats(spacial_distrib_gdf, str(data_file), zonal_stats_method,
                                                                   zonal_stats_value)

    """if data_file_type=='shapefile':

        for index, building in spacial_distrib_gdf.iterrows():
            intersections = []
            data_gdf=input_reading.reading_shp_to_gdf(data_file)
            for index2, polygon in data_gdf.iterrows():
                if method == 'zonal average':
                    if building['geometry'].intersects(polygon['geometry']):
                        intersections.append([building['geometry'].intersection(polygon['geometry']).area,
                                              polygon[dics.keysdic['Impact value']]])
                    if sum(x for x, y in intersections) == 0:
                        system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = 0
                    else:
                        system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = (
                                sum(x * y for x, y in intersections) / sum(x for x, y in intersections))
                if method == 'zonal max':
                    if building['geometry'].intersects(polygon['geometry']):
                        intersections.append([polygon[dics.keysdic['Impact value']]])
                    if sum(x for x in intersections) == 0:
                        system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = 0
                    else:
                        system_dic[building[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = max(
                            intersections)
    if norm_scale:
        !!!!"""

    return indicator_dic