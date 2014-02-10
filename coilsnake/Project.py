import logging
import os
import yaml

# This is a number which tells you the latest version number for the project
# format. Version numbers are necessary because the format of data files may
# change between versions of CoilSnake.
FORMAT_VERSION = 4

# Names for each version, corresponding the the CS version
VERSION_NAMES = {
    1: "1.0",
    2: "1.1",
    3: "1.2",
    4: "1.3"
}

# The default project filename
PROJECT_FILENAME = "Project.snake"

log = logging.getLogger(__name__)


def getVersionName(version):
    try:
        return VERSION_NAMES[version]
    except KeyError:
        return "???"


class Project:
    def __init__(self):
        self._romtype = "Unknown"
        self._resources = {}
        self._dirName = ""

    def load(self, f, romtype=None):
        log.info("Loading %s", f)
        if isinstance(f, str):
            self._dirName = os.path.dirname(f)
        else:
            self._dirName = os.path.dirname(f.name)

        try:
            if isinstance(f, str):
                f = open(f, 'r')
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            if (romtype is None) or (romtype == data["romtype"]):
                self._romtype = data["romtype"]
                self._resources = data["resources"]
                if "version" in data:
                    self._version = data["version"]
                else:
                    self._version = 1

                if self._resources is None:
                    self._resources = {}
            else:  # Loading a project of the wrong romtype
                self._romtype = romtype
                self._resources = {}
        except IOError:
            # Project file doesn't exist
            if not os.path.exists(self._dirName):
                os.makedirs(self._dirName)
            if romtype is None:
                self._romtype = "Unknown"
            else:
                self._romtype = romtype
            self._resources = {}

    def write(self, filename):
        tmp = {
            'romtype': self._romtype,
            'resources': self._resources,
            'version': FORMAT_VERSION}
        f = open(filename, 'w+')
        yaml.dump(tmp, f, Dumper=yaml.CSafeDumper)
        f.close()

    def type(self):
        return self._romtype

    def version(self):
        return self._version

    def setVersion(self, version):
        self._version = version

    def getResource(self, modName, resourceName, extension="dat", mode="rw"):
        if modName not in self._resources:
            self._resources[modName] = {}
        if resourceName not in self._resources[modName]:
            self._resources[modName][resourceName] = \
                resourceName + "." + extension
        fname = os.path.join(
            self._dirName,
            self._resources[modName][resourceName])
        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))
        f = open(fname, mode)
        return f

    def deleteResource(self, modName, resourceName):
        if modName not in self._resources:
            raise RuntimeError("No such module %s" % modName)
        if resourceName not in self._resources[modName]:
            raise RuntimeError("No such resource %s in module %s" %
                               (resourceName, modName))
        fname = os.path.join(
            self._dirName,
            self._resources[modName][resourceName])
        if os.path.isfile(fname):
            os.remove(fname)
        del self._resources[modName][resourceName]
