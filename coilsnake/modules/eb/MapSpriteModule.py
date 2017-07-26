from functools import partial

from coilsnake.model.eb.map_sprites import SpritePlacementPointerTableEntry
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.helper import not_in_bank
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


class MapSpriteModule(EbModule):
    NAME = "NPC Placements"

    POINTER_TABLE_DEFAULT_OFFSET = 0xCF61E7
    POINTER_TABLE_POINTER_OFFSET = 0x2261

    def __init__(self):
        super(MapSpriteModule, self).__init__()
        self.table = eb_table_from_offset(
            offset=self.POINTER_TABLE_DEFAULT_OFFSET,
            single_column=SpritePlacementPointerTableEntry,
            matrix_dimensions=(32, 40))

    def read_from_rom(self, rom):
        pointer_table_offset = from_snes_address(rom.read_multi(self.POINTER_TABLE_POINTER_OFFSET, 3))
        self.table.from_block(rom, pointer_table_offset)

    def write_to_rom(self, rom):
        rom.deallocate((0xf61e7, 0xf8984))

        pointer_table_offset = rom.allocate(size=self.table.size,
                                            can_write_to=partial(not_in_bank, 0x0f))
        self.table.to_block(rom, pointer_table_offset)
        rom.write_multi(self.POINTER_TABLE_POINTER_OFFSET, to_snes_address(pointer_table_offset), 3)

    def write_to_project(self, resource_open):
        with resource_open("map_sprites", "yml", True) as f:
            self.table.to_yml_file(f, default_flow_style=None)

    def read_from_project(self, resource_open):
        with resource_open("map_sprites", "yml", True) as f:
            self.table.from_yml_file(f)