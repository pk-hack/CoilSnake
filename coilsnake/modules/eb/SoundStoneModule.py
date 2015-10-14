from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbTileArrangement, EbGraphicTileset
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, to_snes_address, write_asm_pointer

GRAPHICS_ASM_POINTER_OFFSET = 0x4ACF0
PALETTE_OFFSET = 0xEF806

SOUND_STONE_SUBPALETTES = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],

    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],

    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],

    [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1],
    [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1]
]

SOUND_STONE_ARRANGEMENT = EbTileArrangement(width=16, height=22)
for y in range(SOUND_STONE_ARRANGEMENT.height):
    for x in range(SOUND_STONE_ARRANGEMENT.width):
        SOUND_STONE_ARRANGEMENT[x, y].tile = y * SOUND_STONE_ARRANGEMENT.width + x
        SOUND_STONE_ARRANGEMENT[x, y].subpalette = SOUND_STONE_SUBPALETTES[y][x]


class SoundStoneModule(EbModule):
    NAME = "Sound Stone"
    FREE_RANGES = [(0x0EDD5D, 0x0EF805)]  # Sound stone graphics

    def __init__(self):
        super(SoundStoneModule, self).__init__()
        self.tileset = EbGraphicTileset(num_tiles=352, tile_width=8, tile_height=8)
        self.palette = EbPalette(num_subpalettes=6, subpalette_length=16)

    def read_from_rom(self, rom):
        graphics_offset = from_snes_address(read_asm_pointer(
            block=rom, offset=GRAPHICS_ASM_POINTER_OFFSET))
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=rom, offset=graphics_offset)
            self.tileset.from_block(block=compressed_block, bpp=4)
        self.palette.from_block(block=rom, offset=PALETTE_OFFSET)

    def write_to_rom(self, rom):
        tileset_block_size = self.tileset.block_size(bpp=4)
        with EbCompressibleBlock(tileset_block_size) as compressed_block:
            self.tileset.to_block(block=compressed_block, offset=0, bpp=4)
            compressed_block.compress()
            tileset_offset = rom.allocate(data=compressed_block)
            write_asm_pointer(block=rom, offset=GRAPHICS_ASM_POINTER_OFFSET, pointer=to_snes_address(tileset_offset))
        self.palette.to_block(block=rom, offset=PALETTE_OFFSET)

    def read_from_project(self, resource_open):
        with resource_open("Logos/SoundStone", "png") as image_file:
            image = open_indexed_image(image_file)
            self.palette.from_image(image)
            self.tileset.from_image(image, SOUND_STONE_ARRANGEMENT, self.palette)

    def write_to_project(self, resource_open):
        image = SOUND_STONE_ARRANGEMENT.image(self.tileset, self.palette)
        with resource_open("Logos/SoundStone", "png") as image_file:
            image.save(image_file, "png")

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version < 8:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)