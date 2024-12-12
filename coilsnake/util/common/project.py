import logging

import os

from coilsnake.exceptions.common.exceptions import CoilSnakeError
from coilsnake.util.common.yml import yml_load, yml_dump


log = logging.getLogger(__name__)

# This is a number which tells you the latest version number for the project
# format. Version numbers are necessary because the format of data files may
# change between versions of CoilSnake.

FORMAT_VERSION = 13

# Names for each version, corresponding the the CS version
VERSION_NAMES = {
    1:  "1.0",
    2:  "1.1",
    3:  "1.2",
    4:  "1.3",
    5:  "2.0.4",
    6:  "2.1",
    7:  "2.2",
    8:  "2.3.1",
    9:  "3.33",
    10: "4.0",
    11: "4.1",
    12: "4.2",
    13: "NEXT"
}

# The default project filename
PROJECT_FILENAME = "Project.snake"


def get_version_name(version):
    try:
        return VERSION_NAMES[version]
    except KeyError:
        return "Unknown Version"


class Project(object):
    def __init__(self):
        self.romtype = "Unknown"
        self._resources = {}
        self._dir_name = ""

    def load(self, f, romtype=None):
        if isinstance(f, str):
            self._dir_name = os.path.dirname(f)
        else:
            self._dir_name = os.path.dirname(f.name)

        try:
            if isinstance(f, str):
                f = open(f, 'r')
            data = yml_load(f)
            if (romtype is None) or (romtype == data["romtype"]):
                self.romtype = data["romtype"]
                self._resources = data["resources"]
                if "version" in data:
                    self.version = data["version"]
                else:
                    self.version = 1

                if self._resources is None:
                    self._resources = {}
            else:  # Loading a project of the wrong romtype
                self.romtype = romtype
                self._resources = {}
        except IOError:
            # Project file doesn't exist
            if not os.path.exists(self._dir_name):
                os.makedirs(self._dir_name)
            if romtype is None:
                self.romtype = "Unknown"
            else:
                self.romtype = romtype
            self._resources = {}

    def write(self, filename):
        tmp = {
            'romtype': self.romtype,
            'resources': self._resources,
            'version': FORMAT_VERSION}
        f = open(filename, 'w+')
        yml_dump(tmp, f)
        f.close()

    def get_resource(self, module_name, resource_name, extension="dat", mode="r+", encoding=None, newline=None):
        if module_name not in self._resources:
            self._resources[module_name] = {}
        if resource_name not in self._resources[module_name]:
            self._resources[module_name][resource_name] = resource_name + "." + extension
        fname = os.path.join(self._dir_name, self._resources[module_name][resource_name])
        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))
        f = open(fname, mode, encoding=encoding, newline=newline)
        return f

    def delete_resource(self, module_name, resource_name):
        if module_name not in self._resources:
            raise CoilSnakeError("No such module {}".format(module_name))
        if resource_name not in self._resources[module_name]:
            raise CoilSnakeError("No such resource {} in module {}".format(resource_name, module_name))
        fname = os.path.join(self._dir_name, self._resources[module_name][resource_name])
        if os.path.isfile(fname):
            os.remove(fname)
        del self._resources[module_name][resource_name]
