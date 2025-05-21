from pathlib import Path
import os

def reading_files(foldername):
    folder = Path.cwd().parent.parent / foldername
    files = os.listdir(folder)
    files = [f for f in files if os.path.isfile(os.path.join(folder, f))]
    return files