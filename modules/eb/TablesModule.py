import EbModule
from EbTable import EbTable

import yaml

class TablesModule(EbModule.EbModule):
    _name = "Tables"
    def __init__(self):
        self._tables = []
        with open('games/eb.yml') as f:
            data = yaml.load(f)
            for i in data:
                if data[i]['type'] == 'data':
                    self._tables.append(EbTable(i, data[i]))
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
