import yaml

from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbTileArrangement, EbGraphicTileset
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, write_asm_pointer, to_snes_address


_FONT_IMAGE_PALETTE = EbPalette(1, 2)
_FONT_IMAGE_PALETTE[0, 0].from_tuple((255, 255, 255))
_FONT_IMAGE_PALETTE[0, 1].from_tuple((0, 0, 0))
_FONT_IMAGE_ARRANGEMENT = EbTileArrangement(width=16, height=6)
for y in range(_FONT_IMAGE_ARRANGEMENT.height):
    for x in range(_FONT_IMAGE_ARRANGEMENT.width):
        _FONT_IMAGE_ARRANGEMENT[x, y].tile = y * _FONT_IMAGE_ARRANGEMENT.width + x


class EbFont(object):
    def __init__(self, num_characters=96, tile_width=16, tile_height=8):
        self.num_characters = num_characters
        self.tileset = EbGraphicTileset(num_tiles=num_characters, tile_width=tile_width, tile_height=tile_height)
        self.character_widths = None

    def from_block(self, block, tileset_offset, character_widths_offset):
        self.tileset.from_block(block=block, offset=tileset_offset, bpp=1)
        self.character_widths = block[character_widths_offset:character_widths_offset + self.num_characters].to_list()

    def to_block(self, block, tileset_offset, character_widths_offset):
        self.tileset.to_block(block=block, offset=tileset_offset, bpp=1)
        block[character_widths_offset:character_widths_offset + self.num_characters] = self.character_widths

    def to_files(self, image_file, widths_file, image_format="png", widths_format="yml"):
        image = _FONT_IMAGE_ARRANGEMENT.image(self.tileset, _FONT_IMAGE_PALETTE)
        image.save(image_file, image_format)
        del image

        character_widths_dict = dict(enumerate(self.character_widths))
        if widths_format == "yml":
            yaml.dump(character_widths_dict, widths_file, default_flow_style=False, Dumper=yaml.CSafeDumper)

    def from_files(self, image_file, widths_file, image_format="png", widths_format="yml"):
        image = open_indexed_image(image_file)
        self.tileset.from_image(image, _FONT_IMAGE_ARRANGEMENT, _FONT_IMAGE_PALETTE)
        del image

        if widths_format == "yml":
            widths_dict = yaml.load(widths_file, Loader=yaml.CSafeLoader)
            self.character_widths = map(lambda i: widths_dict[i], range(self.tileset.num_tiles_maximum))


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