from functools import partial

from coilsnake.model.eb.map_music import MapMusicTableEntry
from coilsnake.model.eb.table import eb_table_from_offset, EbBankPointerToVariableSizeEntryTableEntry, \
    EbPointerTableEntry
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.helper import not_in_bank
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


MAP_MUSIC_ASM_POINTER_OFFSET = 0x6939
MAP_MUSIC_DEFAULT_OFFSET = 0xCF58EF


class MapMusicModule(EbModule):
    NAME = "Map Music"

    def __init__(self):
        super(MapMusicModule, self).__init__()
        self.pointer_table = eb_table_from_offset(
            offset=MAP_MUSIC_DEFAULT_OFFSET,
            single_column=EbBankPointerToVariableSizeEntryTableEntry.create(
                EbPointerTableEntry.create(2),
                MapMusicTableEntry,
                0x0f))

    def read_from_rom(self, rom):
        self.pointer_table.from_block(rom, from_snes_address(rom.read_multi(MAP_MUSIC_ASM_POINTER_OFFSET, 3)))

    def write_to_rom(self, rom):
        rom.deallocate((0xf58ef, 0xf61e5))

        pointer_table_offset = rom.allocate(size=self.pointer_table.size, can_write_to=partial(not_in_bank, 0x0f))
        self.pointer_table.to_block(rom, pointer_table_offset)
        rom.write_multi(MAP_MUSIC_ASM_POINTER_OFFSET, to_snes_address(pointer_table_offset), 3)

    def write_to_project(self, resource_open):
        with resource_open("map_music", "yml", True) as f:
            self.pointer_table.to_yml_file(f, default_flow_style=False)

    def read_from_project(self, resource_open):
        with resource_open("map_music", "yml", True) as f:
            self.pointer_table.from_yml_file(f)
