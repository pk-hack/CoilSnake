import os

from coilsnake.root import ASSET_PATH


def asset_path(path):
    return os.path.join(ASSET_PATH, os.path.join(*path))


def open_asset(*path):
    return open(asset_path(path), 'r')