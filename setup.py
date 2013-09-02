#! /usr/bin/env python

from distutils.core import setup
import py2exe
import os

from CoilSnake import _VERSION

# Compile a list of all the resource files and where they should be copied to.
dataFiles = []
for root, subFolders, files in os.walk('resources'):
    directoryFileList = []
    for f in files:
        directoryFileList.append(os.path.join(root, f))
    dataFiles.append((root, directoryFileList))

# Compile a list of all the modules which aren't imported normally.
includeModuleList = []
with open('resources/modulelist.txt', 'r') as f:
    for line in f:
        line = line.rstrip('\n')
        if line[0] == '#':
            continue
        includeModuleList.append("modules." + line)

setup(name='CoilSnake',
    version=_VERSION,
    windows=['CoilSnakeGUI.py'],
    data_files=dataFiles,
    zipfile=None,
    options={"py2exe": {"includes": includeModuleList}})