from array import array
from functools import partial
import logging
from zlib import crc32

from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.map_tilesets import EbMapPalette, EbTileset
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr, yml_load, yml_dump
from coilsnake.util.eb.helper import is_in_bank, not_in_bank
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


log = logging.getLogger(__name__)

GRAPHICS_POINTER_TABLE_OFFSET = 0xEF105B
ARRANGEMENTS_POINTER_TABLE_OFFSET = 0xEF10AB
COLLISIONS_POINTER_TABLE_OFFSET = 0xEF117B
MAP_TILESET_TABLE_OFFSET = 0xEF101B
PALETTE_POINTER_TABLE_OFFSET = 0xEF10FB


class TilesetModule(EbModule):
    NAME = "Tilesets"
    FREE_RANGES = [(0x17c600, 0x17fbe7),
                   (0x190000, 0x19fc17),
                   (0x1b0000, 0x1bf2ea),
                   (0x1c0000, 0x1cd636),
                   (0x1d0000, 0x1dfecd),
                   (0x1e0000, 0x1ef0e6),
                   (0x1f0000, 0x1fc242)]

    def __init__(self):
        super(TilesetModule, self).__init__()
        self.graphics_pointer_table = eb_table_from_offset(GRAPHICS_POINTER_TABLE_OFFSET)
        self.arrangements_pointer_table = eb_table_from_offset(ARRANGEMENTS_POINTER_TABLE_OFFSET)
        self.collisions_pointer_table = eb_table_from_offset(COLLISIONS_POINTER_TABLE_OFFSET)
        self.map_tileset_table = eb_table_from_offset(MAP_TILESET_TABLE_OFFSET)
        self.palette_pointer_table = eb_table_from_offset(PALETTE_POINTER_TABLE_OFFSET)
        self.tilesets = [EbTileset() for i in range(20)]

    def read_from_rom(self, rom):
        log.debug("Reading pointer tables")
        self.graphics_pointer_table.from_block(rom, from_snes_address(GRAPHICS_POINTER_TABLE_OFFSET))
        self.arrangements_pointer_table.from_block(rom, from_snes_address(ARRANGEMENTS_POINTER_TABLE_OFFSET))
        self.collisions_pointer_table.from_block(rom, from_snes_address(COLLISIONS_POINTER_TABLE_OFFSET))
        self.map_tileset_table.from_block(rom, from_snes_address(MAP_TILESET_TABLE_OFFSET))
        self.palette_pointer_table.from_block(rom, from_snes_address(PALETTE_POINTER_TABLE_OFFSET))

        for i, tileset in enumerate(self.tilesets):
            log.debug("Reading tileset #{}".format(i))
            tileset.minitiles_from_block(rom, from_snes_address(self.graphics_pointer_table[i][0]))
            tileset.arrangements_from_block(rom, from_snes_address(self.arrangements_pointer_table[i][0]))
            tileset.collisions_from_block(rom, from_snes_address(self.collisions_pointer_table[i][0]))

        # Read palettes
        log.debug("Reading palettes")
        for i in range(self.map_tileset_table.num_rows):
            draw_tileset = self.map_tileset_table[i][0]
            # Estimate the number of palettes for this map tileset, assuming that the palettes are stored contiguously
            if i == 31:
                k = 8
            else:
                k = self.palette_pointer_table[i + 1][0] - self.palette_pointer_table[i][0]
                k //= 0xc0

            # Add the palettes to the tileset
            palette_offset = from_snes_address(self.palette_pointer_table[i][0])
            for j in range(k):
                palette = EbMapPalette()
                palette.from_block(block=rom, offset=palette_offset)
                self.tilesets[draw_tileset].add_palette(i, j, palette)
                palette_offset += 0xc0

    def write_to_rom(self, rom):
        # Collisions need to be in the 0xD8 bank
        rom.deallocate((0x180000, 0x18f05d))
        collision_offsets = dict()
        collision_array = array('B', [0] * 16)
        log.debug("Writing collisions")
        for tileset_id, tileset in enumerate(self.tilesets):
            with Block(len(tileset.collisions) * 2) as collision_table:
                j = 0
                for collision in tileset.collisions:
                    for i, collision_item in enumerate(collision):
                        collision_array[i] = collision_item
                    collision_hash = crc32(collision_array)

                    try:
                        collision_offset = collision_offsets[collision_hash]
                    except KeyError:
                        collision_offset = rom.allocate(data=collision,
                                                        can_write_to=partial(is_in_bank, 0x18)) & 0xffff
                        collision_offsets[collision_hash] = collision_offset

                    collision_table.write_multi(key=j, item=collision_offset, size=2)
                    j += 2
                collision_table_offset = rom.allocate(data=collision_table, can_write_to=partial(not_in_bank, 0x18))
                self.collisions_pointer_table[tileset_id] = [to_snes_address(collision_table_offset)]

        self.collisions_pointer_table.to_block(block=rom, offset=from_snes_address(COLLISIONS_POINTER_TABLE_OFFSET))

        # Palettes need to be in the 0xDA bank
        rom.deallocate((0x1a0000, 0x1afaa6))  # Not sure if this can go farther

        map_tileset_palettes = {}
        number_of_palettes = 0

        # Write maps/drawing tilesets associations and map tset pals
        log.debug("Writing palettes")
        for map_tileset_id in range(32):  # For each map tileset
            # Find the drawing tileset number for this map tileset
            for i, tileset in enumerate(self.tilesets):
                if tileset.has_map_tileset(map_tileset_id):
                    tileset_id = i
                    break
            else:
                # TODO Error, this drawing tileset isn't associated
                tileset_id = 0
            self.map_tileset_table[map_tileset_id] = [tileset_id]

            palettes = tileset.get_palettes_by_map_tileset(map_tileset_id)
            palettes.sort()

            map_tileset_palettes[map_tileset_id] = palettes
            number_of_palettes += len(palettes)

        # Write the event palettes.
        # These are written first because the standard palettes each potentially contain a pointer
        # to the location of an event palette
        for map_tileset_id in range(32):
            for map_palette_id, palette in map_tileset_palettes[map_tileset_id]:
                palette.flag_palette_to_block(rom)

        # Write the standard palettes
        # Allocate space for the standard palettes contiguously
        palette_offset = rom.allocate(size=0xc0 * number_of_palettes, can_write_to=partial(is_in_bank, 0x1a))
        for map_tileset_id in range(32):
            self.palette_pointer_table[map_tileset_id] = [to_snes_address(palette_offset)]

            for map_palette_id, palette in map_tileset_palettes[map_tileset_id]:
                palette.to_block(block=rom, offset=palette_offset)
                palette_offset += palette.block_size()

        self.map_tileset_table.to_block(block=rom, offset=from_snes_address(MAP_TILESET_TABLE_OFFSET))
        self.palette_pointer_table.to_block(block=rom, offset=from_snes_address(PALETTE_POINTER_TABLE_OFFSET))

        for tileset_id, tileset in enumerate(self.tilesets):
            log.debug("Writing tileset #{}".format(tileset_id))
            self.graphics_pointer_table[tileset_id] = [to_snes_address(tileset.minitiles_to_block(rom))]
            self.arrangements_pointer_table[tileset_id] = [to_snes_address(tileset.arrangements_to_block(rom))]

        self.graphics_pointer_table.to_block(block=rom, offset=from_snes_address(GRAPHICS_POINTER_TABLE_OFFSET))
        self.arrangements_pointer_table.to_block(block=rom, offset=from_snes_address(ARRANGEMENTS_POINTER_TABLE_OFFSET))

    def write_map_palette_settings(self, palette_settings, resource_open):
        with resource_open("map_palette_settings", "yml") as f:
            yml_str_rep = yml_dump(palette_settings, default_flow_style=False)
            yml_str_rep = convert_values_to_hex_repr(yml_str_rep, "Event Flag")
            f.write(yml_str_rep)

    def write_to_project(self, resource_open):
        # Dump an additional YML with color0 data
        palette_settings = dict()
        log.debug("Writing palette settings")
        for i in range(0, 32):  # For each map tileset
            entry = dict()
            tileset = None
            for ts in self.tilesets:
                if ts.has_map_tileset(i):
                    tileset = ts
                    break

            palettes = tileset.get_palettes_by_map_tileset(i)
            palettes.sort()
            for (palette_id, palette) in palettes:
                entry[palette_id] = palette.settings_yml_rep()
            palette_settings[i] = entry

        self.write_map_palette_settings(palette_settings, resource_open)

        # Dump the tilesets
        for i, tileset in enumerate(self.tilesets):
            log.debug("Writing tileset #{}".format(i))
            with resource_open("Tilesets/" + str(i).zfill(2), "fts") as f:
                tileset.to_file(f)

    def read_from_project(self, resource_open):
        for i, tileset in enumerate(self.tilesets):
            log.debug("Reading tileset #{}".format(i))
            with resource_open("Tilesets/" + str(i).zfill(2), "fts") as f:
                tileset.from_file(f)

        log.debug("Reading palette settings")
        with resource_open("map_palette_settings", "yml") as f:
            yml_rep = yml_load(f)
            for map_tileset in yml_rep:
                # Get the draw (normal) tileset
                tileset = None
                for ts in self.tilesets:
                    if ts.has_map_tileset(map_tileset):
                        tileset = ts
                        break

                # For each map palette
                palettes = tileset.get_palettes_by_map_tileset(map_tileset)
                for palette_id, palette in palettes:
                    entry = yml_rep[map_tileset][palette_id]
                    palette.settings_from_yml_rep(entry)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version <= 6:
            with resource_open_r("map_palette_settings", "yml") as f:
                yml_rep = yml_load(f)
                for map_tileset in yml_rep.itervalues():
                    for map_palette in map_tileset.itervalues():
                        if "Event Palette" in map_palette:
                            map_palette["Event Palette"] = {
                                "Colors": map_palette["Event Palette"],
                                "Event Flag": 0,
                                "Flash Effect": 0,
                                "Sprite Palette": map_palette["Sprite Palette"]
                            }
            self.write_map_palette_settings(yml_rep, resource_open_w)

            self.upgrade_project(
                7, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(
                old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
