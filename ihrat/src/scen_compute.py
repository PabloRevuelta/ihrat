import list_dics_functions as ldfun
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
    ldfun.add_listofdics_to_dicofdics(maindic, zonal_stats, ['IMP VAL'])

    #Calculamos el porecentaje de impacto aplicando las curvas de vulnerabilidad. Curva y=0.33x si 0<=x<=3
    #meter condicionantes para ver los casos menores que 0 o mayores que 3 o errores. (ESTO LO DEJAMOS ASÍ PORQUE
    #ES PROVISIONAL, YA QUE LUEGO HABRÁ QUE ELEGIR LAS FUNCIONES DE VULN DE UNA LISTA). Lo añadimos al diccionario
    damage_perc_list = []
    for i in range(len(zonal_stats)):
        damage_perc_list.append(0.33 * zonal_stats[i]['mean'])
    ldfun.add_list_to_dicofdics(maindic, damage_perc_list, 'DAM_FRAC')

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