import logging

from coilsnake.model.eb.map_events import MapEventPointerTableEntry, MapEventSubTableEntry
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr_in_yml_file, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


log = logging.getLogger(__name__)

POINTER_TABLE_POINTER_OFFSET = 0x70d
POINTER_TABLE_DEFAULT_OFFSET = 0xD01598
POINTER_TABLE_BANK_OFFSET = 0x704


class MapEventModule(EbModule):
    NAME = "Map Event Tile Changes"
    FREE_RANGES = [(0x101598, 0x10187f)]

    def __init__(self):
        super(MapEventModule, self).__init__()
        self.pointer_table_entry_class = type("MapEventPointerTableEntrySubclass", (MapEventPointerTableEntry,), {})
        self.pointer_table = eb_table_from_offset(
            offset=POINTER_TABLE_DEFAULT_OFFSET,
            single_column=self.pointer_table_entry_class)

    def read_from_rom(self, rom):
        bank = from_snes_address(rom[POINTER_TABLE_BANK_OFFSET] << 16) >> 16
        log.debug("Reading data from {:#x} bank".format(bank))
        self.pointer_table_entry_class.bank = bank

        pointer_table_offset = from_snes_address(rom.read_multi(POINTER_TABLE_POINTER_OFFSET, 3))
        log.debug("Reading pointer table from {:#x}".format(pointer_table_offset))
        self.pointer_table.from_block(rom, pointer_table_offset)

    def write_to_rom(self, rom):
        pointer_table_offset = rom.allocate(size=self.pointer_table.size)

        bank = rom.get_largest_unallocated_range()[0] >> 16
        log.debug("Writing data to {:#x} bank".format(bank))
        self.pointer_table_entry_class.bank = bank
        rom[POINTER_TABLE_BANK_OFFSET] = to_snes_address(bank << 16) >> 16

        log.debug("Writing pointer table to {:#x}".format(pointer_table_offset))
        rom.write_multi(POINTER_TABLE_POINTER_OFFSET, to_snes_address(pointer_table_offset), 3)
        self.pointer_table.to_block(rom, pointer_table_offset)

    def write_to_project(self, resource_open):
        with resource_open("map_changes", "yml", True) as f:
            self.pointer_table.to_yml_file(f, default_flow_style=None)

    def read_from_project(self, resource_open):
        with resource_open("map_changes", "yml", True) as f:
            self.pointer_table.from_yml_file(f)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version < 5:
            with resource_open_r("map_changes", "yml", True) as f:
                data = yml_load(f)

            for i in data:
                if data[i] is None:
                    data[i] = []
                else:
                    for entry in data[i]:
                        entry["Tile Changes"] = entry["Changes"]
                        del entry["Changes"]

                        for j, change in enumerate(entry["Tile Changes"]):
                            entry["Tile Changes"][j] = MapEventSubTableEntry.to_yml_rep(change)

            with resource_open_w("map_changes", "yml", True) as f:
                yml_dump(data, f)

            convert_values_to_hex_repr_in_yml_file("map_changes", resource_open_r, resource_open_w, ["Event Flag"],
                                                   default_flow_style=None)

            self.upgrade_project(5, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)


