import os
import yaml

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
            data = yaml.load(f)
            if (romtype == None) or (romtype == data["romtype"]):
                self._romtype = data["romtype"]
                self._resources = data["resources"]
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
        f = open(filename, 'w')
        yaml.dump(tmp, f)
        f.close()
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
