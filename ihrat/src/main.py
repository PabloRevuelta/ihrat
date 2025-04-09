import geopandas as gpd
import os
from pathlib import Path
import list_dics_functions as ldfun
import scen_compute

def reading_shapefiles_exp(): #Returns a list with the path from all the .shp files in the expmaps folder
    #Get the exposition maps folder path
    folderpath=Path.cwd().parent.parent / 'expmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in folderpath.rglob('*.shp') if file.is_file()]
    filesdic={}
    for file in files:
        filesdic[os.path.splitext(os.path.relpath(file, folderpath))[0]]={'path':file,'crs':gpd.read_file(file).crs}

    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return filesdic
def reading_rasters_haz(): #Returns a list with the path from all the .shp files in the expmaps folder
    #Get the exposition maps folder path
    folderpath=Path.cwd().parent.parent / 'hazmaps'
    #Search for all the .shp files and add them to the list
    files = [file for file in folderpath.rglob('*.tif') if file.is_file()]
    filesdic = {}
    for file in files:
        filesdic[os.path.splitext(os.path.relpath(file, folderpath))[0]] = file
    # Check crs. Si alguno da error, no utilizar y marcar (AÑADIR)
    return filesdic



def main():

    #Get the exposition maps paths from the expmaps folder files
    #and the hazard scenarios maps paths and crs from the hazmaps folder files
    expsystdic = reading_shapefiles_exp()
    scendic = reading_rasters_haz()

    # Create dic for the summary table
    summarydic = []

    #Main loop. Travel through every system exposed and compute the risk analysands for all hazard scenarios.
    #Then, export the results to individual .csv files and .shp files. Also add the aggregate
    #results to the summary dic
    for system in expsystdic.keys():

        # We need the attribute keys of the wanted attributes from the shapefile and the keys we want to use in the outputs.
        # VER COMO HACEMOS CON LOS NOMBRS DE LAS COLUMNAS EN LOS INPUTS. Si los pasamos previos o los ponemos
        # bien directamente en los archivos de input en un pre-formateo de los datos.

        #In the shapefiles, the attributes headers must be pre-processed to match the used by the program, those being:
        #Buildings: BUILD_ID, Population number/Building value: EXP_VALUE, Tipe of system: TYPE (POP, BUILD),
        #Damage function: DAM_FUN
        indiv_dic = ldfun.shp_to_dict(expsystdic[system]['path'], 'BUILD_ID')
        """indiv_dic= ldfun.expshp_to_dic(expsystdic[system]['path'],keys)"""

        print(system)

        for scen in scendic.keys():

            scensum = scen_compute.scen_compute(system, expsystdic[system], indiv_dic, scen,
                                                scendic[scen])
            scensum['SYSTEM']=system
            scensum['SCEN']=scen
            summarydic.append(scensum)

            print(scen)




    #Export them to a .csv file.
    path = Path.cwd().parent.parent / 'results/csvs/manga_exposicion_summary.csv'
    ldfun.listofddics_to_csv(summarydic, path)


if __name__ == "__main__":
    main()