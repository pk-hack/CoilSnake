import EbModule
from modules.Table import Table, TableEntry, _return, genericEntryGenerator
from modules.TablesModule import TablesModule
from modules.eb.EbBlocksModule import EbDataBlock

import yaml

class EbTableEntryPointerToBlock(TableEntry):
    def __init__(self, tep, BlockClass, blockSpec):
        self._data = BlockClass(blockSpec)
        self._tep = tep
        self.name = self._tep.name
    def readFromRom(self, rom, addr):
        self._tep.readFromRom(rom, addr)
        # Assumes that Tableentry._data is the SNES ptr
        block_addr = EbModule.toRegAddr(self._tep._data)
        self._data.readFromRom(rom, block_addr)
    def writeToRom(self, rom, addr):
        new_block_addr = self._data.writeToFree(rom)
        self._tep.set('$' + hex(EbModule.toSnesAddr(new_block_addr))[2:])
        self._tep.writeToRom(rom, addr)
    def size(self):
        return self._tep.size()
    def set(self, str):
        self._data.set(str)
    def dump(self):
        return self._data.dump()

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
        te = TableEntry(spec["name"], readF, writeF, sizeF, loadF, dumpF)
        if spec.has_key('points to'):
            return EbTableEntryPointerToBlock(te, EbDataBlock,
                    table_map[spec['points to']])
        else:
            return te
    else:
        return genericEntryGenerator(spec, table_map)

class EbTable(Table):
    tableEntryGenerator = staticmethod(ebEntryGenerator)
    def __init__(self, addr, spec):
        Table.__init__(self,addr,spec)
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
