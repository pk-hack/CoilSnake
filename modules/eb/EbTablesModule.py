import yaml

import EbModule
from modules.Table import Table, IntTableEntry, genericEntryGenerator
from modules.TablesModule import TablesModule


class PointerTableEntry(IntTableEntry):
    def load(self, data):
        if not isinstance(data, str):
            raise RuntimeError("Invalid pointer or label: '%s'" % data)
        elif data[0] == '$':
            self._data = int(data[1:], 16)
        else:
            try:
                self._data = EbModule.address_labels[data]
            except KeyError:
                raise RuntimeError("Invalid label: '" + data + "'")

    def dump(self):
        return '$' + hex(self._data)[2:]


class PaletteTableEntry:
    def __init__(self, name, size):
        self.name = name
        self._size = size

    def size(self):
        return self._size

    def readFromRom(self, rom, addr):
        self._data = EbModule.readPalette(rom, addr, self._size / 2)

    def writeToRom(self, rom, addr):
        EbModule.writePalette(rom, addr, self._data)

    def load(self, data):
        self._data = map(lambda y: tuple(map(int, y[1:-1].split(','))), data)

    def dump(self):
        return map(str, self._data)

    def setVal(self, val):
        self._data = val

    def val(self):
        return self._data


class TextTableEntry:
    def __init__(self, name, size):
        self.name = name
        self._size = size

    def size(self):
        return self._size

    def readFromRom(self, rom, addr):
        self._data = EbModule.readStandardText(rom, addr, self._size)

    def writeToRom(self, rom, addr):
        EbModule.writeStandardText(rom, addr, self._data, self._size)

    def writeToFree(self, rom):
        loc = rom.getFreeLoc(self._size)
        self.writeToRom(rom, loc)
        return loc

    def load(self, data):
        self._data = data

    def dump(self):
        return self._data

    def setVal(self, val):
        self._data = val

    def val(self):
        return self._data


class NullTerminatedTextTableEntry(TextTableEntry):
    def writeToRom(self, rom, addr):
        EbModule.writeStandardText(rom, addr, self._data, self._size - 1)
        rom[addr + self._size - 1] = 0


def ebEntryGenerator(spec, table_map):
    if "type" not in spec:
        return genericEntryGenerator(spec, table_map)
    elif spec['type'] == 'pointer':
        return PointerTableEntry(spec["name"], spec["size"])
    elif spec['type'] == 'palette':
        return PaletteTableEntry(spec["name"], spec["size"])
    elif spec['type'] == 'standardtext':
        return TextTableEntry(spec["name"], spec["size"])
    elif spec['type'] == 'standardtext null-terminated':
        return NullTerminatedTextTableEntry(spec["name"], spec["size"])
    else:
        return genericEntryGenerator(spec, table_map)


class EbTable(Table):
    tableEntryGenerator = staticmethod(ebEntryGenerator)
    eb_table_map = None

    def __init__(self, addr):
        if EbTable.eb_table_map is None:
            # print "Loading eb.yml"
            with open("resources/structures/eb.yml") as f:
                i = 1
                for doc in yaml.load_all(f, Loader=yaml.CSafeLoader):
                    if i == 1:
                        i += 1
                    elif i == 2:
                        EbTable.eb_table_map = doc
                        break
                        # print "Done"
        Table.__init__(self, addr, EbTable.eb_table_map)
        self._addr = EbModule.toRegAddr(self._addr)


class EbTablesModule(EbModule.EbModule):
    NAME = "EarthBound Tables"
    _tableIDs = []

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._tm = TablesModule(EbTable, self._tableIDs)

    def __exit__(self, type, value, traceback):
        self._tm.__exit__(type, value, traceback)

    def read_from_rom(self, rom):
        self._tm.read_from_rom(rom)

    def write_to_rom(self, rom):
        self._tm.write_to_rom(rom)

    def write_to_project(self, resourceOpener):
        self._tm.write_to_project(resourceOpener)

    def read_from_project(self, resourceOpener):
        self._tm.read_from_project(resourceOpener)
