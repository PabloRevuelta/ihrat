import pandas as pd
import os

#%%
# Ruta del archivo Excel
archivo_excel = "C:\\Users\\revueltaap\\Desktop\\Funciones España\\Funciones Inventory.xlsx"
output_folder = "C:\\Users\\revueltaap\\Desktop\\salida_txt"

# Cargar todas las hojas del Excel como un diccionario de DataFrames
hojas = pd.read_excel(archivo_excel, sheet_name=None,skiprows=1)

# Guardar cada hoja en un archivo TXT
for nombre_hoja, df in hojas.items():
    # Crear un nombre de archivo basado en el nombre de la hoja
    nombre_txt = f"{nombre_hoja}.txt"

    # Guardar el contenido en formato texto (separado por tabulaciones)
    output_path = os.path.join(output_folder, nombre_txt)
    df.to_csv(output_path, sep='\t', index=False)

    print(f"✅ Guardado: {nombre_txt}")

#%%

import numpy as np
import os
import json

# Carpeta donde están los txt
carpeta_txt = "C:\\Users\\revueltaap\\Desktop\\salida_txt"

ruta_json ="C:\\Users\\revueltaap\\UNICAN\\EMCAN 2024 A2 ADAPTA - Documentos\\02_Tareas\\Proyecto ihrat\\ihrat\\ihrat\\src\\level_3_analysis\\damage_functions\\damage_functions_dictionary.json"

# Si el JSON ya existe, lo cargamos; si no, lo inicializamos
if os.path.exists(ruta_json):
    with open(ruta_json, "r", encoding="utf-8") as f:
        funciones_json = json.load(f)
else:
    funciones_json = {"functions": []}

for archivo in os.listdir(carpeta_txt):
    if archivo.endswith(".txt"):
        # Nombre de la función (sin extensión)
        nombre = os.path.splitext(archivo)[0]

        # Cargar datos: suponemos dos columnas x y y
        ruta = os.path.join(carpeta_txt, archivo)
        datos = np.loadtxt(ruta,skiprows=1)  # usa delimiter="," si tus txt son CSV

        x = datos[:, 0]
        values = datos[:, 1]

        # Añadir función solo si no existe ya
        if not any(f["name"] == nombre for f in funciones_json["functions"]):
            # Guardar en JSON con metadatos
            funciones_json["functions"].append({
                "name": nombre,
                "origen": "Huizinga, J., De Moel, H. and Szewczyk, W., Global flood depth-damage functions: Methodology and the database with guidelines, EUR 28552 EN, Publications Office of the European Union, Luxembourg, 2017, ISBN 978-92-79-67781-6, doi:10.2760/16510, JRC105688.",
                "region": "Europe",
                "property type": "Residential building",
                "application": "Relative",
                "type": "interpolation",
                "variables":['x'],
                "x": x.tolist(),
                "values": values.tolist(),
                "interpolation_type": "linear",
                "asset": "Building Content",
                "units": "% damage"
            })


# Guardar el JSON actualizado
with open(ruta_json, "w", encoding="utf-8") as f:
    json.dump(funciones_json, f, ensure_ascii=False, indent=4)

#%%

import pandas as pd
import os

# Ruta al archivo Excel
archivo_excel = r"C:\Users\revueltaap\Desktop\Global_dam_fun.xlsx"

# Carpeta donde guardar los TXT
carpeta_salida = r"C:\Users\revueltaap\Desktop\salida_txt"
os.makedirs(carpeta_salida, exist_ok=True)

# Leer la hoja del Excel
df = pd.read_excel(archivo_excel, sheet_name="Damage functions")

# Identificar los nombres de columnas de países (desde la cabecera "Damage function")
columnas_paises = ["EUROPE", "North AMERICA", "Centr&South AMERICA", "ASIA", "AFRICA", "OCEANIA", "GLOBAL"]

# Rellenar hacia adelante los tipos de activos (Residential, Commercial, etc.)
df["Damage class"] = df["Damage class"].ffill()

# Recorrer cada tipo de asset
for asset, grupo_asset in df.groupby("Damage class"):
    # Para cada país o región
    for pais in columnas_paises:
        # Crear DataFrame con dos columnas: x (Flood depth) y y (valores)
        data_xy = grupo_asset[["Flood depth [m]", pais]].dropna()

        # Saltar si no hay datos válidos
        if data_xy.empty:
            continue

        # Crear nombre del archivo
        nombre_archivo = f"{asset.replace(' ', '_')}_{pais.replace('&', 'and').replace(' ', '_')}.txt"
        ruta_archivo = os.path.join(carpeta_salida, nombre_archivo)

        # Guardar en TXT separado por tabulaciones
        data_xy.to_csv(ruta_archivo, sep="\t", index=False, header=["x", "y"])

        print(f"✅ Guardado: {ruta_archivo}")
#%%

import numpy as np
import pandas as pd
import os
import json
import country_converter as coco
import pycountry_convert as pc

# ---- Rutas ----
ruta_json = r"C:\Users\revueltaap\UNICAN\EMCAN 2024 A2 ADAPTA - Documentos\02_Tareas\Proyecto ihrat\ihrat\ihrat\src\level_3_analysis\damage_functions\damage_functions_dictionary.json"
archivo_excel = r"C:\Users\revueltaap\Desktop\MaxDamage-Transport.xlsx"

# ---- Tipo de interpolación por defecto ----
tipo_interp = "linear"

# ---- Cargar JSON existente ----

with open(ruta_json, "r", encoding="utf-8") as f:
    funciones_json = json.load(f)

# ---- Cargar Excel con las funciones máximas ----
df_max = pd.read_excel(archivo_excel, header=[0, 1])
paises = df_max["Country"]["Unnamed: 0_level_1"]

def continente_ajustado(nombre_pais):
    # Buscar el país en pycountry por nombre
    cont = coco.convert(names=nombre_pais, to='continent')

    if cont == "America" and nombre_pais in ['United States','Mexico','Canada']:
        return "Global"
    elif cont == "America":
        return "Central and South America"
    elif cont=='Oceania':
        return 'Global'
    elif cont=='Africa':
        return "Global"
    else:
        return cont

paises_lista = paises.tolist()
pais_a_continente = {}
for pais in paises_lista:
    pais_a_continente[pais] = continente_ajustado(pais)


# ---- Crear nuevas funciones basadas en el continente ----
for i, pais in enumerate(paises):
    continente = pais_a_continente.get(pais)
    if not continente:
        print(f"⚠️ No se encontró continente para el país {pais}, se omite")
        continue

    # Seleccionar funciones base para el continente y tipo de propiedad
    funciones_base = [
        f for f in funciones_json["functions"]
        if f.get("property type", "").lower() == "transport"
        and f.get("region", "").lower() == continente.lower()
    ]

    if not funciones_base:
        print(f"⚠️ No se encontró función base para {pais} en el continente {continente}")
        continue

    for col_name, unidad in df_max.columns:
        if col_name == "Country":
            continue

        factor = df_max.loc[i, (col_name, unidad)]
        if pd.isna(factor):
            continue

        # Usar la primera función base del continente (o aplicar lógica diferente si hay varias)
        f_base = funciones_base[0]
        nueva_funcion = f_base.copy()
        nueva_funcion["name"] = f"{f_base['name']}_{pais}_{col_name.replace(' ', '_')}"
        nueva_funcion["region"] = pais  # ahora la función se aplica al país
        nueva_funcion["application"] = "Absolute"
        nueva_funcion["asset"] = col_name
        nueva_funcion["units"] = unidad
        nueva_funcion["y"] = (np.array(f_base["y"]) * factor).tolist()

        funciones_json["functions"].append(nueva_funcion)

    # ---- Guardar el JSON actualizado ----
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(funciones_json, f, ensure_ascii=False, indent=4)
