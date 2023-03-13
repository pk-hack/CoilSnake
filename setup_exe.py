#!/usr/bin/env python3

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--clean',
    'CoilSnake.spec'
])