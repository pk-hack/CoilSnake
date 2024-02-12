#!/usr/bin/env python
import glob
import os
from coilsnake.ui.information import VERSION

def rename_exe():
    exe_paths = glob.glob('dist/CoilSnake*')
    if not exe_paths:
        print("Couldn't locate CoilSnake executable. Doing nothing...")
        return
    for exe_path in exe_paths:
        new_exe_path = exe_path.replace('CoilSnake', f'CoilSnake-{VERSION}')
        if exe_path != new_exe_path:
            os.rename(exe_path, new_exe_path)

if __name__ == '__main__':
    rename_exe()
