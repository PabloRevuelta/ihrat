import bathtub_module

if __name__ == "__main__":

    twl_dic_single={'scen 1': 1.0}
    twl_dic_multi={'file_name':'ExpFit_A_pilot','scens_names': ['exp_rp50','exp_rp100']}
    coastlines_file_name='coastlines.shp'
    crs='epsg:3035'
    bathtub_module.bathtub_module(twl_dic_multi,coastlines_file_name,crs,input_type='multi value')