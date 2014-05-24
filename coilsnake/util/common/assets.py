import os

from coilsnake.root import ASSET_PATH


def asset_path(path):
    return os.path.join(ASSET_PATH, os.path.join(*path))


def open_asset(*path):
    return open(asset_path(path), 'r')


def asset_exists(*path):
    return os.path.exists(asset_path(path))


def ccscript_library_path():
    return asset_path(["mobile-sprout", "lib"])