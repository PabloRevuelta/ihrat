import level_3_analysis

if __name__ == "__main__":

    '''hazard_input_dic = {
        'Flooding': {
            'folder': 'Escenarios',
            'extension': '.tif'
        }
    }

    params_dic = {
        'scenarios': [],
        'horizons': [],
        'return periods':['005'],
        'partial agg':'external',
        'zonal stats method':'centers', #centers or all touched
        'zonal stats value':'mean' #mean or max
    }'''

    hazard_input_dic = {
        'Flooding': {
            'folder': 'Escenarios',
            'extension': '.tif'
        }
    }

    params_dic = {
        'scenarios': [],
        'horizons': [],
        'return periods': ['5'],
        'partial agg': True
    }

    exposure_raster_input_dic = {
        'ury_ppp_2020_constrained': {
            'Type of system': 'POP',
            'Damage function': 'pop_A'
        }
    }

    level_3_analysis.main(hazard_input_dic,params_dic,exposure_raster_input_dic)