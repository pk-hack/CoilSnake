import GenericModule
from modules.Table import Table
from modules.Progress import updateProgress

import yaml

# For encoding/decoding text entries
# Note: this assumes only 1-character replacements
#class TextTable:
#    def __init__(self, decDict):
#        self._decDict = decDict
#        self._encDict = dict((v,k) for k, v in decDict.iteritems())
#    def decode(self, rom, addr, terminator=None):

class TablesModule(GenericModule.GenericModule):
    _name = "Generic Tables"
    def __init__(self, TableClass, tableIDs):
        self._tables = map(lambda x: TableClass(x), tableIDs)
        self._pct = 50.0/len(self._tables)
    def free(self):
        for t in self._tables:
            del(t)
    def readFromRom(self, rom):
        for t in self._tables:
            t.readFromRom(rom)
            updateProgress(self._pct)
    def writeToRom(self, rom):
        for t in self._tables:
            t.writeToRom(rom)
            updateProgress(self._pct)
    def writeToProject(self, resourceOpener):
        for t in self._tables:
            t.writeToProject(resourceOpener)
            updateProgress(self._pct)
    def readFromProject(self, resourceOpener):
        for t in self._tables:
            t.readFromProject(resourceOpener)
            updateProgress(self._pct)
