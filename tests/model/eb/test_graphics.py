from nose.tools import assert_equal, assert_raises, assert_list_equal, assert_false, assert_true, assert_is_instance

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangementItem, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette
from tests.coilsnake_test import BaseTestCase, TilesetImageTestCase


class TestEbGraphicTileset(BaseTestCase, TilesetImageTestCase):
    def test_init(self):
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=16)
        assert_equal(tileset.num_tiles_maximum, 1)
        assert_equal(tileset.tile_width, 8)
        assert_equal(tileset.tile_height, 16)

        assert_raises(InvalidArgumentError, EbGraphicTileset, 0, 8, 8)
        assert_raises(InvalidArgumentError, EbGraphicTileset, -1, 8, 8)
        assert_raises(InvalidArgumentError, EbGraphicTileset, 1, 0, 8)
        assert_raises(InvalidArgumentError, EbGraphicTileset, 1, -1, 8)
        assert_raises(InvalidArgumentError, EbGraphicTileset, 1, 1, 8)
        assert_raises(InvalidArgumentError, EbGraphicTileset, 1, 8, 0)
        assert_raises(InvalidArgumentError, EbGraphicTileset, 1, 8, -1)

    def test_from_block_invalid(self):
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=16)
        block = Block()
        assert_raises(NotImplementedError, tileset.from_block, block, 0, 32)
        assert_raises(NotImplementedError, tileset.from_block, block, 0, 2)

    def test_from_block_1bpp(self):
        block = Block()
        block.from_list([0b00000011,
                         0b01110000,
                         0b01001001,
                         0b11110000,
                         0b01001010,
                         0b11001000,
                         0b01110001,
                         0b00000001,
                         0b00100000,
                         0b00110000,
                         0b00101000,
                         0b00101000,
                         0b01100000,
                         0b11100000,
                         0b11000000,
                         0b00000001])
        tileset = EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8)
        tileset.from_block(block, offset=0, bpp=1)
        assert_list_equal(tileset[0], [[0, 0, 0, 0, 0, 0, 1, 1],
                                       [0, 1, 1, 1, 0, 0, 0, 0],
                                       [0, 1, 0, 0, 1, 0, 0, 1],
                                       [1, 1, 1, 1, 0, 0, 0, 0],
                                       [0, 1, 0, 0, 1, 0, 1, 0],
                                       [1, 1, 0, 0, 1, 0, 0, 0],
                                       [0, 1, 1, 1, 0, 0, 0, 1],
                                       [0, 0, 0, 0, 0, 0, 0, 1]])
        assert_list_equal(tileset[1], [[0, 0, 1, 0, 0, 0, 0, 0],
                                       [0, 0, 1, 1, 0, 0, 0, 0],
                                       [0, 0, 1, 0, 1, 0, 0, 0],
                                       [0, 0, 1, 0, 1, 0, 0, 0],
                                       [0, 1, 1, 0, 0, 0, 0, 0],
                                       [1, 1, 1, 0, 0, 0, 0, 0],
                                       [1, 1, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 1]])

    def test_from_block_1bpp_out_of_bounds(self):
        block = Block()
        block.from_list([0b00000011,
                         0b01110000,
                         0b01001001,
                         0b11110000,
                         0b01001010,
                         0b11001000,
                         0b01110001,
                         0b00000001,
                         0b00100000,
                         0b00110000,
                         0b00101000,
                         0b00101000,
                         0b01100000,
                         0b11100000,
                         0b11000000,
                         0b00000001])
        tileset = EbGraphicTileset(num_tiles=3, tile_width=8, tile_height=8)
        tileset.from_block(block, offset=0, bpp=1)
        assert_list_equal(tileset[0], [[0, 0, 0, 0, 0, 0, 1, 1],
                                       [0, 1, 1, 1, 0, 0, 0, 0],
                                       [0, 1, 0, 0, 1, 0, 0, 1],
                                       [1, 1, 1, 1, 0, 0, 0, 0],
                                       [0, 1, 0, 0, 1, 0, 1, 0],
                                       [1, 1, 0, 0, 1, 0, 0, 0],
                                       [0, 1, 1, 1, 0, 0, 0, 1],
                                       [0, 0, 0, 0, 0, 0, 0, 1]])
        assert_list_equal(tileset[1], [[0, 0, 1, 0, 0, 0, 0, 0],
                                       [0, 0, 1, 1, 0, 0, 0, 0],
                                       [0, 0, 1, 0, 1, 0, 0, 0],
                                       [0, 0, 1, 0, 1, 0, 0, 0],
                                       [0, 1, 1, 0, 0, 0, 0, 0],
                                       [1, 1, 1, 0, 0, 0, 0, 0],
                                       [1, 1, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 1]])
        assert_list_equal(tileset[2], [[0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0],
                                       [0, 0, 0, 0, 0, 0, 0, 0]])

    def test_from_block_2bpp(self):
        block = Block()
        block.from_list([0b01010101,  # Tile 1
                         0b10111010,
                         0b01100100,
                         0b11001111,
                         0b10100000,
                         0b10111101,
                         0b11100001,
                         0b01101011,
                         0b10110111,
                         0b00000111,
                         0b11111010,
                         0b01111101,
                         0b00110010,
                         0b11101100,
                         0b00110110,
                         0b10111100,
                         0b11111001,  # Tile 2
                         0b01101010,
                         0b10011000,
                         0b11111111,
                         0b11001011,
                         0b00111000,
                         0b01000001,
                         0b01110001,
                         0b11001010,
                         0b11000000,
                         0b01111010,
                         0b11011101,
                         0b00011011,
                         0b00001111,
                         0b00100001,
                         0b11110000])
        tileset = EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8)
        tileset.from_block(block, offset=0, bpp=2)
        assert_list_equal(tileset[0], [[2, 1, 2, 3, 2, 1, 2, 1],
                                       [2, 3, 1, 0, 2, 3, 2, 2],
                                       [3, 0, 3, 2, 2, 2, 0, 2],
                                       [1, 3, 3, 0, 2, 0, 2, 3],
                                       [1, 0, 1, 1, 0, 3, 3, 3],
                                       [1, 3, 3, 3, 3, 2, 1, 2],
                                       [2, 2, 3, 1, 2, 2, 1, 0],
                                       [2, 0, 3, 3, 2, 3, 1, 0]])
        assert_list_equal(tileset[1], [[1, 3, 3, 1, 3, 0, 2, 1],
                                       [3, 2, 2, 3, 3, 2, 2, 2],
                                       [1, 1, 2, 2, 3, 0, 1, 1],
                                       [0, 3, 2, 2, 0, 0, 0, 3],
                                       [3, 3, 0, 0, 1, 0, 1, 0],
                                       [2, 3, 1, 3, 3, 2, 1, 2],
                                       [0, 0, 0, 1, 3, 2, 3, 3],
                                       [2, 2, 3, 2, 0, 0, 0, 1]])

    def test_to_block_invalid(self):
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=16)
        block = Block()
        assert_raises(NotImplementedError, tileset.to_block, block, 0, 32)
        assert_raises(NotImplementedError, tileset.to_block, block, 0, 2)

    def test_to_block_1bpp(self):
        tileset = EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8)
        tileset.tiles[0] = [[0, 0, 0, 0, 0, 0, 1, 1],
                            [0, 1, 1, 1, 0, 0, 0, 0],
                            [0, 1, 0, 0, 1, 0, 0, 1],
                            [1, 1, 1, 1, 0, 0, 0, 0],
                            [0, 1, 0, 0, 1, 0, 1, 0],
                            [1, 1, 0, 0, 1, 0, 0, 0],
                            [0, 1, 1, 1, 0, 0, 0, 1],
                            [0, 0, 0, 0, 0, 0, 0, 1]]
        tileset.tiles[1] = [[0, 0, 1, 0, 0, 0, 0, 0],
                            [0, 0, 1, 1, 0, 0, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0, 0],
                            [0, 0, 1, 0, 1, 0, 0, 0],
                            [0, 1, 1, 0, 0, 0, 0, 0],
                            [1, 1, 1, 0, 0, 0, 0, 0],
                            [1, 1, 0, 0, 0, 0, 0, 0],
                            [0, 0, 0, 0, 0, 0, 0, 1]]
        block = Block()
        block.from_list([0] * 16)
        tileset.to_block(block, 0, 1)
        assert_list_equal(block.to_list(), [0b00000011,
                                            0b01110000,
                                            0b01001001,
                                            0b11110000,
                                            0b01001010,
                                            0b11001000,
                                            0b01110001,
                                            0b00000001,
                                            0b00100000,
                                            0b00110000,
                                            0b00101000,
                                            0b00101000,
                                            0b01100000,
                                            0b11100000,
                                            0b11000000,
                                            0b00000001])

    def test_to_block_2bpp(self):
        tileset = EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8)
        tileset.tiles[0] = [[2, 1, 2, 3, 2, 1, 2, 1],
                            [2, 3, 1, 0, 2, 3, 2, 2],
                            [3, 0, 3, 2, 2, 2, 0, 2],
                            [1, 3, 3, 0, 2, 0, 2, 3],
                            [1, 0, 1, 1, 0, 3, 3, 3],
                            [1, 3, 3, 3, 3, 2, 1, 2],
                            [2, 2, 3, 1, 2, 2, 1, 0],
                            [2, 0, 3, 3, 2, 3, 1, 0]]
        tileset.tiles[1] = [[1, 3, 3, 1, 3, 0, 2, 1],
                            [3, 2, 2, 3, 3, 2, 2, 2],
                            [1, 1, 2, 2, 3, 0, 1, 1],
                            [0, 3, 2, 2, 0, 0, 0, 3],
                            [3, 3, 0, 0, 1, 0, 1, 0],
                            [2, 3, 1, 3, 3, 2, 1, 2],
                            [0, 0, 0, 1, 3, 2, 3, 3],
                            [2, 2, 3, 2, 0, 0, 0, 1]]
        block = Block()
        block.from_list([0] * 32)
        tileset.to_block(block, 0, 2)
        assert_list_equal(block.to_list(), [0b01010101,  # Tile 1
                                            0b10111010,
                                            0b01100100,
                                            0b11001111,
                                            0b10100000,
                                            0b10111101,
                                            0b11100001,
                                            0b01101011,
                                            0b10110111,
                                            0b00000111,
                                            0b11111010,
                                            0b01111101,
                                            0b00110010,
                                            0b11101100,
                                            0b00110110,
                                            0b10111100,
                                            0b11111001,  # Tile 2
                                            0b01101010,
                                            0b10011000,
                                            0b11111111,
                                            0b11001011,
                                            0b00111000,
                                            0b01000001,
                                            0b01110001,
                                            0b11001010,
                                            0b11000000,
                                            0b01111010,
                                            0b11011101,
                                            0b00011011,
                                            0b00001111,
                                            0b00100001,
                                            0b11110000])

    def test_block_size(self):
        assert_equal(EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8).block_size(2), 32)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=8, tile_height=8).block_size(2), 160)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=8, tile_height=8).block_size(4), 320)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=8, tile_height=8).block_size(8), 640)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=8, tile_height=8).block_size(1), 80)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=8, tile_height=16).block_size(1), 160)
        assert_equal(EbGraphicTileset(num_tiles=10, tile_width=16, tile_height=16).block_size(1), 320)

    def test_from_image_8x8_1bpp(self):
        palette = EbPalette(1, 2)
        palette[0, 0].from_tuple((0xff, 0xff, 0xff))
        palette[0, 1].from_tuple((0x0, 0x0, 0x0))

        arrangement = EbTileArrangement(width=2, height=2)
        arrangement[0, 0].tile = 0
        arrangement[1, 0].tile = 2
        arrangement[0, 1].tile = 1
        arrangement[1, 1].tile = 3

        tileset = EbGraphicTileset(num_tiles=4, tile_width=8, tile_height=8)
        tileset.from_image(self.tile_8x8_2bpp_img, arrangement=arrangement, palette=palette)
        assert_list_equal(tileset[0], [[0] * 8] * 8)
        assert_list_equal(tileset[2], [[1] * 8] * 8)
        assert_list_equal(tileset[1],
                          [[0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 1, 1, 1, 1, 0, 0],
                           [0, 0, 1, 1, 1, 1, 0, 0],
                           [0, 0, 1, 1, 1, 1, 0, 0],
                           [0, 0, 1, 1, 1, 1, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0]])
        assert_list_equal(tileset[3],
                          [[0, 1, 1, 1, 1, 1, 1, 1],
                           [0, 1, 1, 1, 1, 1, 1, 1],
                           [0, 1, 0, 0, 0, 0, 1, 1],
                           [1, 1, 0, 0, 1, 0, 1, 1],
                           [1, 1, 0, 1, 0, 0, 1, 1],
                           [1, 1, 0, 0, 0, 0, 1, 1],
                           [1, 1, 1, 1, 1, 1, 1, 1],
                           [1, 1, 1, 1, 1, 1, 1, 0]])

    def test_from_image_8x16_2bpp(self):
        palette = EbPalette(1, 4)
        palette[0, 0].from_tuple((0xff, 0xff, 0xff))
        palette[0, 1].from_tuple((0x30, 0x00, 0xff))
        palette[0, 2].from_tuple((0xff, 0x00, 0x00))
        palette[0, 3].from_tuple((0x00, 0xff, 0x48))

        arrangement = EbTileArrangement(width=2, height=3)
        arrangement[0, 0].tile = 1
        arrangement[1, 0].tile = 1
        arrangement[0, 1].tile = 3
        arrangement[1, 1].tile = 2
        arrangement[0, 2].tile = 0
        arrangement[1, 2].tile = 4

        tileset = EbGraphicTileset(num_tiles=5, tile_width=8, tile_height=16)
        tileset.from_image(self.tile_8x16_4bpp_img, arrangement=arrangement, palette=palette)

        assert_list_equal(tileset[1], [[2] * 8] * 16)
        assert_list_equal(tileset[3], [[3] * 8] * 16)
        assert_list_equal(tileset[2],
                          [[3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3, 3, 1, 3, 3, 3, 3, 3],
                           [3, 3, 1, 3, 3, 1, 3, 3],
                           [1] * 8,
                           [1, 1, 2, 2, 1, 1, 1, 1],
                           [1, 2, 2, 2, 2, 2, 1, 1],
                           [1, 1, 1, 1, 1, 2, 1, 1],
                           [1, 1, 1, 1, 2, 2, 1, 1],
                           [1, 1, 2, 2, 2, 1, 1, 1],
                           [1] * 8,
                           [1] * 8,
                           [1, 1, 1, 3, 1, 1, 1, 1]])
        assert_list_equal(tileset[0],
                          [[2, 1, 1, 1, 1, 1, 1, 1],
                           [2, 3, 3, 3, 3, 3, 3, 1],
                           [0, 2, 3, 3, 3, 3, 1, 3],
                           [0, 2, 3, 3, 3, 3, 1, 3],
                           [0, 0, 2, 3, 3, 1, 3, 3],
                           [0, 0, 2, 3, 3, 1, 3, 3],
                           [0, 0, 0, 2, 1, 3, 3, 3],
                           [0, 0, 0, 2, 1, 3, 3, 3],
                           [0, 0, 0, 1, 2, 3, 3, 3],
                           [0, 0, 0, 1, 2, 3, 3, 3],
                           [0, 0, 1, 0, 0, 2, 3, 3],
                           [0, 0, 1, 0, 0, 2, 3, 3],
                           [0, 1, 0, 0, 0, 0, 2, 3],
                           [0, 1, 0, 0, 0, 0, 2, 3],
                           [1, 0, 0, 0, 0, 0, 0, 2],
                           [1, 0, 0, 0, 0, 0, 0, 2]])
        assert_list_equal(tileset[4],
                          [[3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3, 2, 3, 3, 3, 2, 3, 3],
                           [3] * 8,
                           [3] * 8,
                           [3, 3, 3, 3, 3, 3, 3, 2],
                           [2, 3, 3, 3, 3, 3, 2, 3],
                           [3, 2, 3, 3, 3, 2, 2, 3],
                           [3, 2, 2, 2, 2, 2, 3, 3],
                           [3] * 8,
                           [3] * 8,
                           [3] * 8,
                           [3] * 8])


class TestEbTileArrangementItem(BaseTestCase):
    def test_init(self):
        arrangement_item = EbTileArrangementItem(tile=12, subpalette=3, is_vertically_flipped=False,
                                                 is_horizontally_flipped=True, is_priority=True)
        assert_equal(arrangement_item.tile, 12)
        assert_equal(arrangement_item.subpalette, 3)
        assert_false(arrangement_item.is_vertically_flipped, False)
        assert_true(arrangement_item.is_horizontally_flipped, True)
        assert_true(arrangement_item.is_priority, True)

        assert_raises(InvalidArgumentError, EbTileArrangementItem, -1, 0)
        assert_raises(InvalidArgumentError, EbTileArrangementItem, 0, -1)
        assert_raises(InvalidArgumentError, EbTileArrangementItem, -1, -1)
        assert_raises(InvalidArgumentError, EbTileArrangementItem, 0x400, 0)
        assert_raises(InvalidArgumentError, EbTileArrangementItem, 0, 8)
        assert_raises(InvalidArgumentError, EbTileArrangementItem, 0x400, 8)

    def test_from_block(self):
        arrangement_item = EbTileArrangementItem()
        block = Block()
        block.from_list([3] * 3)

        block.write_multi(0, 0x8000 | 0x2000 | (7 << 10) | 0x120, 2)
        arrangement_item.from_block(block, 0)
        assert_true(arrangement_item.is_vertically_flipped)
        assert_false(arrangement_item.is_horizontally_flipped)
        assert_true(arrangement_item.is_priority, True)
        assert_equal(arrangement_item.subpalette, 7)
        assert_equal(arrangement_item.tile, 0x120)

        block.write_multi(1, 0x4000 | (2 << 10) | 0x3f5, 2)
        arrangement_item.from_block(block, 1)
        assert_false(arrangement_item.is_vertically_flipped)
        assert_true(arrangement_item.is_horizontally_flipped)
        assert_false(arrangement_item.is_priority)
        assert_equal(arrangement_item.subpalette, 2)
        assert_equal(arrangement_item.tile, 0x3f5)

    def test_to_block(self):
        arrangement_item = EbTileArrangementItem()
        block = Block()
        block.from_list([4] * 3)

        arrangement_item.is_vertically_flipped = True
        arrangement_item.is_horizontally_flipped = False
        arrangement_item.is_priority = True
        arrangement_item.subpalette = 7
        arrangement_item.tile = 0x120
        arrangement_item.to_block(block, 0)
        assert_equal(block.read_multi(0, 2), 0x8000 | 0x2000 | (7 << 10) | 0x120)

        arrangement_item.is_vertically_flipped = False
        arrangement_item.is_horizontally_flipped = True
        arrangement_item.is_priority = False
        arrangement_item.subpalette = 2
        arrangement_item.tile = 0x3f5
        arrangement_item.to_block(block, 1)
        assert_equal(block.read_multi(1, 2), 0x4000 | (2 << 10) | 0x3f5)


class TestEbTileArrangement(BaseTestCase):
    def test_init(self):
        arrangement = EbTileArrangement(32, 28)
        assert_equal(arrangement.width, 32)
        assert_equal(arrangement.height, 28)

        assert_raises(InvalidArgumentError, EbTileArrangement, 0, 32)
        assert_raises(InvalidArgumentError, EbTileArrangement, -1, 32)
        assert_raises(InvalidArgumentError, EbTileArrangement, 32, 0)
        assert_raises(InvalidArgumentError, EbTileArrangement, 32, -1)
        assert_raises(InvalidArgumentError, EbTileArrangement, 0, 0)
        assert_raises(InvalidArgumentError, EbTileArrangement, -1, -1)

    def test_from_block(self):
        block = Block()
        block.from_list([1] * 5)
        block.write_multi(1, 0x8000 | 0x2000 | (7 << 10) | 0x120, 2)
        block.write_multi(3, 0x4000 | (2 << 10) | 0x3f5, 2)

        arrangement = EbTileArrangement(2, 1)
        arrangement.from_block(block, 1)

        assert_true(arrangement[0, 0].is_vertically_flipped)
        assert_false(arrangement[0, 0].is_horizontally_flipped)
        assert_true(arrangement[0, 0].is_priority, True)
        assert_equal(arrangement[0, 0].subpalette, 7)
        assert_equal(arrangement[0, 0].tile, 0x120)

        assert_false(arrangement[1, 0].is_vertically_flipped)
        assert_true(arrangement[1, 0].is_horizontally_flipped)
        assert_false(arrangement[1, 0].is_priority)
        assert_equal(arrangement[1, 0].subpalette, 2)
        assert_equal(arrangement[1, 0].tile, 0x3f5)

        arrangement = EbTileArrangement(1, 2)
        arrangement.from_block(block, 1)

        assert_true(arrangement[0, 0].is_vertically_flipped)
        assert_false(arrangement[0, 0].is_horizontally_flipped)
        assert_true(arrangement[0, 0].is_priority, True)
        assert_equal(arrangement[0, 0].subpalette, 7)
        assert_equal(arrangement[0, 0].tile, 0x120)

        assert_false(arrangement[0, 1].is_vertically_flipped)
        assert_true(arrangement[0, 1].is_horizontally_flipped)
        assert_false(arrangement[0, 1].is_priority)
        assert_equal(arrangement[0, 1].subpalette, 2)
        assert_equal(arrangement[0, 1].tile, 0x3f5)

    def test_getitem(self):
        arrangement = EbTileArrangement(2, 1)
        assert_is_instance(arrangement[0, 0], EbTileArrangementItem)
        assert_is_instance(arrangement[1, 0], EbTileArrangementItem)

        assert_raises(InvalidArgumentError, arrangement.__getitem__, (-1, 0))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (0, -1))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (-1, -1))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (0, 1))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (0, 2))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (1, 2))
        assert_raises(InvalidArgumentError, arrangement.__getitem__, (3, 0))