from array import array

from nose.tools import assert_equal, assert_raises, assert_list_equal, assert_false, assert_true, assert_is_instance, \
    assert_not_equal, assert_set_equal, nottest

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.graphics import EbGraphicTileset, EbTileArrangementItem, EbTileArrangement
from coilsnake.model.eb.palettes import EbPalette, EbColor
from tests.coilsnake_test import BaseTestCase, TilesetImageTestCase, assert_images_equal


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

    def test_from_block_4bpp(self):
        block = Block()
        block.from_list([0b01010110,
                         0b00001011,

                         0b11001110,
                         0b10010110,

                         0b01110001,
                         0b00111011,

                         0b00001011,
                         0b10011110,

                         0b00011000,
                         0b00000011,

                         0b10000001,
                         0b11101011,

                         0b00000100,
                         0b01000101,

                         0b01010110,
                         0b10001111,

                         0b00101100,
                         0b10110000,

                         0b01010110,
                         0b10110010,

                         0b01010000,
                         0b11000000,

                         0b00111000,
                         0b10010111,

                         0b00101101,
                         0b11111100,

                         0b01111101,
                         0b11101010,

                         0b10101111,
                         0b10110111,

                         0b01100000,
                         0b11101110])
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=8)
        tileset.from_block(block, offset=0, bpp=4)
        assert_list_equal(tileset[0], [[8, 1, 12, 9, 6, 5, 3, 2],
                                       [11, 5, 8, 14, 1, 7, 15, 0],
                                       [8, 13, 3, 7, 2, 0, 2, 3],
                                       [10, 0, 4, 14, 7, 10, 11, 9],
                                       [8, 8, 12, 9, 13, 12, 2, 6],
                                       [11, 14, 14, 4, 14, 4, 10, 7],
                                       [12, 2, 12, 8, 4, 15, 12, 14],
                                       [10, 13, 12, 1, 10, 11, 11, 2]])


    def test_to_block_invalid(self):
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=16)
        block = Block()
        assert_raises(NotImplementedError, tileset.to_block, block, 0, 32)
        assert_raises(NotImplementedError, tileset.to_block, block, 0, 2)

    def test_to_block_1bpp(self):
        tileset = EbGraphicTileset(num_tiles=2, tile_width=8, tile_height=8)
        tileset.tiles = [None, None]
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
        tileset.tiles = [None, None]
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

    def test_to_block_4bpp(self):
        tileset = EbGraphicTileset(num_tiles=1, tile_width=8, tile_height=8)
        tileset.tiles = [None]
        tileset.tiles[0] = [[8, 1, 12, 9, 6, 5, 3, 2],
                            [11, 5, 8, 14, 1, 7, 15, 0],
                            [8, 13, 3, 7, 2, 0, 2, 3],
                            [10, 0, 4, 14, 7, 10, 11, 9],
                            [8, 8, 12, 9, 13, 12, 2, 6],
                            [11, 14, 14, 4, 14, 4, 10, 7],
                            [12, 2, 12, 8, 4, 15, 12, 14],
                            [10, 13, 12, 1, 10, 11, 11, 2]]
        block = Block()
        block.from_list([0] * 32)
        tileset.to_block(block, 0, 4)
        assert_list_equal(block.to_list(), [0b01010110,
                                            0b00001011,

                                            0b11001110,
                                            0b10010110,

                                            0b01110001,
                                            0b00111011,

                                            0b00001011,
                                            0b10011110,

                                            0b00011000,
                                            0b00000011,

                                            0b10000001,
                                            0b11101011,

                                            0b00000100,
                                            0b01000101,

                                            0b01010110,
                                            0b10001111,

                                            0b00101100,
                                            0b10110000,

                                            0b01010110,
                                            0b10110010,

                                            0b01010000,
                                            0b11000000,

                                            0b00111000,
                                            0b10010111,

                                            0b00101101,
                                            0b11111100,

                                            0b01111101,
                                            0b11101010,

                                            0b10101111,
                                            0b10110111,

                                            0b01100000,
                                            0b11101110])

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

    def test_add_tile(self):
        tileset = EbGraphicTileset(num_tiles=5, tile_width=8, tile_height=8)
        tile = [array('B', [5, 7, 6, 4, 1, 5, 3, 3]),
                array('B', [5, 8, 3, 7, 5, 7, 1, 1]),
                array('B', [6, 1, 1, 5, 4, 0, 1, 5]),
                array('B', [2, 1, 4, 5, 4, 1, 6, 4]),
                array('B', [4, 6, 6, 2, 1, 0, 4, 4]),
                array('B', [6, 1, 0, 7, 5, 8, 1, 8]),
                array('B', [8, 0, 4, 0, 2, 8, 0, 8]),
                array('B', [0, 6, 8, 6, 0, 5, 4, 0])]
        tile1_id, tile1_vflip, tile1_hflip = tileset.add_tile(tile)

        tile2_id, tile2_vflip, tile2_hflip = tileset.add_tile(tile)
        assert_equal(tile2_id, tile1_id)
        assert_equal(tile2_vflip, tile1_vflip)
        assert_equal(tile2_hflip, tile1_hflip)

        tile.reverse()
        tile2_id, tile2_vflip, tile2_hflip = tileset.add_tile(tile)
        assert_equal(tile2_id, tile1_id)
        assert_equal(tile2_vflip, not tile1_vflip)
        assert_equal(tile2_hflip, tile1_hflip)

        for row in tile:
            row.reverse()
        tile2_id, tile2_vflip, tile2_hflip = tileset.add_tile(tile)
        assert_equal(tile2_id, tile1_id)
        assert_equal(tile2_vflip, not tile1_vflip)
        assert_equal(tile2_hflip, not tile1_hflip)

        tile.reverse()
        tile2_id, tile2_vflip, tile2_hflip = tileset.add_tile(tile)
        assert_equal(tile2_id, tile1_id)
        assert_equal(tile2_vflip, tile1_vflip)
        assert_equal(tile2_hflip, not tile1_hflip)

        tile = [array('B', [1, 2, 3, 4, 1, 5, 3, 3]),
                array('B', [5, 8, 3, 7, 5, 7, 1, 1]),
                array('B', [6, 1, 1, 5, 4, 0, 1, 5]),
                array('B', [2, 1, 4, 5, 4, 1, 6, 4]),
                array('B', [4, 6, 6, 2, 1, 0, 4, 4]),
                array('B', [6, 1, 0, 7, 5, 8, 1, 8]),
                array('B', [8, 0, 4, 0, 2, 8, 0, 8]),
                array('B', [0, 6, 8, 6, 0, 5, 4, 0])]
        tile2_id, tile2_vflip, tile2_hflip = tileset.add_tile(tile)
        assert_not_equal(tile2_id, tile1_id)


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


class TestEbTileArrangement(BaseTestCase, TilesetImageTestCase):
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

    def test_from_image_single_subpalette(self):
        palette = EbPalette(1, 2)
        tileset = EbGraphicTileset(num_tiles=6, tile_width=8, tile_height=8)
        arrangement = EbTileArrangement(width=6, height=1)
        arrangement.from_image(self.tile_8x8_2bpp_2_img, tileset=tileset, palette=palette)

        assert_equal(palette[0, 0], EbColor(0, 0, 0))
        assert_equal(palette[0, 1], EbColor(0xf8, 0xf8, 0xf8))

        item = arrangement[0, 0]
        assert_equal(item.subpalette, 0)

        assert_equal(arrangement[1, 0].tile, item.tile)
        assert_equal(arrangement[1, 0].is_horizontally_flipped, not item.is_horizontally_flipped)
        assert_equal(arrangement[1, 0].is_vertically_flipped, item.is_vertically_flipped)
        assert_equal(arrangement[1, 0].subpalette, 0)

        assert_equal(arrangement[2, 0].tile, item.tile)
        assert_equal(arrangement[2, 0].is_horizontally_flipped, item.is_horizontally_flipped)
        assert_equal(arrangement[2, 0].is_vertically_flipped, not item.is_vertically_flipped)
        assert_equal(arrangement[2, 0].subpalette, 0)

        assert_equal(arrangement[3, 0].tile, item.tile)
        assert_equal(arrangement[3, 0].is_horizontally_flipped, not item.is_horizontally_flipped)
        assert_equal(arrangement[2, 0].is_vertically_flipped, not item.is_vertically_flipped)
        assert_equal(arrangement[3, 0].subpalette, 0)

        assert_not_equal(arrangement[4, 0].tile, item.tile)
        assert_equal(arrangement[4, 0].subpalette, 0)

        assert_equal(arrangement[5, 0].tile, item.tile)
        assert_equal(arrangement[5, 0].is_horizontally_flipped, item.is_horizontally_flipped)
        assert_equal(arrangement[5, 0].is_vertically_flipped, item.is_vertically_flipped)
        assert_equal(arrangement[5, 0].subpalette, 0)

    @nottest
    def test_from_image_2_subpalettes(self):
        palette = EbPalette(2, 4)
        tileset = EbGraphicTileset(num_tiles=4, tile_width=8, tile_height=8)
        arrangement = EbTileArrangement(width=4, height=1)
        arrangement.from_image(image=self.tile_8x8_2bpp_3_img, tileset=tileset, palette=palette)

        img_palette = self.tile_8x8_2bpp_3_img.getpalette()
        self.tile_8x8_2bpp_3_img.putpalette([x & 0xf8 for x in img_palette])
        before_image_rgb = self.tile_8x8_2bpp_3_img.convert("RGB")
        after_image_rgb = arrangement.image(tileset, palette).convert("RGB")
        assert_images_equal(before_image_rgb, after_image_rgb)

        assert_set_equal({palette[1, i] for i in range(4)},
                         {EbColor(24, 0, 248), EbColor(0, 248, 24), EbColor(152, 0, 248), EbColor(248, 144, 0)})
        assert_set_equal({palette[0, i] for i in range(4)},
                         {EbColor(24, 0, 248), EbColor(0, 248, 24), EbColor(216, 248, 0), EbColor(152, 0, 248)})

        assert_equal(arrangement[0, 0].tile, 0)
        assert_equal(arrangement[0, 0].subpalette, 0)
        assert_equal({tileset[0][0][i] for i in [-1, -2, -3, -4]}, {0, 1, 2, 3})

        assert_equal(arrangement[1, 0].tile, 1)
        assert_equal(arrangement[1, 0].subpalette, 1)
        assert_equal({tileset[1][0][i] for i in [-1, -2, -3, -4]}, {0, 1, 2, 3})

        assert_equal(arrangement[2, 0].tile, 2)
        assert_equal(arrangement[2, 0].subpalette, 0)

        assert_equal(arrangement[3, 0].tile, 3)
        assert_equal(arrangement[3, 0].subpalette, 1)

    def test_to_image_single_subpalette(self):
        palette = EbPalette(1, 2)
        tileset = EbGraphicTileset(num_tiles=6, tile_width=8, tile_height=8)
        arrangement = EbTileArrangement(width=6, height=1)
        arrangement.from_image(self.tile_8x8_2bpp_2_img, tileset=tileset, palette=palette)

        new_image = arrangement.image(tileset, palette)
        assert_images_equal(self.tile_8x8_2bpp_2_img, new_image)