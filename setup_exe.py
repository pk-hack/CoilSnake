#!/usr/bin/env python

import os
from distutils.core import setup, Extension

import py2exe

data_files = []
for root, sub_folders, files in os.walk(os.path.join("coilsnake", "assets")):
    directory_file_list = []
    for f in files:
        directory_file_list.append(os.path.join(root, f))
    data_files.append((root, directory_file_list))

include_module_list = ["CCScriptWriter.CCScriptWriter"]
with open(os.path.join("coilsnake", "assets", "modulelist.txt"), "r") as f:
    for line in f:
        line = line.rstrip("\n")
        if line[0] == "#":
            continue
        include_module_list.append("coilsnake.modules." + line)

setup(
    name="coilsnake",
    version="2.0",
    description="CoilSnake",
    url="http://kiij.github.io/CoilSnake",
    packages=["coilsnake"],
    data_files=data_files,

    ext_modules=[
        Extension("coilsnake.util.eb.native_comp", ["coilsnake/util/eb/native_comp.c"])
    ],

    windows=[{"script": os.path.join("script", "gui.py"),
              "icon_resources": [(1, os.path.join("coilsnake", "assets", "images", "exe_icon.ico"))],
              "dest_base": "CoilSnake"}],
    options={"py2exe": {"includes": include_module_list,
                        "bundle_files": 2,
                        "optimize": 2,
                        "skip_archive": True}},
)