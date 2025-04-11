
def add_listofdics_to_dicofdics(dic,listofdics,newkeys):
    #Add to each entry of a dictionary of dictionaries the values stored in a list of dictionaries.
    #To each entry of the dictionary, add the corresponding dictionary from the list. Also change the keys to the new
    #ones
    for i, j in zip(dic, listofdics):
        dic[i].update(j)

    #List the old keys
    keyslist = list(set(key for diccionario in listofdics for key in diccionario.keys()))
    #Look for then in the dictionary and change them with the new ones
    for i in range(len(keyslist)):
        change_keys_dic(dic, keyslist[i], newkeys[i])

def add_dic_to_dicofdics(dicofdics,dic,key):
    # Add to each entry of a dictionary of dictionaries the values stored in a dictionary, with the same key.
    # To each entry of the dictionary od dictionaries, add the corresponding value from the dictionary
    for clave in dicofdics:
            dicofdics[clave][key] = dic[clave]

def product_columns_dic(dic,key1,key2):
    # Multiply two columns of a dic. Return a dictionary with the same keys and the products
    product_dic = {}
    for key, subdic in dic.items():
        product = round(subdic[key1] * subdic[key2], 3)
        product_dic[key] = product
    return product_dic

def change_keys_dic(dic,oldkey,newkey):
    #Go through all subdictionaries in a dic. Detectc if oldkey is in subdic. If not, does nothing.
    #If yes, change it with the new one
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


