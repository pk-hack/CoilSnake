import os
import yaml

# This is a number which tells you the latest version number for the project
# format. Version numbers are necessary because the format of data files may
# change between versions of CoilSnake.
FORMAT_VERSION = 3

# Names for each version, corresponding the the CS version
VERSION_NAMES = {
        1: "1.0",
        2: "1.1",
        3: "1.1.1",
        }

def getVersionName(version):
    try:
        return VERSION_NAMES[version]
    except KeyError:
        return "???"

# The default project filename
PROJECT_FILENAME = "Project.snake"

class Project:
    def __init__(self):
        self._romtype = "Unknown"
        self._resources = { }
        self._dirName = ""
    def load(self, f, romtype=None):
        if type(f) == str:
            self._dirName = os.path.dirname(f)
        else:
            self._dirName = os.path.dirname(f.name)

        try:
            if (type(f) == str):
                f = open(f, 'r') 
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            if (romtype == None) or (romtype == data["romtype"]):
                self._romtype = data["romtype"]
                self._resources = data["resources"]
                if "version" in data:
                    self._version = data["version"]
                else:
                    self._version = 1

                if self._resources == None:
                    self._resources = { }
            else: # Loading a project of the wrong romtype
                self._romtype = romtype
                self._resources = { }
        except IOError:
            # Project file doesn't exist
            if not os.path.exists(self._dirName):
                os.makedirs(self._dirName)
            if romtype == None:
                self._romtype = "Unknown"
            else:
                self._romtype = romtype
            self._resources = { }
    def write(self, filename):
        tmp = { }
        tmp['romtype'] = self._romtype
        tmp['resources'] = self._resources
        tmp['version'] = FORMAT_VERSION
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
            self._resources[modName] = { }
        if resourceName not in self._resources[modName]:
            self._resources[modName][resourceName] = \
                resourceName+"."+extension
        fname = os.path.join(self._dirName,self._resources[modName][resourceName])
        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))
        f = open(fname, mode)
        return f
