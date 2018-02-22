#!/usr/bin/env python

from distutils.core import Extension
from cx_Freeze import setup, Executable

import os
import sys
import platform

# Workaround for tcl/tk with cx_freeze
# From https://stackoverflow.com/questions/35533803/keyerror-tcl-library-when-i-use-cx-freeze
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

data_files = []
for root, sub_folders, files in os.walk(os.path.join("coilsnake", "assets")):
    directory_file_list = []
    for f in files:
        directory_file_list.append(os.path.join(root, f))
    data_files.append((root, directory_file_list))

# Get the list of all dynamically loaded modules
include_module_list = []
with open(os.path.join("coilsnake", "assets", "modulelist.txt"), "r") as f:
    for line in f:
        line = line.rstrip("\n")
        if line[0] == "#":
            continue
        include_module_list.append("coilsnake.modules." + line)

# Manually include tk and tcl dependencies, these aren't automatically included
build_exe_options = {
        "packages": include_module_list,
        'include_files': [
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
         ],
         "optimize": 2}


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

extra_compile_args = []

if platform.system() != "Windows":
    extra_compile_args = ["-std=c99"]

setup(      
    name="coilsnake",
    version="3.33",
    description="CoilSnake",
    url="https://mrtenda.github.io/CoilSnake",
    packages=["coilsnake"],
    data_files=data_files,

    ext_modules=[
        Extension(
            "coilsnake.util.eb.native_comp",
            ["coilsnake/util/eb/native_comp.c", "coilsnake/util/eb/exhal/compress.c"],
            extra_compile_args=extra_compile_args,
        )
    ],
    options = {"build_exe": build_exe_options},
    executables = [Executable(
        os.path.join("script", "gui.py"),
        base=base,
        targetName="CoilSnake.exe",
        icon= os.path.join("coilsnake", "assets", "images", "icon.ico")
    )])
