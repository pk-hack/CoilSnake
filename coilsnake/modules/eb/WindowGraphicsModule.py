from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import EbStandardTextTableEntry
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, write_asm_pointer, to_snes_address

GRAPHICS_1_ASM_POINTER_OFFSET = 0x47c47
GRAPHICS_2_ASM_POINTER_OFFSET = 0x47caa
FLAVOR_NAME_ASM_POINTER_OFFSETS = [0x1F70F, 0x1F72A, 0x1F745, 0x1F760, 0x1F77B]
FLAVOR_NAME_ENTRY = EbStandardTextTableEntry.create(size=25)
FLAVOR_PALETTES_OFFSET = 0x201fc8

ARRANGEMENT_PREVIEW_SUBPALETTES = [
    0, 0, 0, 0, 1, 1, 1, 4, 4, 4, 4, 6, 6, 6, 6, 6,
    7, 7, 7, 7, 7, 7, 7, 4, 4, 4, 4, 6, 6, 6, 6, 6,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 6,
    0, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 6, 6, 6, 6, 3, 3, 6,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 6,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 0, 0,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 0, 0
]
ARRANGEMENT_1 = EbTileArrangement(width=16, height=26)
for y in range(ARRANGEMENT_1.height):
    for x in range(ARRANGEMENT_1.width):
        i = y * ARRANGEMENT_1.width + x
        ARRANGEMENT_1[x, y].tile = i
        ARRANGEMENT_1[x, y].subpalette = ARRANGEMENT_PREVIEW_SUBPALETTES[i]
ARRANGEMENT_2 = EbTileArrangement(width=7, height=1)
for y in range(ARRANGEMENT_2.height):
    for x in range(ARRANGEMENT_2.width):
        ARRANGEMENT_2[x, y].tile = y * ARRANGEMENT_1.width + x
        ARRANGEMENT_2[x, y].subpalette = 0


class WindowGraphicsModule(EbModule):
    NAME = "Window Graphics"
    FREE_RANGES = [(0x200000, 0x20079f)]  # Graphics

    def __init__(self):
        super(WindowGraphicsModule, self).__init__()
        self.graphics_1 = EbGraphicTileset(num_tiles=416, tile_width=8, tile_height=8)
        self.graphics_2 = EbGraphicTileset(num_tiles=7, tile_width=8, tile_height=8)

        self.flavor_palettes = [EbPalette(8, 4) for i in range(7)]
        self.flavor_names = dict()

    def read_from_rom(self, rom):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(
                block=rom,
                offset=from_snes_address(read_asm_pointer(rom, GRAPHICS_1_ASM_POINTER_OFFSET)))
            self.graphics_1.from_block(block=compressed_block, bpp=2)

        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(
                block=rom,
                offset=from_snes_address(read_asm_pointer(rom, GRAPHICS_2_ASM_POINTER_OFFSET)))
            self.graphics_2.from_block(block=compressed_block, bpp=2)

        # Read palettes
        offset = FLAVOR_PALETTES_OFFSET
        for palette in self.flavor_palettes:
            palette.from_block(block=rom, offset=offset)
            offset += 64

        # Read names
        for asm_pointer_offset in FLAVOR_NAME_ASM_POINTER_OFFSETS:
            self.flavor_names[asm_pointer_offset] = FLAVOR_NAME_ENTRY.from_block(
                block=rom,
                offset=from_snes_address(read_asm_pointer(block=rom, offset=asm_pointer_offset)))

    def write_to_rom(self, rom):
        graphics_1_block_size = self.graphics_1.block_size(bpp=2)
        with EbCompressibleBlock(graphics_1_block_size) as compressed_block:
            self.graphics_1.to_block(block=compressed_block, offset=0, bpp=2)
            compressed_block.compress()
            graphics_1_offset = rom.allocate(data=compressed_block)
            write_asm_pointer(block=rom, offset=GRAPHICS_1_ASM_POINTER_OFFSET,
                              pointer=to_snes_address(graphics_1_offset))

        graphics_2_block_size = self.graphics_2.block_size(bpp=2)
        with EbCompressibleBlock(graphics_2_block_size) as compressed_block:
            self.graphics_2.to_block(block=compressed_block, offset=0, bpp=2)
            compressed_block.compress()
            graphics_2_offset = rom.allocate(data=compressed_block)
            write_asm_pointer(block=rom, offset=GRAPHICS_2_ASM_POINTER_OFFSET,
                              pointer=to_snes_address(graphics_2_offset))

        # Write palettes
        offset = FLAVOR_PALETTES_OFFSET
        for palette in self.flavor_palettes:
            palette.to_block(block=rom, offset=offset)
            offset += 64

        # Write names
        for asm_pointer_offset in FLAVOR_NAME_ASM_POINTER_OFFSETS:
            name = self.flavor_names[asm_pointer_offset]
            offset = rom.allocate(size=FLAVOR_NAME_ENTRY.size)
            FLAVOR_NAME_ENTRY.to_block(block=rom, offset=offset, value=name)
            write_asm_pointer(block=rom, offset=asm_pointer_offset, pointer=to_snes_address(offset))

    def write_to_project(self, resource_open):
        for i, palette in enumerate(self.flavor_palettes):
            with resource_open("WindowGraphics/Windows1_" + str(i), "png") as image_file:
                image = ARRANGEMENT_1.image(tileset=self.graphics_1, palette=palette)
                image.save(image_file, "png")
            with resource_open("WindowGraphics/Windows2_" + str(i), "png") as image_file:
                image = ARRANGEMENT_2.image(tileset=self.graphics_2, palette=palette.get_subpalette(7))
                image.save(image_file, "png")

        # Write names
        with resource_open("WindowGraphics/flavor_names", "txt", True) as f:
            for asm_pointer_offset in FLAVOR_NAME_ASM_POINTER_OFFSETS:
                print(self.flavor_names[asm_pointer_offset], file=f)

    def read_from_project(self, resource_open):
        # Read graphics. Just use the first of each image.
        with resource_open("WindowGraphics/Windows1_0", "png") as image_file:
            image = open_indexed_image(image_file)
            self.graphics_1.from_image(image=image,
                                       arrangement=ARRANGEMENT_1,
                                       palette=self.flavor_palettes[0])

        with resource_open("WindowGraphics/Windows2_0", "png") as image_file:
            image = open_indexed_image(image_file)
            self.graphics_2.from_image(image=image,
                                       arrangement=ARRANGEMENT_2,
                                       palette=self.flavor_palettes[0].get_subpalette(7))

        # Read pals from Windows1 of each flavor.
        # Read subpal 7 from Windows2 of each flavor.
        for i, palette in enumerate(self.flavor_palettes):
            # Read all the palette data from Windows1
            with resource_open("WindowGraphics/Windows1_" + str(i), "png") as image_file:
                image = open_indexed_image(image_file)
                palette.from_image(image=image)

            with resource_open("WindowGraphics/Windows2_" + str(i), "png") as image_file:
                image = open_indexed_image(image_file)
                palette_data = image.getpalette()
                m = 0
                for k in range(4):
                    palette[7, k].from_tuple((palette_data[m], palette_data[m + 1], palette_data[m + 2]))
                    m += 3

        # Read names
        with resource_open("WindowGraphics/flavor_names", "txt", True) as f:
            for asm_pointer_offset in FLAVOR_NAME_ASM_POINTER_OFFSETS:
                name = f.readline()[:-1]
                self.flavor_names[asm_pointer_offset] = FLAVOR_NAME_ENTRY.from_yml_rep(name)
