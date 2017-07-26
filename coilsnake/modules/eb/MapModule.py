import yaml

from coilsnake.model.common.table import EnumeratedLittleEndianIntegerTableEntry, LittleEndianIntegerTableEntry, \
    RowTableEntry
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import replace_field_in_yml, yml_load
from coilsnake.util.eb.pointer import from_snes_address

MAP_POINTERS_OFFSET = 0xa1db
LOCAL_TILESETS_OFFSET = 0x175000
MAP_HEIGHT = 320
MAP_WIDTH = 256

SECTOR_TILESETS_PALETTES_TABLE_OFFSET = 0xD7A800
SECTOR_MUSIC_TABLE_OFFSET = 0xDCD637
SECTOR_MISC_TABLE_OFFSET = 0xD7B200
SECTOR_TOWN_MAP_TABLE_OFFSET = 0xEFA70F

TELEPORT_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Teleport", 1, ["Enabled", "Disabled"]
)
TOWNMAP_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map", 1,
    ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers", "None 2"]
)
SETTING_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Setting", 1,
    ["None", "Indoors", "Exit Mouse usable", "Lost Underworld sprites", "Magicant sprites", "Robot sprites",
     "Butterflies", "Indoors and Butterflies"]
)
TOWNMAP_IMAGE_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map Image", 1,
    ["None", "Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"]
)
TOWNMAP_ARROW_ENTRY = EnumeratedLittleEndianIntegerTableEntry.create(
    "Town Map Arrow", 1,
    ["None", "Up", "Down", "Right", "Left"]
)
TOWNMAP_X = LittleEndianIntegerTableEntry.create("Town Map X", 1)
TOWNMAP_Y = LittleEndianIntegerTableEntry.create("Town Map Y", 1)

SectorYmlTable = RowTableEntry.from_schema(
    name="Aggregate Sector Properties Table Entry",
    schema=[LittleEndianIntegerTableEntry.create("Tileset", 1),
            LittleEndianIntegerTableEntry.create("Palette", 1),
            LittleEndianIntegerTableEntry.create("Music", 1),
            TELEPORT_ENTRY,
            TOWNMAP_ENTRY,
            SETTING_ENTRY,
            LittleEndianIntegerTableEntry.create("Item", 1),
            TOWNMAP_ARROW_ENTRY,
            TOWNMAP_IMAGE_ENTRY,
            TOWNMAP_X,
            TOWNMAP_Y]
)


class MapModule(EbModule):
    NAME = "Map"

    def __init__(self):
        super(MapModule, self).__init__()
        self.tiles = []
        self.sector_tilesets_palettes_table = eb_table_from_offset(offset=SECTOR_TILESETS_PALETTES_TABLE_OFFSET,
                                                                   name="map_sectors")
        self.sector_music_table = eb_table_from_offset(offset=SECTOR_MUSIC_TABLE_OFFSET,
                                                       name="map_sectors")
        self.sector_misc_table = eb_table_from_offset(offset=SECTOR_MISC_TABLE_OFFSET,
                                                      name="map_sectors")
        self.sector_town_map_table = eb_table_from_offset(offset=SECTOR_TOWN_MAP_TABLE_OFFSET,
                                                          name="map_sectors")
        self.sector_yml_table = eb_table_from_offset(offset=SECTOR_TILESETS_PALETTES_TABLE_OFFSET,
                                                     single_column=SectorYmlTable,
                                                     num_rows=self.sector_tilesets_palettes_table.num_rows,
                                                     name="map_sectors")

    def read_from_rom(self, rom):
        # Read map data
        map_ptrs_addr = from_snes_address(rom.read_multi(MAP_POINTERS_OFFSET, 3))
        map_addrs = [from_snes_address(rom.read_multi(map_ptrs_addr + x * 4, 4)) for x in range(8)]

        def read_row_data(row_number):
            offset = map_addrs[row_number % 8] + ((row_number >> 3) << 8)
            return rom[offset:offset + MAP_WIDTH].to_list()

        self.tiles = list(map(read_row_data, range(MAP_HEIGHT)))
        k = LOCAL_TILESETS_OFFSET
        for i in range(MAP_HEIGHT >> 3):
            for j in range(MAP_WIDTH):
                self.tiles[i << 3][j] |= (rom[k] & 3) << 8
                self.tiles[(i << 3) | 1][j] |= ((rom[k] >> 2) & 3) << 8
                self.tiles[(i << 3) | 2][j] |= ((rom[k] >> 4) & 3) << 8
                self.tiles[(i << 3) | 3][j] |= ((rom[k] >> 6) & 3) << 8
                self.tiles[(i << 3) | 4][j] |= (rom[k + 0x3000] & 3) << 8
                self.tiles[(i << 3) | 5][j] |= ((rom[k + 0x3000] >> 2) & 3) << 8
                self.tiles[(i << 3) | 6][j] |= ((rom[k + 0x3000] >> 4) & 3) << 8
                self.tiles[(i << 3) | 7][j] |= ((rom[k + 0x3000] >> 6) & 3) << 8
                k += 1

        # Read sector data
        self.sector_tilesets_palettes_table.from_block(rom, from_snes_address(SECTOR_TILESETS_PALETTES_TABLE_OFFSET))
        self.sector_music_table.from_block(rom, from_snes_address(SECTOR_MUSIC_TABLE_OFFSET))
        self.sector_misc_table.from_block(rom, from_snes_address(SECTOR_MISC_TABLE_OFFSET))
        self.sector_town_map_table.from_block(rom, from_snes_address(SECTOR_TOWN_MAP_TABLE_OFFSET))

    def write_to_rom(self, rom):
        # Write map data
        map_ptrs_addr = from_snes_address(rom.read_multi(MAP_POINTERS_OFFSET, 3))
        map_addrs = [from_snes_address(rom.read_multi(map_ptrs_addr + x * 4, 4)) for x in range(8)]

        for i in range(MAP_HEIGHT):
            offset = map_addrs[i % 8] + ((i >> 3) << 8)
            rom[offset:offset + MAP_WIDTH] = [x & 0xff for x in self.tiles[i]]
        k = LOCAL_TILESETS_OFFSET
        for i in range(MAP_HEIGHT >> 3):
            for j in range(MAP_WIDTH):
                c = ((self.tiles[i << 3][j] >> 8)
                     | ((self.tiles[(i << 3) | 1][j] >> 8) << 2)
                     | ((self.tiles[(i << 3) | 2][j] >> 8) << 4)
                     | ((self.tiles[(i << 3) | 3][j] >> 8) << 6))
                rom[k] = c
                c = ((self.tiles[(i << 3) | 4][j] >> 8)
                     | ((self.tiles[(i << 3) | 5][j] >> 8) << 2)
                     | ((self.tiles[(i << 3) | 6][j] >> 8) << 4)
                     | ((self.tiles[(i << 3) | 7][j] >> 8) << 6))
                rom[k + 0x3000] = c
                k += 1

        # Write sector data
        self.sector_tilesets_palettes_table.to_block(rom, from_snes_address(SECTOR_TILESETS_PALETTES_TABLE_OFFSET))
        self.sector_music_table.to_block(rom, from_snes_address(SECTOR_MUSIC_TABLE_OFFSET))
        self.sector_misc_table.to_block(rom, from_snes_address(SECTOR_MISC_TABLE_OFFSET))
        self.sector_town_map_table.to_block(rom, from_snes_address(SECTOR_TOWN_MAP_TABLE_OFFSET))

    def write_to_project(self, resource_open):
        # Write map tiles
        with resource_open("map_tiles", "map", True) as f:
            for row in self.tiles:
                f.write(hex(row[0])[2:].zfill(3))
                for tile in row[1:]:
                    f.write(" ")
                    f.write(hex(tile)[2:].zfill(3))
                f.write("\n")

        for i in range(self.sector_yml_table.num_rows):
            tileset = self.sector_tilesets_palettes_table[i][0] >> 3
            palette = self.sector_tilesets_palettes_table[i][0] & 7
            music = self.sector_music_table[i][0]
            teleport = self.sector_misc_table[i][0] >> 7
            townmap = (self.sector_misc_table[i][0] >> 3) & 7
            setting = self.sector_misc_table[i][0] & 7
            item = self.sector_misc_table[i][1]
            townmap_arrow = self.sector_town_map_table[i][0] >> 4
            townmap_image = self.sector_town_map_table[i][0] & 0xf
            townmap_x = self.sector_town_map_table[i][1]
            townmap_y = self.sector_town_map_table[i][2]

            self.sector_yml_table[i] = [
                tileset,
                palette,
                music,
                teleport,
                townmap,
                setting,
                item,
                townmap_arrow,
                townmap_image,
                townmap_x,
                townmap_y
            ]
        with resource_open("map_sectors", "yml", True) as f:
            self.sector_yml_table.to_yml_file(f)

    def read_from_project(self, resource_open):
        # Read map data
        with resource_open("map_tiles", "map", True) as f:
            self.tiles = [[int(x, 16) for x in y.split(" ")] for y in f.readlines()]

        # Read sector data
        with resource_open("map_sectors", "yml", True) as f:
            self.sector_yml_table.from_yml_file(f)

        for i in range(self.sector_yml_table.num_rows):
            tileset = self.sector_yml_table[i][0]
            palette = self.sector_yml_table[i][1]
            music = self.sector_yml_table[i][2]
            teleport = self.sector_yml_table[i][3]
            townmap = self.sector_yml_table[i][4]
            setting = self.sector_yml_table[i][5]
            item = self.sector_yml_table[i][6]
            townmap_arrow = self.sector_yml_table[i][7]
            townmap_image = self.sector_yml_table[i][8]
            townmap_x = self.sector_yml_table[i][9]
            townmap_y = self.sector_yml_table[i][10]

            self.sector_tilesets_palettes_table[i] = [(tileset << 3) | palette]

            self.sector_music_table[i] = [music]

            self.sector_misc_table[i] = [(teleport << 7) | (townmap << 3) | setting, item]

            self.sector_town_map_table[i] = [((townmap_arrow << 4) | (townmap_image & 0xf)),
                                             townmap_x,
                                             townmap_y]

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 2:
            replace_field_in_yml(resource_name="map_sectors",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Town Map",
                                 value_map={"scummers": "summers"})

            self.read_from_rom(rom)

            with resource_open_r("map_sectors", 'yml', True) as f:
                data = yml_load(f)
                for i in data:
                    data[i]["Town Map Image"] = TOWNMAP_IMAGE_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] & 0xf)
                    data[i]["Town Map Arrow"] = TOWNMAP_ARROW_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] >> 4)
                    data[i]["Town Map X"] = TOWNMAP_X.to_yml_rep(self.sector_town_map_table[i][1])
                    data[i]["Town Map Y"] = TOWNMAP_Y.to_yml_rep(self.sector_town_map_table[i][2])
            with resource_open_w("map_sectors", 'yml', True) as f:
                yaml.dump(data, f, Dumper=yaml.CSafeDumper, default_flow_style=False)

            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
