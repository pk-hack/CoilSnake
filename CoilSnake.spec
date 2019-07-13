# -*- mode: python ; coding: utf-8 -*-

import sys
from setuptools.sandbox import run_setup

run_setup('setup.py', ['build_ext'])

hiddenimports = []
hidden_import_list = ['PIL._tkinter_finder']

with open(os.path.join("coilsnake", "assets", "modulelist.txt"), "r") as f:
    for line in f:
        line = line.rstrip("\n")

        if line[0] == "#":
            continue

        module = "coilsnake.modules." + line
        hidden_import_list.append(module)

pyver = str(sys.version_info[0]) + "." + str(sys.version_info[1])

a = Analysis(
    ['script/gui.py'],
    pathex = ['.'],
    binaries = [(
        'build/lib.' + sys.platform + '*' + pyver + '/coilsnake',
        'coilsnake')
    ],
    datas = [('coilsnake/assets', 'coilsnake/assets')],
    hiddenimports = hidden_import_list,
    hookspath = [],
    runtime_hooks = [],
    excludes = [
        '_bz2',
        '_ssl',
        '_socket',
        '_lzma',
        'readline',
        'termios',
        'PIL._webp',
        'PySide',
        'PyQt4',
        'PyQt5'
    ],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = None,
    noarchive = False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

if len(sys.argv) > 1 and sys.argv[1] == 'debug':
    exe = EXE(
        pyz,
        [],
        a.scripts,
        exclude_binaries=True,
        name='CoilSnake',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon='coilsnake/assets/images/icon.ico'
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='CoilSnake'
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='CoilSnake',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon='coilsnake/assets/images/icon.ico'
    )