from pathlib import Path
import os
import ast

def reading_files(folder_name,extensions):
    folder = Path.cwd().parent.parent / folder_name
    files = os.listdir(folder)
    #files = [f for f in files if os.path.isfile(os.path.join(folder, f))]
    files = [f for f in files if f.endswith(extensions)]
    return files

def reading_folder_files(folder_name,extension):
    folder_path=Path.cwd().parent.parent/'inputs'/folder_name
    #Search for all the files with the extension in the folder and add their local path to the list
    files_list = [os.path.splitext(os.path.relpath(file, folder_path))[0] for file in folder_path.rglob('*'+extension) if file.is_file()]
    return files_list

def extraer_funciones_ast(ruta_archivo):
    with open(ruta_archivo, "r") as archivo:
        codigo = archivo.read()
    tree = ast.parse(codigo)

    funciones = []
    for nodo in tree.body:
        if isinstance(nodo, ast.FunctionDef):
            nombre_funcion = nodo.name
            inicio = nodo.lineno - 1
            final = nodo.end_lineno
            lineas = codigo.splitlines()[inicio:final]
            funciones.append((nombre_funcion, '\n'.join(lineas)))  # 👈 tupla (nombre, código)
    return funciones