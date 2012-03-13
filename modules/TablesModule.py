import GenericModule
from modules.Table import Table

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
    def __init__(self, structureFile, TableClass):
        self._tables = []
        with open(structureFile) as f:
            i=1
            for doc in yaml.load_all(f):
                if i == 1:
                    # TODO Do stuff with the text table data and whatnot
                    i += 1
                elif i == 2:
                    # Load the Tables
                    for addr in doc:
                        if (doc[addr]['type'] == 'data' and
                                doc[addr].has_key('entries') and
                                doc[addr].has_key('name')):
                            self._tables.append(TableClass(addr, doc))
                    break
    def readFromRom(self, rom):
        for t in self._tables:
           t.readFromRom(rom)
    def writeToRom(self, rom):
        for t in self._tables:
            t.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        for t in self._tables:
            f = resourceOpener(t._name, 'yml')
            f.write(t.dump())
            f.close()
    def readFromProject(self, resourceOpener):
        for t in self._tables:
            f = resourceOpener(t._name, 'yml')
            contents = f.read()
            f.close()
            t.load(contents)
