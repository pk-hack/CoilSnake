from nose.tools import assert_equal, assert_raises, assert_list_equal

from coilsnake.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.graphics import EbGraphicTileset
from tests.coilsnake_test import BaseTestCase


class TestEbGraphicTileset(BaseTestCase):
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