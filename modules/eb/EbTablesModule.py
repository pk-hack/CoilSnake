import EbModule
from modules.Table import Table, TableEntry, _return, genericEntryGenerator
from modules.TablesModule import TablesModule
from modules.eb.EbBlocksModule import EbDataBlock

import yaml

def ebEntryGenerator(spec, table_map):
    if not spec.has_key("type"):
        return genericEntryGenerator(spec, table_map)
    elif spec['type'] == 'pointer':
        # TODO ccscript label integration
        readF = lambda r,a: r.readMulti(a,spec["size"])
        writeF = lambda r,a,d: r.writeMulti(a, d, spec["size"])
        sizeF = lambda d: spec["size"]
        loadF = lambda x: int(x[1:], 16)
        dumpF = lambda x: '$' + hex(x)[2:]
        return TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
    elif spec['type'] == 'palette':
        readF = lambda r,a: EbModule.readPalette(r, a, spec["size"]/2)
        writeF = lambda r,a,d: EbModule.writePalette(r, a, d)
        sizeF = lambda d: spec["size"]
        loadF = lambda x: map(lambda y: tuple(map(int,y[1:-1].split(','))), x)
        dumpF = lambda x: map(str,x)
        return TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
    elif spec['type'] == 'standardtext':
        readF = lambda r,a: EbModule.readStandardText(r, a, spec["size"])
        writeF = lambda r,a,d: EbModule.writeStandardText(r, a, d, spec["size"])
        sizeF = lambda d: spec["size"]
        return TableEntry(spec["name"], readF, writeF, sizeF, _return, _return)
    else:
        return genericEntryGenerator(spec, table_map)

class EbTable(Table):
    tableEntryGenerator = staticmethod(ebEntryGenerator)
    def __init__(self, addr, table_map=None):
        if table_map == None:
            with open("structures/eb.yml") as f:
                i=1
                for doc in yaml.load_all(f):
                    if i == 1:
                        i += 1
                    elif i == 2:
                        table_map = doc
                        break
        Table.__init__(self,addr,table_map)
        self._addr = EbModule.toRegAddr(self._addr)

class EbTablesModule(EbModule.EbModule):
    _name = "EarthBound Tables"
    _tableIDs = [ ]
    def __init__(self):
        self._tm = TablesModule("structures/eb.yml", EbTable, self._tableIDs)
    def readFromRom(self, rom):
        self._tm.readFromRom(rom)
    def writeToRom(self, rom):
        self._tm.writeToRom(rom)
    def writeToProject(self, resourceOpener):
        self._tm.writeToProject(resourceOpener)
    def readFromProject(self, resourceOpener):
        self._tm.readFromProject(resourceOpener)
