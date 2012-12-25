import Eb0Module
from modules.Table import Table, IntTableEntry, genericEntryGenerator
from modules.TablesModule import TablesModule

import yaml

def eb0EntryGenerator(spec, table_map):
    if not spec.has_key("type"):
        return genericEntryGenerator(spec, table_map)
    else:
        return genericEntryGenerator(spec, table_map)


class Eb0Table(Table):
    tableEntryGenerator = staticmethod(eb0EntryGenerator)
    eb_table_map = None
    def __init__(self, addr):
        if Eb0Table.eb_table_map == None:
            with open("resources/structures/eb0.yml") as f:
                i=1
                for doc in yaml.load_all(f, Loader=yaml.CSafeLoader):
                    if i == 1:
                        i += 1
                    elif i == 2:
                        Eb0Table.eb_table_map = doc
                        break
        Table.__init__(self,addr,Eb0Table.eb_table_map)
        self._addr = Eb0Module.toRegAddr(self._addr)

class Eb0TablesModule(Eb0Module.Eb0Module):
    _name = "EarthBound Zero Tables"
    _tableIDs = [ ]
    def __init__(self):
        self._tm = TablesModule(Eb0Table, self._tableIDs)
    def free(self):
        self._tm.free()
    def readFromRom(self, rom):
        self._tm.readFromRom(rom)
    def writeToRom(self, rom):
        self._tm.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        self._tm.writeToProject(resourceOpener)
    def readFromProject(self, resourceOpener):
        self._tm.readFromProject(resourceOpener)
