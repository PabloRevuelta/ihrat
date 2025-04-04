import geopandas as gpd
import csv

def shp_to_dict(file,key):
    #Export the .shp file into a geo data frame and then into a dictionary
    geodataframe = gpd.read_file(file)
    dict = geodataframe.set_index(key).T.to_dict('dict')
    return dict
def add_listofdics_to_dicofdics(dic,listofdics,newkeys):
    #Add to each entry of a dictionary of dictionaries the values stored in a list of dictionaries.
    #To each entry of the dictionary, add the corresponding dictionary from the list
    for i, j in zip(dic, listofdics):
        dic[i].update(j)
    keyslist = list(set(key for diccionario in listofdics for key in diccionario.keys()))
    for i in range(len(keyslist)):
        change_keys_dic(dic, keyslist[i], newkeys[i])
def add_list_to_dicofdics(dic, list, subkey):
    # Add to each entry of a dictionary of dictionaries the values stored in a list.
    # To each entry of the dictionary, add the corresponding value from the list
    for (keydic, dicdic), value in zip(dic.items(), list):
        dicdic[subkey] = value
def add_dic_to_dicofdics(dicofdics,dic,key):
    # Add to each entry of a dictionary of dictionaries the values stored in a dictionary, with the same key.
    # To each entry of the dictionary od dictionaries, add the corresponding value from the dictionary
    for clave in dicofdics:
            dicofdics[clave][key] = dic[clave]
def product_columns_dic(dic,key1,key2):
    # Multiply two columns of a dic. Return a dictionary with the same keys and the products
    product_dic = {}
    for key, subdic in dic.items():
        product = subdic[key1] * subdic[key2]
        product_dic[key] = product
    return product_dic
def dicofddics_to_csv(dic,path):
    #Export the content of dictionary to a .csv file. Each entry is in a single row, they keys are in the first and
    #the keys of the sub dictionaries are the headers. (ORDENAR FALTA)
    with open(path, mode='w', newline='') as file:
        # Get all unique fieldnames from the dictionaries and write them as first row
        fieldnames = set()
        for sub_dict in dic.values():
            fieldnames.update(sub_dict.keys())
        fieldnames = list(fieldnames)
        fieldnames.insert(0, 'Building ID')  # Include the 'Key' column if needed
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        # Write the header row (keys of the inner dictionaries)
        writer.writeheader()
        # Write each row (each inner dictionary as a row)
        for key, sub_dict in dic.items():
            # Add the outer key as a column if needed
            sub_dict['Building ID'] = key  # Optionally include the outer key as a column
            writer.writerow(sub_dict)
def expshp_to_dic(path,keystokeep,newkeys):
    #EXPLICAR
    expdic = shp_to_dict(path,keystokeep[0])
    #Añado a la lista de keystokeep la cabedecera de la geometría
    keystokeep.append('geometry')
    # Iteramos sobre el diccionario principal
    for dic in expdic.values():
        # Filtramos el diccionario para conservar solo las claves indicadas
        for key in list(dic.keys()):
            if key not in keystokeep:
                del dic[key]  # Eliminamos las claves que no están en claves_a_conservar
    for i in range(len(newkeys)):
        change_keys_dic(expdic, keystokeep[i+1], newkeys[i])
    return expdic
def change_keys_dic(dic,oldkey,newkey):
    for subdic in dic.values():
            subdic[newkey] = subdic.pop(oldkey)
def add_value_to_dicofidcs(dic,key,value):
    for subdiccionario in dic.values():
        subdiccionario[key] = value
def column_sum(dic, key):
    sum = 0
    for entry in dic.values():
        if key in entry:
            sum += entry[key]
    return sum
def dic_to_csv(dic,path):
    # Abrimos el archivo CSV en modo escritura
    with open(path, mode='w', newline='') as file:
        escritor = csv.DictWriter(file, fieldnames=dic.keys())
        # Escribimos las cabeceras
        escritor.writeheader()
        # Escribimos la fila con los valores del diccionario
        escritor.writerow(dic)

def dic_to_shp(dic,path,crs):
    #Convertir diccionario de diccionarios a diccionario de listas
    columnas = {key: [] for key in dic[list(dic.keys())[0]].keys()}
    # Recorremos el diccionario de diccionarios para extraer las columnas
    for fila in dic.values():
        for columna, valor in fila.items():
            columnas[columna].append(valor)
    #Change the key values to less than 10 characters
    newkeys={'Building ID':'Build Id','Consequences value (€)':'Cons val €','Damage fraction':'Dam frac',\
             'Exposed value (€)':'Exp val €','Hazard scenario':'Haz scen','Impact value (m)':'Imp val m',\
             'geometry':'geometry'}
    columdic = {newkeys[key]: value for key, value in columnas.items()}

    # 2. Crear un GeoDataFrame a partir del diccionario
    gdf = gpd.GeoDataFrame(columdic, geometry='geometry')
    # 3. Definir el sistema de referencia espacial
    gdf=gdf.set_crs(crs)
    # 4. Guardar el GeoDataFrame como un archivo shapefile
    gdf.to_file(path)