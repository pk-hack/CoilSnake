from coilsnake.modules import GenericModule
from coilsnake.Progress import updateProgress

# For encoding/decoding text entries
# Note: this assumes only 1-character replacements
# class TextTable:
#    def __init__(self, decDict):
#        self._decDict = decDict
#        self._encDict = dict((v,k) for k, v in decDict.iteritems())
#    def decode(self, rom, addr, terminator=None):


class TablesModule(GenericModule.GenericModule):
    NAME = "Generic Tables"

    def __init__(self, TableClass, tableIDs):
        GenericModule.GenericModule.__init__(self)
        self._tables = map(lambda x: TableClass(x), tableIDs)
        self._pct = 50.0 / len(self._tables)

    def __exit__(self, type, value, traceback):
        for t in self._tables:
            del t

    def read_from_rom(self, rom):
        for t in self._tables:
            t.readFromRom(rom)
            updateProgress(self._pct)

    def write_to_rom(self, rom):
        for t in self._tables:
            t.writeToRom(rom)
            updateProgress(self._pct)

    def write_to_project(self, resourceOpener):
        for t in self._tables:
            t.writeToProject(resourceOpener)
            updateProgress(self._pct)

    def read_from_project(self, resourceOpener):
        for t in self._tables:
            t.readFromProject(resourceOpener)
            updateProgress(self._pct)
