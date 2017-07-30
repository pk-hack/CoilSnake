import logging

from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, to_snes_address, write_asm_pointer


log = logging.getLogger(__name__)

GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSETS = [0x2d1ba, 0x2d4dc, 0x2d8c3, 0x4a3ba]
ARRANGEMENT_POINTER_TABLE_ASM_POINTER_OFFSETS = [0x2d2c1, 0x2d537, 0x2d91f, 0x4a416]
PALETTE_POINTER_TABLE_ASM_POINTER_OFFSETS = [0x2d3bb, 0x2d61b, 0x2d7e8, 0x2d9e8, 0x4a4d0]

GRAPHICS_POINTER_TABLE_DEFAULT_OFFSET = 0xcad7a1
ARRANGEMENT_POINTER_TABLE_DEFAULT_OFFSET = 0xcad93d
PALETTE_POINTER_TABLE_DEFAULT_OFFSET = 0xcadad9
BACKGROUND_TABLE_OFFSET = 0xcadca1
SCROLL_TABLE_OFFSET = 0xcaf258
DISTORTION_TABLE_OFFSET = 0xcaf708


class BattleBgModule(EbModule):
    NAME = "Battle Backgrounds"
    FREE_RANGES = [(0xa0000, 0xadca0), (0xb0000, 0xbd899)]

    def __init__(self):
        super(BattleBgModule, self).__init__()
        self.graphics_pointer_table = eb_table_from_offset(offset=GRAPHICS_POINTER_TABLE_DEFAULT_OFFSET)
        self.arrangement_pointer_table = eb_table_from_offset(offset=ARRANGEMENT_POINTER_TABLE_DEFAULT_OFFSET)
        self.palette_pointer_table = eb_table_from_offset(offset=PALETTE_POINTER_TABLE_DEFAULT_OFFSET)
        self.scroll_table = eb_table_from_offset(offset=SCROLL_TABLE_OFFSET)
        self.distortion_table = eb_table_from_offset(offset=DISTORTION_TABLE_OFFSET)
        self.bg_table = eb_table_from_offset(offset=BACKGROUND_TABLE_OFFSET,
                                             hidden_columns=["Graphics and Arrangement", "Palette"])

        self.backgrounds = None
        self.palettes = None

    def __exit__(self, type, value, traceback):
        del self.graphics_pointer_table
        del self.arrangement_pointer_table
        del self.palette_pointer_table
        del self.bg_table

        del self.backgrounds
        del self.palettes

    def read_from_rom(self, rom):
        self.bg_table.from_block(block=rom, offset=from_snes_address(BACKGROUND_TABLE_OFFSET))
        self.scroll_table.from_block(block=rom, offset=from_snes_address(SCROLL_TABLE_OFFSET))
        self.distortion_table.from_block(block=rom, offset=from_snes_address(DISTORTION_TABLE_OFFSET))
        self.graphics_pointer_table.from_block(
            block=rom,
            offset=from_snes_address(read_asm_pointer(block=rom,
                                                      offset=GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSETS[0])))
        self.arrangement_pointer_table.from_block(
            block=rom,
            offset=from_snes_address(read_asm_pointer(block=rom,
                                                      offset=ARRANGEMENT_POINTER_TABLE_ASM_POINTER_OFFSETS[0])))
        self.palette_pointer_table.from_block(
            block=rom,
            offset=from_snes_address(read_asm_pointer(block=rom,
                                                      offset=PALETTE_POINTER_TABLE_ASM_POINTER_OFFSETS[0])))

        self.backgrounds = [None for i in range(self.graphics_pointer_table.num_rows)]
        self.palettes = [None for i in range(self.palette_pointer_table.num_rows)]
        for i in range(self.bg_table.num_rows):
            graphics_id = self.bg_table[i][0]
            color_depth = self.bg_table[i][2]
            if self.backgrounds[graphics_id] is None:
                # Max tiles used in rom: 421 (2bpp) 442 (4bpp)
                tileset = EbGraphicTileset(num_tiles=512, tile_width=8, tile_height=8)
                with EbCompressibleBlock() as compressed_block:
                    compressed_block.from_compressed_block(
                        block=rom,
                        offset=from_snes_address(self.graphics_pointer_table[graphics_id][0]))
                    tileset.from_block(compressed_block, offset=0, bpp=color_depth)

                arrangement = EbTileArrangement(width=32, height=32)
                with EbCompressibleBlock() as compressed_block:
                    compressed_block.from_compressed_block(
                        block=rom,
                        offset=from_snes_address(self.arrangement_pointer_table[graphics_id][0]))
                    arrangement.from_block(block=compressed_block, offset=0)

                self.backgrounds[graphics_id] = (tileset, color_depth, arrangement)
                
            palette_id = self.bg_table[i][1]
            if self.palettes[palette_id] is None:
                palette = EbPalette(num_subpalettes=1, subpalette_length=16)
                palette.from_block(block=rom, offset=from_snes_address(self.palette_pointer_table[palette_id][0]))
                self.palettes[palette_id] = palette

    def write_to_project(self, resource_open):
        with resource_open("bg_data_table", "yml", True) as f:
            self.bg_table.to_yml_file(f)
        with resource_open("bg_scrolling_table", "yml", True) as f:
            self.scroll_table.to_yml_file(f)
        with resource_open("bg_distortion_table", "yml", True) as f:
            self.distortion_table.to_yml_file(f)

        # Export BGs by table entry
        for i in range(self.bg_table.num_rows):
            tileset, color_depth, arrangement = self.backgrounds[self.bg_table[i][0]]
            palette = self.palettes[self.bg_table[i][1]]

            with resource_open("BattleBGs/" + str(i).zfill(3), "png") as f:
                image = arrangement.image(tileset, palette)
                image.save(f, "png")

    def read_from_project(self, resource_open):
        with resource_open("bg_data_table", "yml", True) as f:
            self.bg_table.from_yml_file(f)
        with resource_open("bg_scrolling_table", "yml", True) as f:
            self.scroll_table.from_yml_file(f)
        with resource_open("bg_distortion_table", "yml", True) as f:
            self.distortion_table.from_yml_file(f)

        self.backgrounds = []
        self.palettes = []
        for i in range(self.bg_table.num_rows):
            new_color_depth = self.bg_table[i][2]
            with resource_open("BattleBGs/" + str(i).zfill(3), "png") as f:
                image = open_indexed_image(f)

                new_palette = EbPalette(num_subpalettes=1, subpalette_length=16)
                new_tileset = EbGraphicTileset(num_tiles=512, tile_width=8, tile_height=8)
                new_arrangement = EbTileArrangement(width=32, height=32)

                new_arrangement.from_image(image, new_tileset, new_palette)

                for j, (tileset, color_depth, arrangement) in enumerate(self.backgrounds):
                    if (color_depth == new_color_depth) \
                            and (tileset == new_tileset) \
                            and (arrangement == new_arrangement):
                        self.bg_table[i][0] = j
                        break
                else:
                    self.bg_table[i][0] = len(self.backgrounds)
                    self.backgrounds.append((new_tileset, new_color_depth, new_arrangement))

                for j, palette in enumerate(self.palettes):
                    if palette == new_palette:
                        self.bg_table[i][1] = j
                        break
                else:
                    self.bg_table[i][1] = len(self.palettes)
                    self.palettes.append(new_palette)

    def write_to_rom(self, rom):
        # Write the data table
        self.bg_table.to_block(block=rom, offset=from_snes_address(BACKGROUND_TABLE_OFFSET))
        self.scroll_table.to_block(block=rom, offset=from_snes_address(SCROLL_TABLE_OFFSET))
        self.distortion_table.to_block(block=rom, offset=from_snes_address(DISTORTION_TABLE_OFFSET))

        # Write graphics and arrangements
        self.graphics_pointer_table.recreate(num_rows=len(self.backgrounds))
        self.arrangement_pointer_table.recreate(num_rows=len(self.backgrounds))
        for i, (tileset, color_depth, arrangement) in enumerate(self.backgrounds):
            with EbCompressibleBlock(size=tileset.block_size(bpp=color_depth)) as compressed_block:
                tileset.to_block(block=compressed_block, offset=0, bpp=color_depth)
                compressed_block.compress()
                tileset_offset = rom.allocate(data=compressed_block)
                self.graphics_pointer_table[i] = [to_snes_address(tileset_offset)]

            with EbCompressibleBlock(size=arrangement.block_size()) as compressed_block:
                arrangement.to_block(block=compressed_block, offset=0)
                compressed_block.compress()
                arrangement_offset = rom.allocate(data=compressed_block)
                self.arrangement_pointer_table[i] = [to_snes_address(arrangement_offset)]

        graphics_pointer_table_offset = rom.allocate(size=self.graphics_pointer_table.size)
        self.graphics_pointer_table.to_block(block=rom, offset=graphics_pointer_table_offset)
        for asm_pointer_offset in GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSETS:
            write_asm_pointer(block=rom,
                              offset=asm_pointer_offset,
                              pointer=to_snes_address(graphics_pointer_table_offset))

        arrangement_pointer_table_offset = rom.allocate(size=self.arrangement_pointer_table.size)
        self.arrangement_pointer_table.to_block(block=rom, offset=arrangement_pointer_table_offset)
        for asm_pointer_offset in ARRANGEMENT_POINTER_TABLE_ASM_POINTER_OFFSETS:
            write_asm_pointer(block=rom,
                              offset=asm_pointer_offset,
                              pointer=to_snes_address(arrangement_pointer_table_offset))

        # Write pals
        self.palette_pointer_table.recreate(num_rows=len(self.palettes))
        for i, palette in enumerate(self.palettes):
            with Block(32) as block:
                palette.to_block(block=block, offset=0)
                palette_offset = rom.allocate(data=block)
                self.palette_pointer_table[i] = [to_snes_address(palette_offset)]

        palette_pointer_table_offset = rom.allocate(size=self.palette_pointer_table.size)
        self.palette_pointer_table.to_block(block=rom, offset=palette_pointer_table_offset)
        for asm_pointer_offset in PALETTE_POINTER_TABLE_ASM_POINTER_OFFSETS:
            write_asm_pointer(block=rom,
                              offset=asm_pointer_offset,
                              pointer=to_snes_address(palette_pointer_table_offset))