import yaml

import Eb0Module
from modules.Table import Table, genericEntryGenerator
from modules.TablesModule import TablesModule


def eb0EntryGenerator(spec, table_map):
    if "type" not in spec:
        return genericEntryGenerator(spec, table_map)
    else:
        return genericEntryGenerator(spec, table_map)


class Eb0Table(Table):
    tableEntryGenerator = staticmethod(eb0EntryGenerator)
    eb_table_map = None

    def __init__(self, addr):
        if Eb0Table.eb_table_map is None:
            with open("resources/structures/eb0.yml") as f:
                i = 1
                for doc in yaml.load_all(f, Loader=yaml.CSafeLoader):
                    if i == 1:
                        i += 1
                    elif i == 2:
                        Eb0Table.eb_table_map = doc
                        break
        Table.__init__(self, addr, Eb0Table.eb_table_map)
        self._addr = Eb0Module.toRegAddr(self._addr)


class Eb0TablesModule(Eb0Module.Eb0Module):
    NAME = "EarthBound Zero Tables"
    _tableIDs = []

    def __init__(self):
        Eb0Module.Eb0Module.__init__(self)
        self._tm = TablesModule(Eb0Table, self._tableIDs)

    def free(self):
        self._tm.free()

    def read_from_rom(self, rom):
        self._tm.read_from_rom(rom)

    def write_to_rom(self, rom):
        self._tm.write_to_rom(rom)

    def write_to_project(self, resourceOpener):
        self._tm.write_to_project(resourceOpener)

    def read_from_project(self, resourceOpener):
        self._tm.read_from_project(resourceOpener)
