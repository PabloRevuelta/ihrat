
def add_listofdics_to_dicofdics(dic,listofdics,new_keys):
    #Add to each entry of a dictionary of dictionaries the values stored in a list of dictionaries.
    #To each entry of the dictionary, add the corresponding dictionary from the list. Also change the keys to the new
    #ones
    for i, j in zip(dic, listofdics):
        dic[i].update(j)

    #List the old keys
    keys_list = list(set(key for dictionary in listofdics for key in dictionary.keys()))
    #Look for then in the dictionary and change them with the new ones
    for i in range(len(keys_list)):
        change_keys_dic(dic, keys_list[i], new_keys[i])

def add_dic_to_dicofdics(dicofdics,dic,key):
    # Add to each entry of a dictionary of dictionaries the values stored in a dictionary, with the same key.
    # To each entry of the dictionary od dictionaries, add the corresponding value from the dictionary
    for clave in dicofdics:
            dicofdics[clave][key] = dic[clave]

def product_columns_dic(dic,key1,key2):
    # Multiply two columns of a dic. Return a dictionary with the same keys and the products
    product_dic = {}
    for key, sub_dic in dic.items():
        product = round(sub_dic[key1] * sub_dic[key2], 3)
        product_dic[key] = product
    return product_dic

def change_keys_dic(dic,old_key,new_key):
    #Go through all subdictionaries in a dic. Detect if old_key is in sub_dic. If not, do nothing.
    #If yes, change it with the new one
    for sub_dic in dic.values():
            sub_dic[new_key] = sub_dic.pop(old_key)

def add_value_to_dicofdics(dic,key,value):
    #Given a dictionary of dictionaries, adds the given value to a new entry of all the subdics, with the given key
    for sub_dic in dic.values():
        sub_dic[key] = value

def column_sum(dic, key):
    summation = 0
    for entry in dic.values():
        if key in entry:
            summation += entry[key]
    return summation


