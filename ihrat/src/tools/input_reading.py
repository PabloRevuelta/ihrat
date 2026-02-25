import geopandas as gpd
from pathlib import Path
import csv
import fiona

def reading_folder_files(folder_name,extensions):
    """
        Search recursively inside a predefined inputs folder and return
        all files matching the given extensions.

        PARAMETERS
        ----------
        folder_name : str
            Name of the subfolder inside the global 'inputs' directory.

        extensions : tuple or str
            File extensions to filter (e.g., '.shp' or ('.shp', '.tif')).

        RETURNS
        -------
        dict
            Dictionary where:
            - key   : filename without extension
            - value : absolute Path to the file
        """
    # --------------------------------------------------------------
    # 1. Build the absolute path to the target folder
    #    Assumes project structure:
    #    project_root/
    #        inputs/
    #            <folder_name>/
    # --------------------------------------------------------------
    folder_path=Path.cwd().parent.parent.parent/'inputs'/folder_name
    if not folder_path.exists():
        raise FileNotFoundError(f"Input folder not found: {folder_path}")
    # --------------------------------------------------------------
    # 2. Recursively search for files matching the desired extensions
    # --------------------------------------------------------------
    files = [file for file in folder_path.rglob('*') if file.is_file() and file.name.endswith(extensions)]
    # --------------------------------------------------------------
    # 3. Create a dictionary:
    #    key   → filename without extension
    #    value → absolute resolved path
    # --------------------------------------------------------------
    files_dic = {file.stem: file.resolve() for file in files}

    return files_dic

def reading_files(folder,extensions):
    """
        Read all files in a folder with the specified extensions and
        enrich their metadata with additional information.

        PARAMETERS
        ----------
        folder : str or Path
            Path to the directory containing the files to read.

        extensions : tuple or list
            Allowed file extensions (e.g., ('.shp', '.tif')).

        RETURNS
        -------
        dict
            Dictionary where:
            - key   : file name (without extension)
            - value : dictionary containing:
                - 'path'      : full file path
                - 'extension' : file extension
                - 'crs'       : coordinate reference system (only for .shp files)
        """

    # --------------------------------------------------------------
    # 1. Retrieve files in the folder with the desired extensions
    # --------------------------------------------------------------
    files_dic = reading_folder_files(folder, extensions)
    # --------------------------------------------------------------
    # 2. Build an extended dictionary with metadata
    # --------------------------------------------------------------
    extended_dic={}
    for name, path in files_dic.items():
        # Case A: Shapefile → include CRS information
        if path.suffix=='.shp':
            with fiona.open(path) as src:
                extended_dic[name]={'path':path, 'crs':src.crs, 'extension':path.suffix}
        # Case B: Other raster/vector types → only store basic info
        else:
            extended_dic[name] = {'path': path, 'extension': path.suffix}
    return extended_dic

def reading_input(folder,extension):
    files_dic =reading_folder_files(folder, extension)
    key = list(files_dic.keys())[0]
    file_path = files_dic[key]
    if extension=='.csv':
        return key, csv_to_dic(file_path)
    elif extension=='.shp':
        return key, shp_to_dic(file_path,key)
    return None

def reading_shp_to_dic(folder):
    files_dic =reading_folder_files(folder, '.shp')
    key = list(files_dic.keys())[0]
    file=files_dic[key]
    return shp_to_dic(file,['subarea_fu','geometry']),file

def shp_to_dic(file,keys):
    """
        Convert a shapefile into a dictionary structure using selected fields.

        The shapefile is first loaded as a GeoDataFrame, then transformed into
        a nested dictionary where:
            - outer key   → element identifier (first field in `keys`)
            - inner dict  → attribute values for that element

        PARAMETERS
        ----------
        file : str or Path
            Path to the input shapefile.

        keys : list[str]
            List of column names to extract from the shapefile.
            The first key is used as the unique element ID.

        RETURNS
        -------
        tuple
            dic : dict
                Dictionary representation of the shapefile attributes.
            crs : CRS object
                Coordinate Reference System of the shapefile.
        """
    # ------------------------------------------------------------------
    # 1. Read shapefile into a GeoDataFrame
    # ------------------------------------------------------------------
    geodataframe = gpd.read_file(file)
    # Store Coordinate Reference System for later spatial outputs
    crs=geodataframe.crs
    # ------------------------------------------------------------------
    # 2. Convert selected columns into dictionary format
    #    - Select only requested fields
    #    - Set first key as index (unique element ID)
    #    - Transpose and convert to nested dictionary
    # ------------------------------------------------------------------
    dic = geodataframe[keys].set_index(keys[0]).T.to_dict('dict')
    return dic,crs

def csv_to_dic(file):
    main_dic = {}
    with open(file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = row[reader.fieldnames[0]]  # Use the first column as the key
            # Remove the key from the value dictionary
            value = {k: v for k, v in row.items() if k != reader.fieldnames[0]}
            main_dic[key] = value
    return main_dic

