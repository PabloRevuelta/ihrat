import components_aggregation as comp_agg
import indicators_aggregation as ind_agg
import indicators_obtention as ind_obt

from ihrat.src.tools import input_reading

if __name__ == "__main__":

    # explicación de como tienen que venir preproc los archivos de nombre
    # method='zonal average centers', 'zonal max centers','zonal total addition centers','zonal average all touched', 'zonal max all touched','zonal total addition all touched'
    # present comparisons=None,abs to relative differences, abs to variation %, relative differences to variation %

    exp_indics_main_dic={'Population':{'folder':'','method':'zonal total addition centers',"norm_scale": 'norm_scale_2','present comparisons':None},
                        }
    haz_indics_main_dic = {'Precipitation':{'folder':'pr','method':'zonal average centers',"norm_scale": 'norm_scale_1','present comparisons':'relative differences to variation %','present file':'AEMET-REJILLA-spain-historical-pr'},
                           '24h max precipitation':{'folder':'prMax24h','method':'zonal average centers',"norm_scale": 'norm_scale_1','present comparisons':'relative differences to variation %','present file':'AEMET-REJILLA-spain-historical-prMax24h'},
                           'Mean Temperature':{'folder':'tmean','method':'zonal average centers',"norm_scale": 'norm_scale_1','present comparisons':'relative differences to variation %','present file':'AEMET-REJILLA-spain-historical-tmean'},
                           'Hot days number':{'folder':'tasmaxNap90','method':'zonal average centers',"norm_scale": 'norm_scale_1','present comparisons':'relative differences to variation %','present file':'AEMET-REJILLA-spain-historical-tasmaxNap90'}}
    vuln_indics_main_dic = {'Nivel medio de renta por hogar':{'folder':'','method':'zonal average index','atribute key':'Total',"norm_scale": 'norm_scale_3','present comparisons':None}}

    (geo_dic, crs), geo_data_file_path = input_reading.reading_shp_to_dic('spatial_distribution_input')
    geo_data_polygon_id_field='subarea_fu'

    ind_obt.indicators_computation('EXPOSURE',exp_indics_main_dic,geo_dic,geo_data_file_path,geo_data_polygon_id_field)
    ind_obt.indicators_computation('HAZARD', haz_indics_main_dic, geo_dic,geo_data_file_path,geo_data_polygon_id_field)
    ind_obt.indicators_computation('VULNERABILITY', vuln_indics_main_dic, geo_dic, geo_data_file_path, geo_data_polygon_id_field)

    exp_indics_main_dic=ind_agg.indicator_agg('EXPOSURE','quantitative', {'scenarios':['single'],'horizons':['single']},{'formula':'mean','pond weights':None},indic_main_dic=exp_indics_main_dic,folder=None,external_data_entry_type=None)
    haz_indics_main_dic=ind_agg.indicator_agg('HAZARD','quantitative',{'scenarios':['ssp245','ssp585'],'horizons':['70','100']},{'formula':'mean','pond weights':None},indic_main_dic=haz_indics_main_dic,folder=None,external_data_entry_type=None)
    vuln_indics_main_dic=ind_agg.indicator_agg('VULNER','quantitative', {'scenarios':['single'],'horizons':['single']},{'formula':'mean','pond weights':None},indic_main_dic=vuln_indics_main_dic,folder=None,external_data_entry_type=None)

    main_dic=comp_agg.components_dic_creation(exp_indics_main_dic,haz_indics_main_dic,vuln_indics_main_dic)

    comp_agg.components_agg_and_outputs('quantitative', {'formula':'mean','pond weights':''},geo_data_polygon_id_field,main_dic,geom_input_type='internal',crs=crs)


