import list_dics_functions as ldfun
import damage_functions as dmfun
import rasterstats as rsts
from pathlib import Path

def scen_compute(expname,expdic,maindic,scenname,pathscen):

    #Add the hazard scenario
    ldfun.add_value_to_dicofidcs(maindic, 'HAZ_SCEN', scenname)

    #Obtain zonal stats for the hazard raster map into the exposition polygons and add them to the dic. We change the
    #None values by 0.
    zonal_stats = rsts.zonal_stats(str(expdic['path']),str(pathscen),stats=['mean'])
    for item in zonal_stats:
        if item['mean'] is None:
            item['mean']=0
    ldfun.add_listofdics_to_dicofdics(maindic, zonal_stats, ['IMP_VAL'])

    #Compute for each building of the system and add to the dic the damage fraction applying a damage curve
    #selected in the input file
    for indiv_build_dic in maindic.values():
        dmfun.apply_damage_fun(indiv_build_dic)

    # Compute the economic impact, multiplying the damage percentage by the value of each building of the system.
    impact_value_dic = ldfun.product_columns_dic(maindic, 'DAM_FRAC', 'EXP_VALUE')
    ldfun.add_dic_to_dicofdics(maindic, impact_value_dic, 'IMP_DAMAGE')

    # Export the dictionary of exposed systems to a .csv file. FALTA ORDEN DE LA TABLA
    namefile_csv=expname+scenname+'.csv'
    path = Path.cwd().parent.parent / 'results/csvs'/namefile_csv
    ldfun.dicofddics_to_csv(maindic, path)

    # Create a new shapefile adding the impact scenario, impact value, damage fraction and consequences value
    namefile_shp=expname+scenname+'.shp'
    path = Path.cwd().parent.parent / 'results/shps' / namefile_shp
    ldfun.dic_to_shp(maindic, path, expdic['crs'])

    return {'EXP_VALUE':ldfun.column_sum(maindic, 'EXP_VALUE'),
                  'IMP_DAMAGE':ldfun.column_sum(maindic, 'IMP_DAMAGE')}