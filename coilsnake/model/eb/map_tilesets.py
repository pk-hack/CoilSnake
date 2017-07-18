from functools import partial

from coilsnake.model.common.table import LittleEndianIntegerTableEntry
from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import EbEventFlagTableEntry
from coilsnake.util.eb.helper import is_in_bank


CHARACTERS = "0123456789abcdefghijklmnopqrstuv"

SpritePaletteIdTableEntry = LittleEndianIntegerTableEntry.create(name="Sprite Palette", size=1)
FlashEffectTableEntry = LittleEndianIntegerTableEntry.create(name="Flash Effect", size=1)


class EbMapPalette(EbPalette):
    def __init__(self):
        super(EbMapPalette, self).__init__(num_subpalettes=6, subpalette_length=16)
        self.flag = 0
        self.flag_palette = None
        self.flag_palette_pointer = None
        self.sprite_palette_id = 0
        self.flash_effect = 0

    def from_block(self, block, offset=0):
        self.flag = block.read_multi(offset, 2)
        if self.flag != 0:
            alternate_address = block.read_multi(offset + 0x20, 2) | 0x1a0000
            self.flag_palette = EbMapPalette()
            self.flag_palette.from_block(block, offset=alternate_address)
        self.sprite_palette_id = block[offset + 0x40]
        self.flash_effect = block[offset + 0x60]

        super(EbMapPalette, self).from_block(block, offset)
        for subpalette in self.subpalettes:
            subpalette[0].r = 0
            subpalette[0].g = 0
            subpalette[0].b = 0

    def to_block(self, block, offset=0):
        super(EbMapPalette, self).to_block(block, offset)

        block.write_multi(key=offset, item=self.flag, size=2)
        if self.flag_palette is not None:
            if self.flag_palette_pointer is None:
                self.flag_palette_to_block(block)
            block.write_multi(key=offset + 0x20, item=self.flag_palette_pointer, size=2)
        else:
            block[offset + 0x20] = 0
            block[offset + 0x21] = 0
        block[offset + 0x40] = self.sprite_palette_id
        block[offset + 0x60] = self.flash_effect

    def flag_palette_to_block(self, block):
        if self.flag_palette is not None:
            self.flag_palette_pointer = block.allocate(
                size=self.flag_palette.block_size(),
                can_write_to=partial(is_in_bank, 0x1a))
            self.flag_palette.to_block(block, self.flag_palette_pointer)

    def settings_yml_rep(self, include_colors=False):
        out = {EbEventFlagTableEntry.name: EbEventFlagTableEntry.to_yml_rep(self.flag),
               SpritePaletteIdTableEntry.name: SpritePaletteIdTableEntry.to_yml_rep(self.sprite_palette_id),
               FlashEffectTableEntry.name: FlashEffectTableEntry.to_yml_rep(self.flash_effect)}
        if include_colors:
            out["Colors"] = str(self)
        if self.flag != 0:
            out["Event Palette"] = self.flag_palette.settings_yml_rep(include_colors=True)
        return out

    def settings_from_yml_rep(self, yml_rep, include_colors=False):
        self.flag = EbEventFlagTableEntry.from_yml_rep(yml_rep[EbEventFlagTableEntry.name])
        self.sprite_palette_id = SpritePaletteIdTableEntry.from_yml_rep(yml_rep[SpritePaletteIdTableEntry.name])
        self.flash_effect = FlashEffectTableEntry.from_yml_rep(yml_rep[FlashEffectTableEntry.name])

        if include_colors:
            self.from_string(yml_rep["Colors"])

        if self.flag != 0:
            self.flag_palette = EbMapPalette()
            self.flag_palette.settings_from_yml_rep(yml_rep["Event Palette"], include_colors=True)


class EbTileset(object):
    def __init__(self):
        self.minitiles = EbGraphicTileset(num_tiles=896, tile_width=8, tile_height=8)
        self.arrangements = [None for i in range(1024)]
        self.collisions = [None for i in range(1024)]
        self.palettes = []

    def from_block(self, block, minitiles_offset, arrangements_offset, collisions_offset):
        self.minitiles_from_block(block, minitiles_offset)
        self.arrangements_from_block(block, arrangements_offset)
        self.collisions_from_block(block, collisions_offset)

    def minitiles_from_block(self, block, offset):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=offset)
            self.minitiles.from_block(block=compressed_block, bpp=4)

    def arrangements_from_block(self, block, offset):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=offset)
            num_arrangements = len(compressed_block) // 32

            j = 0
            for i in range(num_arrangements):
                arrangement = [[0 for x in range(4)] for y in range(4)]
                for y in range(4):
                    for x in range(4):
                        arrangement[y][x] = compressed_block.read_multi(key=j, size=2)
                        j += 2
                self.arrangements[i] = arrangement

    def collisions_from_block(self, block, offset):
        for i, arrangement in enumerate(self.arrangements):
            if arrangement is not None:
                collision_offset = 0x180000 | block.read_multi(key=offset + i * 2, size=2)
                self.collisions[i] = block[collision_offset:collision_offset + 16]

    def minitiles_to_block(self, block):
        with EbCompressibleBlock(self.minitiles.block_size(bpp=4)) as compressed_block:
            self.minitiles.to_block(block=compressed_block, offset=0, bpp=4)
            compressed_block.compress()
            return block.allocate(data=compressed_block)

    def arrangements_to_block(self, block):
        with EbCompressibleBlock(1024 * 16 * 2) as compressed_block:
            i = 0
            for arrangement in self.arrangements:
                for y in range(4):
                    for x in range(4):
                        compressed_block.write_multi(key=i, item=arrangement[y][x], size=2)
                        i += 2
            compressed_block.compress()
            return block.allocate(data=compressed_block)

    def add_palette(self, map_tileset, map_palette, palette):
        self.palettes.append((map_tileset, map_palette, palette))

    def has_map_tileset(self, map_tileset):
        for mt, mp, p in self.palettes:
            if mt == map_tileset:
                return True
        return False

    def get_palettes_by_map_tileset(self, map_tileset):
        return [(mp, p) for (mt, mp, p) in self.palettes if mt == map_tileset]

    def minitile_string_rep(self, n):
        if n >= 896:
            return "0000000000000000000000000000000000000000000000000000000000000000"
        else:
            s = str()
            tile = self.minitiles[n]
            for y in range(8):
                for x in range(8):
                    s += CHARACTERS[tile[y][x]]
            return s

    def minitile_from_string(self, n, string_rep):
        if n < 896:
            minitile = [[0] * self.minitiles.tile_width for x in range(self.minitiles.tile_height)]
            i = 0
            for y in range(8):
                for x in range(8):
                    minitile[y][x] = int(string_rep[i], 32)
                    i += 1
            self.minitiles.tiles[n] = minitile

    def arrangement_collision_string_rep(self, n):
        arrangement = self.arrangements[n]
        if arrangement is None:
            return "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        else:
            s = str()
            collision = self.collisions[n]
            for y in range(4):
                for x in range(4):
                    s += "{:04x}{:02x}".format(arrangement[y][x], collision[y*4 + x])
            return s

    def arrangement_collision_from_string(self, n, string_rep):
        i = 0
        arrangement = [[0 for x in range(4)] for y in range(4)]
        collision = [0] * 16
        for y in range(4):
            for x in range(4):
                arrangement[y][x] = int(string_rep[i:i + 4], 16)
                collision[y * 4 + x] = int(string_rep[i + 4: i + 6], 16)
                i += 6
        self.arrangements[n] = arrangement
        self.collisions[n] = collision

    def to_file(self, f):
        for i in range(512):
            print(self.minitile_string_rep(i), file=f)
            print(self.minitile_string_rep(i ^ 512), file=f)
            print(file=f)
        print(file=f)

        for map_tileset, map_palette, palette in self.palettes:
            f.write(CHARACTERS[map_tileset])
            f.write(CHARACTERS[map_palette])
            print(str(palette), file=f)
        print(file=f)
        print(file=f)

        for i in range(1024):
            print(self.arrangement_collision_string_rep(i), file=f)

    def from_file(self, f):
        self.minitiles.tiles = [None] * 896
        for i in range(512):
            self.minitile_from_string(i, f.readline()[:-1])
            self.minitile_from_string(i ^ 512, f.readline()[:-1])
            f.readline()
        f.readline()

        while True:
            line = f.readline()
            if line == "\n":
                break
            map_tileset = int(line[0], 32)
            map_palette = int(line[1], 32)
            palette = EbMapPalette()
            palette.from_string(line[2:-1])
            self.add_palette(map_tileset, map_palette, palette)
        f.readline()

        for i in range(1024):
            self.arrangement_collision_from_string(i, f.readline()[:-1])