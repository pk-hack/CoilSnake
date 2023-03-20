import logging

from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import yml_dump, yml_load
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, \
    write_asm_pointer, to_snes_address

log = logging.getLogger(__name__)

TILESET_POINTER = 0x04C32F
ARRANGEMENT_POINTER = 0x04C388
PALETTE_POINTER = 0x04C3C3

ARRANGEMENT_WIDTH = 32
ARRANGEMENT_HEIGHT = 32
NUM_SUBPALETTES = 8
NUM_TILES = 1024
TILE_WIDTH = 8
TILE_HEIGHT = 8
TILESET_BPP = 4
SUBPALETTE_LENGTH = 16
NESS_OFFSET = 0x0000
JEFF_OFFSET = 0x8000

OLD_DEATH_SCREEN_PATH = "Logos/DeathScreen"
NESS_DEATH_SCREEN_PATH = "Logos/DeathScreen_Ness"
JEFF_DEATH_SCREEN_PATH = "Logos/DeathScreen_Jeff"
DEATH_SCREEN_SUBPALETTES_PATH = "Logos/DeathScreen_palettes"

class DeathScreenModule(EbModule):
    """Extracts the death screen data from EarthBound."""

    NAME = "Death Screen"
    FREE_RANGES = [
        (0x21cfaf, 0x21d4f3),  # Tileset
        (0x21d4f4, 0x21d5e7),  # Palette
        (0x21d5e8, 0x21d6e1)   # Arrangement
    ]

    def __init__(self):
        super(DeathScreenModule, self).__init__()

        self.ness_tileset = EbGraphicTileset(
            num_tiles=NUM_TILES, tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT
        )
        self.jeff_tileset = EbGraphicTileset(
            num_tiles=NUM_TILES, tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT
        )
        self.arrangement = EbTileArrangement(
            width=ARRANGEMENT_WIDTH, height=ARRANGEMENT_HEIGHT
        )
        self.palette = EbPalette(
            num_subpalettes=NUM_SUBPALETTES,
            subpalette_length=SUBPALETTE_LENGTH
        )

    def read_from_rom(self, rom):
        with EbCompressibleBlock() as block:
            # Read the tileset data
            block.from_compressed_block(
                block=rom, offset=from_snes_address(
                    read_asm_pointer(rom, TILESET_POINTER)
                )
            )
            self.ness_tileset.from_block(block=block, offset=NESS_OFFSET, bpp=TILESET_BPP)
            self.jeff_tileset.from_block(block=block, offset=JEFF_OFFSET, bpp=TILESET_BPP)

            # Read the arrangement data
            block.from_compressed_block(
                block=rom, offset=from_snes_address(
                    read_asm_pointer(rom, ARRANGEMENT_POINTER)
                )
            )
            self.arrangement.from_block(block=block, offset=0)

            # Read the palette data
            block.from_compressed_block(
                block=rom, offset=from_snes_address(
                    read_asm_pointer(rom, PALETTE_POINTER)
                )
            )
            self.palette.from_block(block=block, offset=0)

    def write_to_rom(self, rom):
        # Write the tileset data
        block_size = self.ness_tileset.block_size(bpp=TILESET_BPP) + self.jeff_tileset.block_size(bpp=TILESET_BPP)
        with EbCompressibleBlock(block_size) as block:
            self.ness_tileset.to_block(block=block, offset=NESS_OFFSET, bpp=TILESET_BPP)
            self.jeff_tileset.to_block(block=block, offset=JEFF_OFFSET, bpp=TILESET_BPP)
            self._write_compressed_block(rom, block, TILESET_POINTER)

        # Write the tile arrangement data
        block_size = self.arrangement.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.arrangement.to_block(block=block, offset=0)
            self._write_compressed_block(rom, block, ARRANGEMENT_POINTER)

        # Write the palette data
        block_size = self.palette.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.palette.to_block(block=block, offset=0)
            self._write_compressed_block(
                rom, block, PALETTE_POINTER
            )

    def read_from_project(self, resource_open):
        with resource_open(NESS_DEATH_SCREEN_PATH, "png") as f:
            image = open_indexed_image(f)
            self.arrangement.from_image(image, self.ness_tileset, self.palette, True, False)
        with resource_open(JEFF_DEATH_SCREEN_PATH, "png") as f:
            image = open_indexed_image(f)
            self.jeff_tileset.from_image(image, self.arrangement, self.palette)
        with resource_open(DEATH_SCREEN_SUBPALETTES_PATH, "yml", True) as f:
            subpalettes = yml_load(f)
            for subpalette, tiles in subpalettes.items():
                for x, y in tiles:
                    self.arrangement[x, y].subpalette = subpalette

    def write_to_project(self, resource_open):
        with resource_open(NESS_DEATH_SCREEN_PATH, "png") as f:
            image = self.arrangement.image(self.ness_tileset, self.palette, True)
            image.save(f)
        with resource_open(JEFF_DEATH_SCREEN_PATH, "png") as f:
            image = self.arrangement.image(self.jeff_tileset, self.palette, True)
            image.save(f)
        with resource_open(DEATH_SCREEN_SUBPALETTES_PATH, "yml", True) as f:
            subpalettes = {}
            for x in range(ARRANGEMENT_WIDTH):
                for y in range(ARRANGEMENT_HEIGHT):
                    subpalette = self.arrangement[x, y].subpalette
                    if subpalette not in subpalettes:
                        subpalettes[subpalette] = []
                    subpalettes[subpalette].append((x, y))
            yml_dump(subpalettes, f, None)

    def upgrade_project(
            self, old_version, new_version, rom, resource_open_r,
            resource_open_w, resource_delete):
        # version 1-8: no death screen support
        # version   9: Only supported Ness' death screen (DeathScreen.png)
        # version 10+: Supports Ness and Jeff (DeathScreen_*.png)
        if old_version <= 9:
            # Extract DeathScreen_Ness and DeathScreen_Jeff
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)
        if old_version == 9:
            # Move DeathScreen.png over newly-extracted DeathScreen_Ness.png
            with resource_open_r(OLD_DEATH_SCREEN_PATH, "png") as old:
                with resource_open_w(NESS_DEATH_SCREEN_PATH, "png") as new:
                    image = open_indexed_image(old)
                    image.save(new)
            # Delete old DeathScreen.png now that we've copied it
            resource_delete(OLD_DEATH_SCREEN_PATH)

    @staticmethod
    def _write_compressed_block(rom, compressed_block, pointer):
        compressed_block.compress()
        new_offset = rom.allocate(data=compressed_block)
        write_asm_pointer(
            block=rom, offset=pointer, pointer=to_snes_address(new_offset)
        )
