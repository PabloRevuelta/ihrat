import level_3_analysis

if __name__ == "__main__":

    hazscendic = {
        'Inundación': {'folder': 'Escenarios CROPED', 'extension': '.tif'}
    }

    params_dic = {'scenarios': [], 'horizons': [], 'return rate':['005','010','025','050','100','500'],
                  'partial agg':True,'zonal stats method':'centers' ,'zonal stats value':'mean'}

    scen_raster_dic={'ury_ppp_2020_constrained':{'Type of system':'POP','Damage function':'pop_A'}}

    level_3_analysis.main(hazscendic,params_dic,scen_raster_dic)