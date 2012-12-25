from modules.Progress import updateProgress
import yaml

def replaceField(fname, oldField, newField, valueMap, resourceOpenerR,
        resourceOpenerW):
    if newField == None:
        newField = oldField
        valueMap = dict((k.lower() if (type(k) == str) else k, v) for k,v in valueMap.iteritems())
        with resourceOpenerR(fname, 'yml') as f:
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            for i in data:
                if data[i][oldField] in valueMap:
                    if type(data[i][oldField]) == str:
                        data[i][newField] = valueMap[data[i][oldField].lower()].lower()
                    else:
                        data[i][newField] = valueMap[data[i][oldField]].lower()
                else:
                    data[i][newField] = data[i][oldField]
                if newField != oldField:
                    del data[i][oldField]
        with resourceOpenerW(fname, 'yml') as f:
            yaml.dump(data, f, default_flow_style=False,
                    Dumper=yaml.CSafeDumper)

class GenericModule:
    def name(self):
        return self._name
    def compatibleWithRomtype(self, romtype):
        return True
    def free(self):
        pass
    def freeRanges(self):
        return []
    def readFromRom(self, rom):
        updateProgress(50)
    def writeToRom(self, rom):
        updateProgress(50)
    def readFromProject(self, resourceOpener):
        updateProgress(50)
    def writeToProject(self, resourceOpener):
        updateProgress(50)
    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
            resourceOpenerW):
        updateProgress(100)
