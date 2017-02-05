import logging

from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer

log = logging.getLogger(__name__)

BG_TILESET_POINTER = 0xebf2
BG_ARRANGEMENT_POINTER = 0xec1d
BG_ANIM_PALETTE_POINTER = 0xec9d
BG_PALETTE_POINTER = 0xecc6

BG_ARRANGEMENT_WIDTH = 32
BG_ARRANGEMENT_HEIGHT = 28
BG_SUBPALETTE_LENGTH = 256
BG_NUM_ANIM_SUBPALETTES = 20
BG_NUM_TILES = 256
BG_TILESET_BPP = 8

CHARS_TILESET_POINTER = 0xEC49
CHARS_ANIM_PALETTES_POINTER = 0xEC83
CHARS_PALETTE_POINTER = 0x3F492

CHARS_SUBPALETTE_LENGTH = 16
CHARS_NUM_ANIM_SUBPALETTES = 14
CHARS_NUM_TILES = 1024
CHARS_TILESET_BPP = 4

ANIM_SUBPALETTE_LENGTH = 16

NUM_ANIM_FRAMES = BG_NUM_ANIM_SUBPALETTES + CHARS_NUM_ANIM_SUBPALETTES
NUM_CHARS = 9
NUM_SUBPALETTES = 1

ANIM_DATA_TABLE_POINTER = 0x21CF9D
ANIM_DATA_POINTER_OFFSET = 0x210000


def decompress_block(rom, block, pointer):
    block.from_compressed_block(
        block=rom,
        offset=from_snes_address(read_asm_pointer(rom, pointer))
    )


class TitleScreenModule(EbModule):
    NAME = "Title Screen"
    FREE_RANGES = []

    def __init__(self):
        super(TitleScreenModule, self).__init__()

        # Background data (includes the central "B", the copyright
        # notice and the glow around the letters)
        self.bg_tileset = EbGraphicTileset(num_tiles=BG_NUM_TILES)
        self.bg_arrangement = EbTileArrangement(
            width=BG_ARRANGEMENT_WIDTH, height=BG_ARRANGEMENT_HEIGHT
        )
        self.bg_anim_palette = EbPalette(
            num_subpalettes=BG_NUM_ANIM_SUBPALETTES,
            subpalette_length=ANIM_SUBPALETTE_LENGTH)
        self.bg_palette = EbPalette(
            num_subpalettes=NUM_SUBPALETTES,
            subpalette_length=BG_SUBPALETTE_LENGTH
        )

        # Characters data (the title screen's animated letters)
        self.chars_tileset = EbGraphicTileset(num_tiles=CHARS_NUM_TILES)
        self.chars_anim_palette = EbPalette(
            num_subpalettes=CHARS_NUM_ANIM_SUBPALETTES,
            subpalette_length=ANIM_SUBPALETTE_LENGTH
        )
        self.chars_palette = EbPalette(
            num_subpalettes=NUM_SUBPALETTES,
            subpalette_length=CHARS_SUBPALETTE_LENGTH
        )

        self.anim_data = []

    def read_from_rom(self, rom):
        self.read_background_data_from_rom(rom)
        self.read_chars_data_from_rom(rom)
        self.read_anim_data_from_rom(rom)

        # Add the last frame of the characters' animated palette into
        # the background static palette.
        bg_palette = self.bg_palette.list()
        bg_palette[0x80*3:(0x80+ANIM_SUBPALETTE_LENGTH)*3] =\
            self.chars_anim_palette.get_subpalette(
                CHARS_NUM_ANIM_SUBPALETTES-1
            ).list()
        self.bg_palette.from_list(bg_palette)

    def read_background_data_from_rom(self, rom):
        with EbCompressibleBlock() as block:
            # Read the background tileset data
            decompress_block(rom, block, BG_TILESET_POINTER)
            self.bg_tileset.from_block(
                block=block, offset=0, bpp=BG_TILESET_BPP
            )

            # Read the background tile arrangement data
            decompress_block(rom, block, BG_ARRANGEMENT_POINTER)
            self.bg_arrangement.from_block(block=block, offset=0)

            # Read the background palette data
            # The decompressed data is smaller than the expected value,
            # so it is extended with black entries.
            decompress_block(rom, block, BG_PALETTE_POINTER)
            block.from_array(block.to_array() + [0] * (0x200 - len(block)))
            self.bg_palette.from_block(block=block, offset=0)

            # Read the background animated palette data
            # Each subpalette corresponds to an animation frame.
            decompress_block(rom, block, BG_ANIM_PALETTE_POINTER)
            self.bg_anim_palette.from_block(block=block, offset=0)

    def read_chars_data_from_rom(self, rom):
        with EbCompressibleBlock() as block:
            # Read the background tileset data
            decompress_block(rom, block, CHARS_TILESET_POINTER)
            self.chars_tileset.from_block(
                block=block, offset=0, bpp=CHARS_TILESET_BPP
            )

            # Read the background palette data
            decompress_block(rom, block, CHARS_PALETTE_POINTER)
            self.chars_palette.from_block(block=block, offset=0)

            # Read the background animated palette data
            # Each subpalette corresponds to an animation frame.
            decompress_block(rom, block, CHARS_ANIM_PALETTES_POINTER)
            self.chars_anim_palette.from_block(block=block, offset=0)

    def read_anim_data_from_rom(self, rom):
        self.anim_data = []
        for char in xrange(NUM_CHARS):
            char_data = []
            offset = ANIM_DATA_POINTER_OFFSET + rom.read_multi(
                ANIM_DATA_TABLE_POINTER + char*2, 2
            )
            while True:
                entry = TitleScreenAnimEntry()
                entry.from_block(rom, offset)
                char_data.append(entry)
                offset += 5
                if entry.is_final():
                    break
            self.anim_data.append(char_data)

    def write_to_rom(self, rom):
        pass

    def read_from_project(self, resource_open):
        pass

    def write_to_project(self, resource_open):
        # Write out the background's animated frames
        frame_path_format = "TitleScreen/Background/{:02d}"
        for frame in xrange(NUM_ANIM_FRAMES):
            palette = EbPalette(NUM_SUBPALETTES, BG_SUBPALETTE_LENGTH)
            if frame < CHARS_NUM_ANIM_SUBPALETTES:
                colors = [0] * BG_SUBPALETTE_LENGTH * 3
                colors[0x80 * 3:(0x80 + ANIM_SUBPALETTE_LENGTH) * 3] = \
                    self.chars_anim_palette.get_subpalette(frame).list()
            else:
                colors = self.bg_palette.list()
                colors[0x70 * 3:(0x70 + ANIM_SUBPALETTE_LENGTH) * 3] = \
                    self.bg_anim_palette.get_subpalette(
                        frame - CHARS_NUM_ANIM_SUBPALETTES
                    ).list()
            palette.from_list(colors)
            with resource_open(frame_path_format.format(frame), "png") as f:
                image = self.bg_arrangement.image(self.bg_tileset, palette)
                image.save(f)

        # Write out the background's "initial flash"
        with resource_open(
            "TitleScreen/Background/InitialFlash", "png"
        ) as f:
            palette = EbPalette(
                num_subpalettes=NUM_SUBPALETTES,
                subpalette_length=BG_SUBPALETTE_LENGTH,
                rgb_list=[0xFF] * 128 * 3 + [0x0] * 128 * 3
            )
            image = self.bg_arrangement.image(self.bg_tileset, palette)
            image.save(f)

        # Write out the background's static look
        with resource_open(
            "TitleScreen/Background/Static", "png"
        ) as f:
            image = self.bg_arrangement.image(self.bg_tileset, self.bg_palette)
            image.save(f)

        # Write out the characters' animation
        for c, char_data in enumerate(self.anim_data):
            arrangement = EbTileArrangement(3, 6)
            for e, entry in enumerate(char_data):
                tile = entry.tile & (CHARS_NUM_TILES - 1)
                x = (entry.x+16)/8
                y = (entry.y+24)/8
                arrangement[x, y].tile = tile
                if entry.is_border():
                    arrangement[x+1, y].tile = tile + 1
                    arrangement[x, y+1].tile = tile + 16
                    arrangement[x+1, y+1].tile = tile + 17

            for p in xrange(CHARS_NUM_ANIM_SUBPALETTES):
                with resource_open(
                    "TitleScreen/Chars/{}/{}".format(c, p), "png"
                ) as f:
                    image = arrangement.image(
                        self.chars_tileset,
                        self.chars_anim_palette.get_subpalette(p)
                    )
                    image.save(f)

    def upgrade_project(
            self, old_version, new_version, rom, resource_open_r,
            resource_open_w, resource_delete):
        pass


class TitleScreenAnimEntry(object):

    def __init__(self, x=0, y=0, tile=0, flags=0):
        self.x = x
        self.y = y
        self.tile = tile
        self.flags = flags

    def from_block(self, block, offset=0):
        y = block[offset]
        self.y = y if y < 128 else -(256-y)
        self.tile = block.read_multi(offset+1, 2)
        x = block[offset+3]
        self.x = x if x < 128 else -(256-x)
        self.flags = block[offset+4]

    def is_border(self):
        return (self.flags & 0x01) != 0

    def is_final(self):
        return (self.flags & 0x80) != 0

    def __str__(self):
        return "<tile={}, x={}, y={}, flags={}, unknown={}>".format(
            self.tile & (CHARS_NUM_TILES - 1), self.x, self.y,
            bin(self.flags)[2:], self.tile >> 10
        )
