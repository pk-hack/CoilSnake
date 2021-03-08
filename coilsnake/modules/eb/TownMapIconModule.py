from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.model.eb.town_maps import TownMapIconPlacementPointerTableEntry, TownMapEnum
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr_in_yml_file, yml_load, yml_dump
from coilsnake.util.eb.pointer import read_asm_pointer, write_asm_pointer, from_snes_address, to_snes_address


class TownMapIconModule(EbModule):
    NAME = "Town Map Icon Positions"
    FREE_RANGES = [(0x21f491, 0x21f580)]  # Pointer Table and Data

    POINTER_TABLE_DEFAULT_OFFSET = 0xE1F491
    POINTER_TABLE_ASM_POINTER_OFFSET = 0x4D464
    TILE_COUNT_ADDRESS = 0x4d626

    def __init__(self):
        super(TownMapIconModule, self).__init__()
        self.table = eb_table_from_offset(
            offset=self.POINTER_TABLE_DEFAULT_OFFSET,
            single_column=TownMapIconPlacementPointerTableEntry)

    def read_from_rom(self, rom):
        pointer_table_offset = from_snes_address(read_asm_pointer(rom, self.POINTER_TABLE_ASM_POINTER_OFFSET))
        self.table.from_block(rom, pointer_table_offset)

    def write_to_rom(self, rom):
        pointer_table_offset = rom.allocate(size=self.table.size)
        self.table.to_block(rom, pointer_table_offset)
        write_asm_pointer(rom, self.POINTER_TABLE_ASM_POINTER_OFFSET, to_snes_address(pointer_table_offset))
        rom[self.TILE_COUNT_ADDRESS:self.TILE_COUNT_ADDRESS+2] = [0x00, 0x60] # Patch to support additional tiles 

    def read_from_project(self, resource_open):
        with resource_open("TownMaps/icon_positions", "yml", True) as f:
            self.table.from_yml_file(f)

    def write_to_project(self, resource_open):
        with resource_open("TownMaps/icon_positions", "yml", True) as f:
            self.table.to_yml_file(f)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 4:
            with resource_open_r("TownMaps/icon_positions", "yml", True) as f:
                data = yml_load(f)

                for i in range(6):
                    old_key = TownMapEnum.tostring(i).lower()
                    data[i] = data[old_key]
                    del data[old_key]
            with resource_open_w("TownMaps/icon_positions", "yml", True) as f:
                yml_dump(data, f, default_flow_style=False)

            convert_values_to_hex_repr_in_yml_file("TownMaps/icon_positions", resource_open_r, resource_open_w,
                                                   ["Event Flag"])

            self.upgrade_project(5, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        elif old_version <= 2:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
            self.upgrade_project(new_version, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
