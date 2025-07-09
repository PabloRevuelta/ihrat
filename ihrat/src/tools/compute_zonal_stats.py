import rasterstats as rsts

def shape_shape_zonal_stats (spacial_distrib_gdf, data_gdf, zonal_stats_value):

    for index, spatial_zone in spacial_distrib_gdf.iterrows():

        intersections = []
        for index2, polygon in data_gdf.iterrows():
            if zonal_stats_value == 'mean':
                if spatial_zone['geometry'].intersects(polygon['geometry']):
                    intersections.append([spatial_zone['geometry'].intersection(polygon['geometry']).area,
                                          polygon[dics.keysdic['Impact value']]])
                if sum(x for x, y in intersections) == 0:
                    system_dic[spatial_zone[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = 0
                else:
                    system_dic[spatial_zone[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = (
                            sum(x * y for x, y in intersections) / sum(x for x, y in intersections))
            if zonal_stats_value == 'max':
                if spatial_zone['geometry'].intersects(polygon['geometry']):
                    intersections.append([polygon[dics.keysdic['Impact value']]])
                if sum(x for x in intersections) == 0:
                    system_dic[spatial_zone[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = 0
                else:
                    system_dic[spatial_zone[dics.keysdic['Elements ID']]][dics.keysdic['Impact value']] = max(intersections)

def shape_raster_zonal_stats(spatial_units_data, values_data, zonal_stats_method, zonal_stats_value):
    if zonal_stats_method=='centers':
        zonal_stats = rsts.zonal_stats(spatial_units_data, values_data, stats=[zonal_stats_value])
    elif zonal_stats_method=='all touched':
        zonal_stats = rsts.zonal_stats(spatial_units_data, values_data, all_touched=True,stats=[zonal_stats_value])
    for item in zonal_stats:
        if item[zonal_stats_value] is None:
            item[zonal_stats_value] = 0
        item[zonal_stats_value] = round(item[zonal_stats_value], 3)

    return zonal_stats