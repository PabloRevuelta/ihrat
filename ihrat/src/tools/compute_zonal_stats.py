import rasterstats as rsts
import geopandas as gpd

from ihrat.src.tools import input_reading
from ihrat.src.tools import list_dics_functions as ldfun
from ihrat.src.tools import dictionaries as dics

def shape_shape_zonal_stats (geo_data_file_path, data_file,polygon_id_field,input_field, zonal_stats_value):

    spacial_distrib_gdf=gpd.read_file(geo_data_file_path)
    data_gdf=gpd.read_file(data_file)

    zonal_stats={}

    for index, spatial_zone in spacial_distrib_gdf.iterrows():
        intersections = []
        #print('###########')
        #print(str(index) + '/' + str(len(spacial_distrib_gdf)))
        #print('###########')
        for index2, polygon in data_gdf.iterrows():
            #print(str(index2) + '/' + str(len(data_gdf)))

            if zonal_stats_value == 'mean':
                if spatial_zone['geometry'].intersects(polygon['geometry']):
                    intersections.append([spatial_zone['geometry'].intersection(polygon['geometry']).area,
                                          polygon[input_field]])
                if sum(x for x, y in intersections) == 0:
                    zonal_stats[spatial_zone[polygon_id_field]] = 0
                else:
                    zonal_stats[spatial_zone[polygon_id_field]] = (
                            sum(x * y for x, y in intersections) / sum(x for x, y in intersections))
            if zonal_stats_value == 'max':
                if spatial_zone['geometry'].intersects(polygon['geometry']):
                    intersections.append(polygon[input_field])
                if sum(x for x in intersections) == 0:
                    zonal_stats[spatial_zone[polygon_id_field]] = 0
                else:
                    zonal_stats[spatial_zone[polygon_id_field]] = max(
                        intersections)
            if zonal_stats_value == 'sum':
                if spatial_zone['geometry'].intersects(polygon['geometry']):
                    intersections.append(polygon[input_field])
                zonal_stats[spatial_zone[polygon_id_field]]=sum(x for x in intersections)
    return zonal_stats


def shape_raster_zonal_stats(spatial_units_data, values_data, polygon_id_field,zonal_stats_method, zonal_stats_value):
    if zonal_stats_method=='centers':
        zonal_stats = rsts.zonal_stats(str(spatial_units_data), str(values_data), stats=[zonal_stats_value])
    elif zonal_stats_method=='all touched':
        zonal_stats = rsts.zonal_stats(spatial_units_data, values_data, all_touched=True,stats=[zonal_stats_value])
    for item in zonal_stats:
        if item[zonal_stats_value] is None:
            item[zonal_stats_value] = 0
        item[zonal_stats_value] = round(item[zonal_stats_value], 3)

    zonal_stats_dic,_=input_reading.shp_to_dic(spatial_units_data,[polygon_id_field])

    ldfun.add_listofdics_to_dic(zonal_stats_dic, zonal_stats)

    return zonal_stats_dic