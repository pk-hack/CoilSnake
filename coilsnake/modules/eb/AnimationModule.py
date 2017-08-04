from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.pointer import from_snes_address
from coilsnake.util.common.yml import yml_dump

import itertools

ANIMATION_SEQUENCE_POINTERS_TABLE_DEFAULT_OFFSET = 0xcc2de1

# The size of all of these animations is the size of the whole screen

# The End
# The actual graphics are 18 tiles
# So, offset from the beginning, the graphics data ends at (18 * 8 * 8 * 2) / 8 = 0x120
# Palette from 0x120 to 0x127?
# Tile arrangement is from 0x128 to 0xF27 because it encompases the entire screen
# But, there are two frames, so will probably need to split
# Each tile is 2 bytes, the tile arrangement is 0xe00 in size, so there are 1792 tiles
# So let's try 56x32

# Maybe make EbCompressedGraphic, but need support for multiple arrangements
class Animation:
    # All animations take up the entirety of the screen
    SCREEN_WIDTH_TILES = 32
    SCREEN_HEIGHT_TILES = 28

    def __init__(self, graphics_data_size, frame_count):   
        self.tile_width = 8
        self.tile_height = 8
        self.bpp = 2

        self.frame_count = frame_count
        self.graphics_data_size = graphics_data_size

        self.num_tiles = graphics_data_size * 8 // (self.tile_width * self.tile_height * self.bpp)

        # I'm guessing 4 colors because it is 2bpp. Again, how does eb tell?
        self.palettes = [EbPalette(num_subpalettes=1, subpalette_length=4)]
        self.graphics = EbGraphicTileset(num_tiles=self.num_tiles, tile_width=self.tile_width, tile_height=self.tile_height)
        self.arrangements = [EbTileArrangement(width=Animation.SCREEN_WIDTH_TILES, height=Animation.SCREEN_HEIGHT_TILES) for i in range(self.frame_count)]

    def from_block(self, block, offset):
        with EbCompressibleBlock() as compressed_block:
            compressed_block.from_compressed_block(block=block, offset=offset)
            self.graphics.from_block(block=compressed_block,
                                     offset=0,
                                     bpp=self.bpp)

            # These animations appear to have a single palette
            self.palettes[0].from_block(block=compressed_block, offset=self.graphics_data_size)

            # Calculate where the arrangement information begins
            arrangement_offset = self.graphics_data_size + self.palettes[0].block_size()

            # Read in the arrangements (one per frame)
            for i, arrangement in enumerate(self.arrangements):
                offset = arrangement_offset + (i * arrangement.block_size())
                arrangement.from_block(block=compressed_block, offset=offset)            

    def images(self, arrangements=None):
        if not arrangements:
            arrangements = self.arrangements
        return [arrangement.image(self.graphics, palette) for (arrangement, palette) in itertools.product(self.arrangements, self.palettes)]

    def image(self, arrangements=None):
        return self.images(arrangements=arrangements)[0]

class AnimationModule(EbModule):
    """ Extracts non-battle animations from Earthbound. """
    NAME = "Animations"

    def __init__(self):
        super(AnimationModule, self).__init__()
        self.pointer_table = eb_table_from_offset(
            offset=ANIMATION_SEQUENCE_POINTERS_TABLE_DEFAULT_OFFSET
        )
        self.animations = []

    def read_from_rom(self, rom):
        self.pointer_table.from_block(
            rom, offset=from_snes_address(ANIMATION_SEQUENCE_POINTERS_TABLE_DEFAULT_OFFSET))

        for index in range(self.pointer_table.num_rows):
            row = self.pointer_table[index]
            offset = row[0]
            graphics_data_size = row[1]
            frame_count = row[2]

            # The first entry in the table has no data, only add animations that have data
            if graphics_data_size > 0:
                animation = Animation(graphics_data_size=graphics_data_size, frame_count=frame_count)
                animation.from_block(rom, from_snes_address(offset))
                self.animations.append(animation)

    def write_to_rom(self, rom):
        self.pointer_table.to_block(
            rom, offset=from_snes_address(ANIMATION_SEQUENCE_POINTERS_TABLE_DEFAULT_OFFSET))

    def read_from_project(self, resource_open):
        return

    def write_to_project(self, resource_open):
        animation_data = {}
        for i, animation in enumerate(self.animations):
            animation_data[i] = {"graphics data size": animation.graphics_data_size, "frames": len(animation.arrangements)}
            for j, image in enumerate(animation.images()):
                with resource_open("Animations/{}/{}".format(i, str(j).zfill(3)), "png") as f:
                    image.save(f, "png")
        
        with resource_open("Animations/animations", "yml", True) as f:
            yml_dump(animation_data, f, default_flow_style=False)
        return

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        return