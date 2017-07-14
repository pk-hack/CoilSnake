import logging

from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.title_screen import TitleScreenLayoutEntry, \
    CHARS_NUM_TILES
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import yml_dump, yml_load
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, \
    write_asm_pointer, to_snes_address

log = logging.getLogger(__name__)

# Background data pointers
BG_TILESET_POINTER = 0xEBF2
BG_ARRANGEMENT_POINTER = 0xEC1D
BG_ANIM_PALETTE_POINTER = 0xEC9D
BG_PALETTE_POINTER = 0xECC6
BG_PALETTE_POINTER_SECONDARY = 0xED6B

# Background data parameters
BG_ARRANGEMENT_WIDTH = 32
BG_ARRANGEMENT_HEIGHT = 32
BG_SUBPALETTE_LENGTH = 256
BG_NUM_ANIM_SUBPALETTES = 20
BG_NUM_TILES = 256
BG_TILESET_BPP = 8

# Characters data pointers
CHARS_TILESET_POINTER = 0xEC49
CHARS_ANIM_PALETTE_POINTER = 0xEC83
CHARS_PALETTE_POINTER = 0x3F492

# Characters data parameters
CHARS_SUBPALETTE_LENGTH = 16
CHARS_NUM_ANIM_SUBPALETTES = 14
CHARS_TILESET_BPP = 4

# Commmon parameters
ANIM_SUBPALETTE_LENGTH = 16
NUM_ANIM_FRAMES = BG_NUM_ANIM_SUBPALETTES + CHARS_NUM_ANIM_SUBPALETTES
NUM_CHARS = 9
NUM_SUBPALETTES = 1
TILE_WIDTH = 8
TILE_HEIGHT = 8

# Special palette slices
CHARS_ANIM_SLICE = slice(0x80, 0x80 + ANIM_SUBPALETTE_LENGTH)
BG_ANIM_SLICE = slice(0x70, 0x70 + ANIM_SUBPALETTE_LENGTH)

# Animation data bank offsets
CHARS_LAYOUT_BANK = 0xA0FE
CHARS_LAYOUT_TABLE = 0x21CF9D
CHARS_LAYOUT_POINTER_OFFSET_DEFAULT = 0x210000

# Project file paths
BG_REFERENCE_PATH = "TitleScreen/Background/Reference"
BG_FRAMES_PATH = "TitleScreen/Background/{:02d}"
BG_INITIAL_FLASH_PATH = "TitleScreen/Background/InitialFlash"
CHARS_FRAMES_PATH = "TitleScreen/Chars/{:02d}"
CHARS_INITIAL_PATH = "TitleScreen/Chars/Initial"
CHARS_POSITIONS_PATH = "TitleScreen/Chars/positions"


class TitleScreenModule(EbModule):
    """Extracts the title screen data from EarthBound.

    This module allows for the editing of the background and characters
    of the title screen. The slide-in animation for the characters is
    controlled through assembly, while the rest of the animation works
    by changing between several palettes (one for each new frame of
    animation) and keeping the same tileset for each frame.
    """

    NAME = "Title Screen"
    FREE_RANGES = [
        (0x21B211, 0x21C6E4),  # Background Tileset
        (0x21AF7D, 0x21B210),  # Background Arrangement
        (0x21CDE1, 0x21CE07),  # Background Palette
        (0x21AEFD, 0x21AF7C),  # Background Animated Palette

        (0x21C6E5, 0x21CDE0),  # Characters Tileset
        (0x21AE7C, 0x21AE82),  # Characters Palette
        (0x21AE83, 0x21AEFC),  # Characters Animated Palette

        (0x21CE08, 0x21CF9C)  # Animation Data
    ]

    def __init__(self):
        super(TitleScreenModule, self).__init__()

        # Background data (includes the central "B", the copyright
        # notice and the glow around the letters)
        self.bg_tileset = EbGraphicTileset(
            num_tiles=BG_NUM_TILES, tile_width=TILE_WIDTH,
            tile_height=TILE_HEIGHT
        )
        self.bg_arrangement = EbTileArrangement(
            width=BG_ARRANGEMENT_WIDTH, height=BG_ARRANGEMENT_HEIGHT
        )
        self.bg_anim_palette = EbPalette(
            num_subpalettes=BG_NUM_ANIM_SUBPALETTES,
            subpalette_length=ANIM_SUBPALETTE_LENGTH
        )
        self.bg_palette = EbPalette(
            num_subpalettes=NUM_SUBPALETTES,
            subpalette_length=BG_SUBPALETTE_LENGTH
        )

        # Characters data (the title screen's animated letters)
        self.chars_tileset = EbGraphicTileset(
            num_tiles=CHARS_NUM_TILES, tile_width=TILE_WIDTH,
            tile_height=TILE_HEIGHT
        )
        self.chars_anim_palette = EbPalette(
            num_subpalettes=CHARS_NUM_ANIM_SUBPALETTES,
            subpalette_length=ANIM_SUBPALETTE_LENGTH
        )
        self.chars_palette = EbPalette(
            num_subpalettes=NUM_SUBPALETTES,
            subpalette_length=CHARS_SUBPALETTE_LENGTH
        )
        self.chars_layouts = [[] for _ in xrange(NUM_CHARS)]

    def read_from_rom(self, rom):
        self.read_background_data_from_rom(rom)
        self.read_chars_data_from_rom(rom)
        self.read_chars_layouts_from_rom(rom)

        # Add the characters palette to the background data.
        self.bg_palette[0, CHARS_ANIM_SLICE] =\
            self.chars_anim_palette.get_subpalette(
                CHARS_NUM_ANIM_SUBPALETTES - 1
            )[0, :]

    def read_background_data_from_rom(self, rom):
        with EbCompressibleBlock() as block:
            # Read the background tileset data
            self._decompress_block(rom, block, BG_TILESET_POINTER)
            self.bg_tileset.from_block(
                block=block, offset=0, bpp=BG_TILESET_BPP
            )

            # Read the background tile arrangement data
            self._decompress_block(rom, block, BG_ARRANGEMENT_POINTER)
            self.bg_arrangement.from_block(block=block, offset=0)

            # Read the background palette data
            # The decompressed data is smaller than the expected value,
            # so it is extended with black entries.
            self._decompress_block(rom, block, BG_PALETTE_POINTER)
            block.from_array(
                block.to_array() + [0]*(BG_SUBPALETTE_LENGTH*2 - len(block))
            )
            self.bg_palette.from_block(block=block, offset=0)

            # Read the background animated palette data
            # Each subpalette corresponds to an animation frame.
            self._decompress_block(rom, block, BG_ANIM_PALETTE_POINTER)
            self.bg_anim_palette.from_block(block=block, offset=0)

    def read_chars_data_from_rom(self, rom):
        with EbCompressibleBlock() as block:
            # Read the characters tileset data
            self._decompress_block(rom, block, CHARS_TILESET_POINTER)
            self.chars_tileset.from_block(
                block=block, offset=0, bpp=CHARS_TILESET_BPP
            )

            # Read the characters palette data
            self._decompress_block(rom, block, CHARS_PALETTE_POINTER)
            self.chars_palette.from_block(block=block, offset=0)

            # Read the characters animated palette data
            # Each subpalette corresponds to an animation frame.
            self._decompress_block(rom, block, CHARS_ANIM_PALETTE_POINTER)
            self.chars_anim_palette.from_block(block=block, offset=0)

    def read_chars_layouts_from_rom(self, rom):
        lda_instruction = rom[CHARS_LAYOUT_BANK]
        chars_layout_pointer_offset = CHARS_LAYOUT_POINTER_OFFSET_DEFAULT

        # Check if we are dealing with the modified Rom,
        # If we are, we need to recalculate the offset to the
        # character layouts
        if lda_instruction == 0xA9:
            bank = rom[CHARS_LAYOUT_BANK + 1]
            chars_layout_pointer_offset = from_snes_address(bank << 16)

        self.chars_layouts = [[] for _ in xrange(NUM_CHARS)]
        for char in xrange(NUM_CHARS):
            # Get the location of a character's data
            offset = chars_layout_pointer_offset + rom.read_multi(
                CHARS_LAYOUT_TABLE + char*2, 2
            )

            # Read entries until a final entry is encountered
            while True:
                entry = TitleScreenLayoutEntry()
                entry.from_block(rom, offset)
                self.chars_layouts[char].append(entry)
                offset += 5
                if entry.is_final():
                    break

    def write_to_rom(self, rom):
        self.write_background_data_to_rom(rom)
        self.write_chars_data_to_rom(rom)
        self.write_chars_layouts_to_rom(rom)

    def write_background_data_to_rom(self, rom):
        # Write the background tileset data
        block_size = self.bg_tileset.block_size(bpp=BG_TILESET_BPP)
        with EbCompressibleBlock(block_size) as block:
            self.bg_tileset.to_block(block=block, offset=0, bpp=BG_TILESET_BPP)
            self._write_compressed_block(rom, block, BG_TILESET_POINTER)

        # Write the background tile arrangement data
        block_size = self.bg_arrangement.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.bg_arrangement.to_block(block=block, offset=0)
            self._write_compressed_block(rom, block, BG_ARRANGEMENT_POINTER)

        # Write the background palette data
        # There is an additional pointer to this location, so change that one
        # too
        block_size = self.bg_palette.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.bg_palette.to_block(block=block, offset=0)
            new_offset = self._write_compressed_block(
                rom, block, BG_PALETTE_POINTER
            )
            write_asm_pointer(
                block=rom, offset=BG_PALETTE_POINTER_SECONDARY,
                pointer=to_snes_address(new_offset)
            )

        # Write the background animated palette data
        block_size = self.bg_anim_palette.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.bg_anim_palette.to_block(block=block, offset=0)
            self._write_compressed_block(rom, block, BG_ANIM_PALETTE_POINTER)

    def write_chars_data_to_rom(self, rom):
        # Write the characters tileset data
        block_size = self.chars_tileset.block_size(bpp=CHARS_TILESET_BPP)
        with EbCompressibleBlock(block_size) as block:
            self.chars_tileset.to_block(
                block=block, offset=0, bpp=CHARS_TILESET_BPP
            )
            self._write_compressed_block(rom, block, CHARS_TILESET_POINTER)

        # Write the characters palette data
        block_size = self.chars_palette.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.chars_palette.to_block(block=block, offset=0)
            self._write_compressed_block(rom, block, CHARS_PALETTE_POINTER)

        # Write the characters animation palette data
        block_size = self.chars_anim_palette.block_size()
        with EbCompressibleBlock(block_size) as block:
            self.chars_anim_palette.to_block(block=block, offset=0)
            self._write_compressed_block(
                rom, block, CHARS_ANIM_PALETTE_POINTER
            )

    def write_chars_layouts_to_rom(self, rom):
        block_size = sum(
            TitleScreenLayoutEntry.block_size()*len(c)
            for c in self.chars_layouts
        )

        # Ensure the new data is located in only one bank
        # Spreading it across two banks might make part of it inaccessible.
        def can_write_to(begin):
            return begin >> 16 == (begin + block_size) >> 16

        with Block(block_size) as block:
            # Write the character animation data to the ROM
            offset = 0
            for layout in self.chars_layouts:
                for entry in layout:
                    entry.to_block(block=block, offset=offset)
                    offset += entry.block_size()
            new_offset = to_snes_address(rom.allocate(
                data=block,
                size=block_size,
                can_write_to=can_write_to
            ))

            # Write the offsets to the layouts to the ROM
            new_bank = new_offset >> 16
            new_data_start = new_offset & 0xFFFF
            data_offset = new_data_start
            for c, layout in enumerate(self.chars_layouts):
                rom[CHARS_LAYOUT_TABLE + c*2:CHARS_LAYOUT_TABLE + c*2 + 2] = [
                    data_offset & 0xFF, data_offset >> 8
                ]
                data_offset += len(layout)*TitleScreenLayoutEntry.block_size()

            # Change the offset for the character layouts
            # The way this normally works is that EarthBound stores the address
            # of the bank holding the data (0xE1 by default, hence the 0x210000
            # offset); the offsets in the table are then prefixed with that
            # address. However, reallocating the data may have changed its
            # bank, so we need to manually set it to the new bank address.

            # In order to change the offset, we are replacing a LDA instruction 
            # which addresses a direct page (0xA5) with a LDA instruction
            # that treats its operand as the constant to load (0xA9)
            # See https://wiki.superfamicom.org/snes/show/65816+Reference#instructions.
            rom[CHARS_LAYOUT_BANK:CHARS_LAYOUT_BANK + 2] = [0xA9, new_bank]

    def read_from_project(self, resource_open):
        self.read_background_data_from_project(resource_open)
        self.read_chars_data_from_project(resource_open)

    def read_background_data_from_project(self, resource_open):
        # Load the background reference image
        # The image's arrangement, tileset and palette will be used for the
        # animation frames
        with resource_open(BG_REFERENCE_PATH, "png") as f:
            image = open_indexed_image(f)
            self.bg_arrangement.from_image(
                image, self.bg_tileset, self.bg_palette
            )

        # Read the background animated frames
        for frame in xrange(NUM_ANIM_FRAMES):
            # Create temporary structures used to check consistency between
            # frames
            tileset = EbGraphicTileset(BG_NUM_TILES, TILE_WIDTH, TILE_HEIGHT)
            arrangement = EbTileArrangement(
                BG_ARRANGEMENT_WIDTH, BG_ARRANGEMENT_HEIGHT
            )
            palette = EbPalette(NUM_SUBPALETTES, BG_SUBPALETTE_LENGTH)

            # Read one frame's image data
            with resource_open(BG_FRAMES_PATH.format(frame), "png") as f:
                image = open_indexed_image(f)
                arrangement.from_image(image, tileset, palette)

            # Make sure each frame's tileset and arrangement is identical
            # The background palette is checked only if it isn't the fake
            # palette used for the first few frames
            if frame >= CHARS_NUM_ANIM_SUBPALETTES:
                # Get the background animated subpalette from the background
                # palette
                colors = palette[0, BG_ANIM_SLICE]
                self.bg_anim_palette.subpalettes[
                    frame - CHARS_NUM_ANIM_SUBPALETTES
                ] = colors
                palette[0, BG_ANIM_SLICE] = self.bg_palette[
                    0, BG_ANIM_SLICE
                ]
                if self.bg_palette != palette:
                    log.warn(
                        "Palette from background frame {} does not match "
                        "reference.".format(frame)
                    )
            if self.bg_tileset != tileset:
                log.warn(
                    "Tileset from background frame {} does not match "
                    "reference.".format(frame)
                )
            if self.bg_arrangement != arrangement:
                log.warn(
                    "Arrangement from background frame {} does not match "
                    "reference.".format(frame)
                )

    def read_chars_data_from_project(self, resource_open):
        # Read the characters positions
        with resource_open(CHARS_POSITIONS_PATH, "yml") as f:
            chars_positions = yml_load(f)

        # Read the characters animated frames
        self.chars_tileset = None
        self.chars_anim_palette = EbPalette(
            CHARS_NUM_ANIM_SUBPALETTES, ANIM_SUBPALETTE_LENGTH
        )
        original_tileset = None
        for p in xrange(CHARS_NUM_ANIM_SUBPALETTES):
            # Read one of the animation frames
            with resource_open(CHARS_FRAMES_PATH.format(p), "png") as f:
                # Create temporary structures to hold the data
                image = open_indexed_image(f)
                arrangement = EbTileArrangement(
                    image.width // TILE_WIDTH, image.height // TILE_HEIGHT
                )
                tileset = EbGraphicTileset(
                    CHARS_NUM_TILES, TILE_WIDTH, TILE_HEIGHT
                )
                anim_subpalette = EbPalette(
                    NUM_SUBPALETTES, ANIM_SUBPALETTE_LENGTH
                )
                arrangement.from_image(image, tileset, anim_subpalette, True)

            # Add the characters animation subpalette
            for i in xrange(ANIM_SUBPALETTE_LENGTH):
                self.chars_anim_palette[p, i] = anim_subpalette[0, i]

            # Add the characters tileset if not already set, otherwise
            # ensure that it the current tileset is identical
            if not self.chars_tileset:
                original_tileset = tileset
                self.chars_tileset = EbGraphicTileset(
                    CHARS_NUM_TILES, TILE_WIDTH, TILE_HEIGHT
                )
                self.chars_tileset.tiles = [
                    [[0 for _ in xrange(TILE_HEIGHT)]
                        for _ in xrange(TILE_WIDTH)]
                    for _ in xrange(CHARS_NUM_TILES)
                ]
                unused_tiles = set(xrange(CHARS_NUM_TILES))

                # Set the new character layouts
                self.chars_layouts = [[] for _ in xrange(NUM_CHARS)]
                for c, data in chars_positions.items():
                    # Get the data from the YAML file
                    x = int(data['x'] // TILE_WIDTH)
                    y = int(data['y'] // TILE_HEIGHT)
                    width = int(data['width'] // TILE_WIDTH)
                    height = int(data['height'] // TILE_HEIGHT)
                    x_offset = data['top_left_offset']['x']
                    y_offset = data['top_left_offset']['y']
                    unknown = data['unknown']

                    # Generate a list of all tiles must be visited
                    # Where possible, we try to generate a multi tile (4 tiles
                    # stored as one); otherwise, bordering tiles that are
                    # visited will all be single tiles.
                    l = [
                        (i, j) for i in xrange(0, width, 2)
                        for j in xrange(0, height, 2)
                    ]
                    if width % 2 == 1:
                        l.extend([(width-1, j) for j in xrange(1, height, 2)])
                    if height % 2 == 1:
                        l.extend([(i, height-1) for i in xrange(1, width, 2)])

                    # Generate the new reduced tileset
                    for i, j in l:
                        # Put the tile in the new tileset
                        o_tile = arrangement[x + i, y + j].tile
                        n_tile = unused_tiles.pop()
                        self.chars_tileset.tiles[n_tile] = tileset[o_tile]

                        entry = TitleScreenLayoutEntry(
                            i*8 + x_offset, j*8 + y_offset, n_tile, 0, unknown
                        )

                        # Create a multi entry if possible to save space
                        if i < width - 1 and j < height - 1:
                            entry.set_single(True)
                            o_tile_r = arrangement[x+i+1, y+j].tile
                            o_tile_d = arrangement[x+i, y+j+1].tile
                            o_tile_dr = arrangement[x+i+1, y+j+1].tile
                            n_tile_r = n_tile + 1
                            n_tile_d = n_tile + 16
                            n_tile_dr = n_tile + 17
                            unused_tiles.difference_update(
                                (n_tile_r, n_tile_d, n_tile_dr)
                            )
                            self.chars_tileset.tiles[n_tile_r] = \
                                tileset[o_tile_r]
                            self.chars_tileset.tiles[n_tile_d] = \
                                tileset[o_tile_d]
                            self.chars_tileset.tiles[n_tile_dr] = \
                                tileset[o_tile_dr]

                        self.chars_layouts[c].append(entry)
                    self.chars_layouts[c][-1].set_final(True)

            elif original_tileset != tileset:
                log.warn(
                    "Tileset from characters frame {} does not match "
                    "tileset from characters frame 0.".format(p)
                )

        # Read the initial characters palette
        with resource_open(CHARS_INITIAL_PATH, "png") as f:
            image = open_indexed_image(f)
            arrangement = EbTileArrangement(
                image.width // TILE_WIDTH, image.height // TILE_HEIGHT
            )
            tileset = EbGraphicTileset(
                CHARS_NUM_TILES, TILE_WIDTH, TILE_HEIGHT
            )
            self.chars_palette = EbPalette(
                NUM_SUBPALETTES, ANIM_SUBPALETTE_LENGTH
            )
            arrangement.from_image(image, tileset, self.chars_palette)

    def write_to_project(self, resource_open):
        self.write_background_data_to_project(resource_open)
        self.write_chars_data_to_project(resource_open)

    def write_background_data_to_project(self, resource_open):
        # Write out the reference background image
        # This image is used to get the arrangement, tileset and static palette
        # that will be used by all background images.
        with resource_open(
            BG_REFERENCE_PATH, "png"
        ) as f:
            image = self.bg_arrangement.image(self.bg_tileset, self.bg_palette)
            image.save(f)

        # Write out the background's animated frames
        for frame in xrange(NUM_ANIM_FRAMES):
            palette = EbPalette(NUM_SUBPALETTES, BG_SUBPALETTE_LENGTH)
            if frame < CHARS_NUM_ANIM_SUBPALETTES:
                palette[0, CHARS_ANIM_SLICE] = \
                    self.chars_anim_palette.get_subpalette(frame)[0, :]
            else:
                palette[0, :] = self.bg_palette.get_subpalette(0)[0, :]
                palette[0, BG_ANIM_SLICE] = \
                    self.bg_anim_palette.get_subpalette(
                        frame - CHARS_NUM_ANIM_SUBPALETTES
                    )[0, :]
            with resource_open(BG_FRAMES_PATH.format(frame), "png") as f:
                image = self.bg_arrangement.image(self.bg_tileset, palette)
                image.save(f)

    def write_chars_data_to_project(self, resource_open):
        # Build an arrangement combining every character for convenience
        chars_positions = {}
        arrangement = EbTileArrangement(3*9, 6)
        for c, layout in enumerate(self.chars_layouts):
            top_left = {'x': 128, 'y': 128}
            for e, entry in enumerate(layout):
                tile = entry.tile & (CHARS_NUM_TILES - 1)
                top_left['x'] = min(top_left['x'], int(entry.x))
                top_left['y'] = min(top_left['y'], int(entry.y))
                x = c*3 + (entry.x + 16) // 8
                y = (entry.y + 24) // 8
                arrangement[x, y].tile = tile
                if not entry.is_single():
                    arrangement[x+1, y].tile = tile + 1
                    arrangement[x, y+1].tile = tile + 16
                    arrangement[x+1, y+1].tile = tile + 17
            chars_positions[c] = {
                'x': c*3*8,
                'y': 0,
                'width': 3*8,
                'height': 6*8,
                'top_left_offset': top_left,
                'unknown': layout[0].unknown
            }

        # Write the characters animation frames
        for p in xrange(CHARS_NUM_ANIM_SUBPALETTES):
            with resource_open(CHARS_FRAMES_PATH.format(p), "png") as f:
                image = arrangement.image(
                    self.chars_tileset,
                    self.chars_anim_palette.get_subpalette(p)
                )
                image.save(f)

        # Write out the initial characters palette
        with resource_open(CHARS_INITIAL_PATH, "png") as f:
            image = arrangement.image(
                self.chars_tileset,
                self.chars_palette
            )
            image.save(f)

        # Write out the positions of the characters
        with resource_open(CHARS_POSITIONS_PATH, "yml") as f:
            yml_dump(chars_positions, f, False)

    def upgrade_project(
            self, old_version, new_version, rom, resource_open_r,
            resource_open_w, resource_delete):
        if old_version < 9:
            self.read_from_rom(rom)
            self.write_to_project(resource_open_w)

    @staticmethod
    def _decompress_block(rom, block, pointer):
        block.from_compressed_block(
            block=rom,
            offset=from_snes_address(read_asm_pointer(rom, pointer))
        )

    @staticmethod
    def _write_compressed_block(rom, compressed_block, pointer):
        compressed_block.compress()
        new_offset = rom.allocate(data=compressed_block)
        write_asm_pointer(
            block=rom, offset=pointer, pointer=to_snes_address(new_offset)
        )
        return new_offset
