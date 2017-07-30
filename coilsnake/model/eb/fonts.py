from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbTileArrangement, EbGraphicTileset
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, write_asm_pointer, to_snes_address


FONT_IMAGE_PALETTE = EbPalette(1, 2)
FONT_IMAGE_PALETTE[0, 0].from_tuple((255, 255, 255))
FONT_IMAGE_PALETTE[0, 1].from_tuple((0, 0, 0))
FONT_IMAGE_ARRANGEMENT_WIDTH = 16
_FONT_IMAGE_ARRANGEMENT_96 = EbTileArrangement(width=FONT_IMAGE_ARRANGEMENT_WIDTH, height=6)
_FONT_IMAGE_ARRANGEMENT_128 = EbTileArrangement(width=FONT_IMAGE_ARRANGEMENT_WIDTH, height=8)

for y in range(_FONT_IMAGE_ARRANGEMENT_96.height):
    for x in range(_FONT_IMAGE_ARRANGEMENT_96.width):
        _FONT_IMAGE_ARRANGEMENT_96[x, y].tile = y * _FONT_IMAGE_ARRANGEMENT_96.width + x
for y in range(_FONT_IMAGE_ARRANGEMENT_128.height):
    for x in range(_FONT_IMAGE_ARRANGEMENT_128.width):
        _FONT_IMAGE_ARRANGEMENT_128[x, y].tile = y * _FONT_IMAGE_ARRANGEMENT_128.width + x


class EbFont(object):
    def __init__(self, num_characters=96, tile_width=16, tile_height=8):
        self.num_characters = num_characters
        self.tileset = EbGraphicTileset(num_tiles=num_characters, tile_width=tile_width, tile_height=tile_height)
        self.character_widths = None

    def from_block(self, block, tileset_offset, character_widths_offset):
        self.tileset.from_block(block=block, offset=tileset_offset, bpp=1)
        for i in range(96, self.num_characters):
            self.tileset.clear_tile(i, color=1)
        self.character_widths = block[character_widths_offset:character_widths_offset + self.num_characters].to_list()

    def to_block(self, block):
        tileset_offset = block.allocate(size=self.tileset.block_size(bpp=1))
        self.tileset.to_block(block=block, offset=tileset_offset, bpp=1)

        character_widths_offset = block.allocate(size=self.num_characters)
        block[character_widths_offset:character_widths_offset + self.num_characters] = self.character_widths

        return tileset_offset, character_widths_offset

    def to_files(self, image_file, widths_file, image_format="png", widths_format="yml"):
        if self.num_characters == 96:
            image = _FONT_IMAGE_ARRANGEMENT_96.image(self.tileset, FONT_IMAGE_PALETTE)
        elif self.num_characters == 128:
            image = _FONT_IMAGE_ARRANGEMENT_128.image(self.tileset, FONT_IMAGE_PALETTE)
        image.save(image_file, image_format)
        del image

        character_widths_dict = dict(enumerate(self.character_widths))
        if widths_format == "yml":
            yml_dump(character_widths_dict, widths_file, default_flow_style=False)

    def from_files(self, image_file, widths_file, image_format="png", widths_format="yml"):
        image = open_indexed_image(image_file)

        if self.num_characters == 96:
            self.tileset.from_image(image, _FONT_IMAGE_ARRANGEMENT_96, FONT_IMAGE_PALETTE)
        elif self.num_characters == 128:
            self.tileset.from_image(image, _FONT_IMAGE_ARRANGEMENT_128, FONT_IMAGE_PALETTE)
        del image

        if widths_format == "yml":
            widths_dict = yml_load(widths_file)
            self.character_widths = [widths_dict[i] for i in range(self.tileset.num_tiles_maximum)]

    def image_size(self):
        if self.num_characters == 96:
            arr = _FONT_IMAGE_ARRANGEMENT_96
        elif self.num_characters == 128:
            arr = _FONT_IMAGE_ARRANGEMENT_128

        return arr.width * self.tileset.tile_width, arr.height * self.tileset.tile_height


_CREDITS_PREVIEW_SUBPALETTES = [
    [1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1],
    [1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
_CREDITS_PREVIEW_ARRANGEMENT = EbTileArrangement(width=16, height=12)
for y in range(_CREDITS_PREVIEW_ARRANGEMENT.height):
    for x in range(_CREDITS_PREVIEW_ARRANGEMENT.width):
        _CREDITS_PREVIEW_ARRANGEMENT[x, y].tile = y * _CREDITS_PREVIEW_ARRANGEMENT.width + x
        _CREDITS_PREVIEW_ARRANGEMENT[x, y].subpalette = _CREDITS_PREVIEW_SUBPALETTES[y][x]


class EbCreditsFont(object):
    def __init__(self):
        self.tileset = EbGraphicTileset(num_tiles=192, tile_width=8, tile_height=8)
        self.palette = EbPalette(num_subpalettes=2, subpalette_length=4)

    def from_block(self, block, tileset_asm_pointer_offset, palette_offset):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=from_snes_address(
                read_asm_pointer(block=block, offset=tileset_asm_pointer_offset)))
            self.tileset.from_block(block=compressed_block, bpp=2)
        self.palette.from_block(block=block, offset=palette_offset)

    def to_block(self, block, tileset_asm_pointer_offset, palette_offset):
        tileset_block_size = self.tileset.block_size(bpp=2)
        with EbCompressibleBlock(tileset_block_size) as compressed_block:
            self.tileset.to_block(block=compressed_block, offset=0, bpp=2)
            compressed_block.compress()
            tileset_offset = block.allocate(data=compressed_block)
            write_asm_pointer(block=block, offset=tileset_asm_pointer_offset, pointer=to_snes_address(tileset_offset))
        self.palette.to_block(block=block, offset=palette_offset)

    def to_files(self, image_file, image_format="png"):
        image = _CREDITS_PREVIEW_ARRANGEMENT.image(self.tileset, self.palette)
        image.save(image_file, image_format)
        del image

    def from_files(self, image_file, image_format="png"):
        image = open_indexed_image(image_file)
        self.palette.from_image(image)
        self.tileset.from_image(image, _CREDITS_PREVIEW_ARRANGEMENT, self.palette)
        del image