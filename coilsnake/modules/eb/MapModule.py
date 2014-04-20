import yaml

from coilsnake.model.common.table import EnumeratedLittleEndianIntegerTableEntry, LittleEndianIntegerTableEntry
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.project import replace_field_in_yml
from coilsnake.util.eb.pointer import from_snes_address

MAP_POINTERS_OFFSET = 0xa1db
LOCAL_TILESETS_OFFSET = 0x175000
MAP_HEIGHT = 320
MAP_WIDTH = 256

SECTOR_TILESETS_PALETTES_TABLE_OFFSET = 0xD7A800
SECTOR_MUSIC_TABLE_OFFSET = 0xDCD637
SECTOR_MISC_TABLE_OFFSET = 0xD7B200
SECTOR_TOWN_MAP_TABLE_OFFSET = 0xEFA70F

INTEGER_ENTRY = LittleEndianIntegerTableEntry.create("Integer", 1)
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


class MapModule(EbModule):
    NAME = "Map"

    def __init__(self):
        super(MapModule, self).__init__()
        self.tiles = []
        self.sector_tilesets_palettes_table = eb_table_from_offset(offset=SECTOR_TILESETS_PALETTES_TABLE_OFFSET)
        self.sector_music_table = eb_table_from_offset(offset=SECTOR_MUSIC_TABLE_OFFSET)
        self.sector_misc_table = eb_table_from_offset(offset=SECTOR_MISC_TABLE_OFFSET)
        self.sector_town_map_table = eb_table_from_offset(offset=SECTOR_TOWN_MAP_TABLE_OFFSET)

    def read_from_rom(self, rom):
        # Read map data
        map_ptrs_addr = from_snes_address(rom.read_multi(MAP_POINTERS_OFFSET, 3))
        map_addrs = [from_snes_address(rom.read_multi(map_ptrs_addr + x * 4, 4)) for x in range(8)]

        def read_row_data(row_number):
            offset = map_addrs[row_number % 8] + ((row_number >> 3) << 8)
            return rom[offset:offset + MAP_WIDTH].to_list()

        self.tiles = map(read_row_data, range(MAP_HEIGHT))
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
        with resource_open("map_tiles", "map") as f:
            for row in self.tiles:
                f.write(hex(row[0])[2:].zfill(3))
                for tile in row[1:]:
                    f.write(" ")
                    f.write(hex(tile)[2:].zfill(3))
                f.write("\n")

        # Write sector data
        out = dict()
        for i in range(self.sector_tilesets_palettes_table.num_rows):
            out[i] = {
                "Tileset": INTEGER_ENTRY.to_yml_rep(self.sector_tilesets_palettes_table[i][0] >> 3),
                "Palette": INTEGER_ENTRY.to_yml_rep(self.sector_tilesets_palettes_table[i][0] & 7),
                "Music": INTEGER_ENTRY.to_yml_rep(self.sector_music_table[i][0]),
                "Teleport": TELEPORT_ENTRY.to_yml_rep(self.sector_misc_table[i][0] >> 7),
                "Town Map": TOWNMAP_ENTRY.to_yml_rep((self.sector_misc_table[i][0] >> 3) & 7),
                "Setting": SETTING_ENTRY.to_yml_rep(self.sector_misc_table[i][0] & 7),
                "Item": INTEGER_ENTRY.to_yml_rep(self.sector_misc_table[i][1]),
                "Town Map Image": TOWNMAP_IMAGE_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] & 0xf),
                "Town Map Arrow": TOWNMAP_ARROW_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] >> 4),
                "Town Map X": INTEGER_ENTRY.to_yml_rep(self.sector_town_map_table[i][1]),
                "Town Map Y": INTEGER_ENTRY.to_yml_rep(self.sector_town_map_table[i][2])}
        with resource_open("map_sectors", "yml") as f:
            yaml.dump(out, f, Dumper=yaml.CSafeDumper, default_flow_style=False)

    def read_from_project(self, resource_open):
        # Read map data
        with resource_open("map_tiles", "map") as f:
            self.tiles = map(lambda y:
                              map(lambda x: int(x, 16), y.split(" ")),
                              f.readlines())

        # Read sector data
        with resource_open("map_sectors", "yml") as f:
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for i in input:
                entry = input[i]

                tileset = INTEGER_ENTRY.from_yml_rep(entry["Tileset"])
                palette = INTEGER_ENTRY.from_yml_rep(entry["Palette"])
                self.sector_tilesets_palettes_table[i] = [(tileset << 3) | palette]

                music = INTEGER_ENTRY.from_yml_rep(entry["Music"])
                self.sector_music_table[i] = [music]

                teleport = TELEPORT_ENTRY.from_yml_rep(entry["Teleport"])
                townmap = TOWNMAP_ENTRY.from_yml_rep(entry["Town Map"])
                setting = SETTING_ENTRY.from_yml_rep(entry["Setting"])
                item = INTEGER_ENTRY.from_yml_rep(entry["Item"])
                self.sector_misc_table[i] = [(teleport << 7) | (townmap << 3) | setting, item]

                townmap_arrow = TOWNMAP_ARROW_ENTRY.from_yml_rep(entry["Town Map Arrow"])
                townmap_image = TOWNMAP_IMAGE_ENTRY.from_yml_rep(entry["Town Map Image"])
                townmap_x = INTEGER_ENTRY.from_yml_rep(entry["Town Map X"])
                townmap_y = INTEGER_ENTRY.from_yml_rep(entry["Town Map Y"])
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

            with resource_open_r("map_sectors", 'yml') as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
                for i in data:
                    data[i]["Town Map Image"] = TOWNMAP_IMAGE_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] & 0xf)
                    data[i]["Town Map Arrow"] = TOWNMAP_ARROW_ENTRY.to_yml_rep(self.sector_town_map_table[i][0] >> 4)
                    data[i]["Town Map X"] = INTEGER_ENTRY.to_yml_rep(self.sector_town_map_table[i][1])
                    data[i]["Town Map Y"] = INTEGER_ENTRY.to_yml_rep(self.sector_town_map_table[i][2])
            with resource_open_w("map_sectors", 'yml') as f:
                yaml.dump(data, f, Dumper=yaml.CSafeDumper, default_flow_style=False)

            self.upgrade_project(3, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
