import os
import sys

from coilsnake.root import ASSET_PATH


def asset_path(path):
    return os.path.join(ASSET_PATH, os.path.join(*path))


def open_asset(*path):
    return open(asset_path(path), 'r')


def ccc_file_name():
    if sys.platform == "win32" or sys.platform == "cygwin":
        return asset_path("bin", "ccc.exe")
    else:
        return asset_path("bin", "ccc")