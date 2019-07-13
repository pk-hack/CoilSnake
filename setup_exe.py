#!/usr/bin/env python3

import PyInstaller.__main__

PyInstaller.__main__.run([
    '--windowed',
    '--noconsole',
    '--clean',
    'CoilSnake.spec'
])