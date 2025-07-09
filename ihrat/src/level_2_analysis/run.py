import components_aggregation as comp_agg
import indicators_aggregation as ind_agg
import indicators_obtention as ind_obt

from ihrat.src.tools import input_reading

if __name__ == "__main__":


    spacial_distrib_gdf=input_reading.reading_shp_to_gdf('spatial_distribution_input')
    #crs = spacial_distrib_gdf.crs VER SI PUEDO NO USARLO, TODA LA INFO DEL gdf

    exposure_indicators_dic=ind_obt.indicators_computation('EXPOSURE','zonal average centers',spacial_distrib_gdf)

    a=0
    """"

    ind_agg.indicator_agg(risk_component,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None)
    ind_agg.indicator_agg(risk_component,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None)
    ind_agg.indicator_agg(risk_component,type_of_data,agg_fields,agg_extras,main_dic=None,folder=None,external_data_entry_type=None)

    name =
    main_dic=comp_agg.components_dic_creation(dic_exp,dic_haz,dic_vuln)

    comp_agg.components_agg_and_outputs(type_of_data,agg_extras,name,main_dic,geom_input_type='internal',crs=crs)"""


