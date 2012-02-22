import os
import yaml

class Project:
    def __init__(self, fname, romtype=None):
        if romtype == None:
            data = yaml.load(fname)
            self._dirName = os.path.dirname(fname.name)
            self._romtype = data["romtype"]
            self._resources = data["resources"]
        else:
            self._dirName = os.path.dirname(fname)
            self._romtype = romtype
            try:
                f = open(fname)
                data = yaml.load(f)
                if (self._romtype == data["romtype"]):
                    self._resources = data["resources"]
                else:
                    self._resources = { }
            except IOError:
                # Project file doesn't exist
                if not os.path.exists(os.path.dirname(self._dirName)):
                    os.makedirs(self._dirName)
                self._resources = { }
    def type(self):
        return self._romtype
    def getResource(self, modName, resourceName, extension="dat", mode="rw"):
        if modName not in self._resources:
            self._resources[modName] = { }
        if resourceName not in self._resources[modName]:
            self._resources[modName][resourceName] = \
                modName+"_"+resourceName+"."+extension
        fname = os.path.join(self._dirName,self._resources[modName][resourceName])
        f = open(fname, mode)
        return f
    def write(self, filename):
        tmp = { }
        tmp['romtype'] = self._romtype
        tmp['resources'] = self._resources
        f = open(filename, 'w')
        yaml.dump(tmp, f)
        f.close()
