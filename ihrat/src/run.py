import main_tool

if __name__ == "__main__":

    #Basic: main_tool(tool_selected,partial_agg_flag=False,zonal_stats_method='centers',zonal_stats_value='mean',dam_fun_file=FALSE)
    #zonal_stats_method='centers' or 'all touched' only in s-r ('centers' base)
    #partial_agg_flag = False or True for all (FALSE base)
    #zonal_stats_value = 'mean' or 'max' only in s-r y s-s ('mean' base)
    #dam_fun_file=FALSE or TRUE for r-r (FALSE base)

    main_tool.shape_raster_tool(partial_agg_flag=True)