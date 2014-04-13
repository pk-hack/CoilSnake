from nose.tools import assert_list_equal, assert_equal

from coilsnake.model.common.blocks import Block
from coilsnake.util.eb.graphics import read_1bpp_graphic_from_block, write_1bpp_graphic_to_block, \
    read_2bpp_graphic_from_block, write_2bpp_graphic_to_block, write_4bpp_graphic_to_block, read_4bpp_graphic_from_block


def test_read_1bpp_graphic_from_block():
    source = Block()
    source.from_list([42,
                      0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000,
                      0b01110001,
                      0b00000001])
    target = [[0 for x in range(8)] for y in range(8)]
    assert_equal(8, read_1bpp_graphic_from_block(source, target, 1, x=0, y=0, height=8))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 1]])


def test_read_1bpp_graphic_from_block_offset_target():
    source = Block()
    source.from_list([0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000,
                      0b01110001,
                      0b00000001])
    target = [[0 for x in range(10)] for y in range(10)]
    assert_equal(8, read_1bpp_graphic_from_block(source, target, 0, x=2, y=1, height=8))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
        [0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
        [0, 0, 1, 1, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])


def test_read_1bpp_graphic_from_block_rectangular_short():
    source = Block()
    source.from_list([42, 0xeb,
                      0b00000011,
                      0b01110000,
                      0b01001001,
                      0b11110000,
                      0b01001010,
                      0b11001000])
    target = [[0 for x in range(8)] for y in range(6)]
    assert_equal(6, read_1bpp_graphic_from_block(source, target, 2, x=0, y=0, height=6))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0]])


def test_read_1bpp_graphic_from_block_rectangular_tall():
    source = Block()
    source.from_list([42, 11, 99,
                      0b00000011,
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
                      0b00000001,
                      12, 21])
    target = [[0 for x in range(8)] for y in range(16)]
    assert_equal(16, read_1bpp_graphic_from_block(source, target, 3, x=0, y=0, height=16))

    assert_list_equal(target, [
        [0, 0, 0, 0, 0, 0, 1, 1],
        [0, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0, 1],
        [1, 1, 1, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 1, 0],
        [1, 1, 0, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1]])


def test_write_1bpp_graphic_to_block():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0],
              [0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 1]]
    target = Block()
    target.from_list([32] * 10)
    assert_equal(8, write_1bpp_graphic_to_block(source, target, 1, x=0, y=0, height=8))
    assert_list_equal(target.to_list(), [32,
                                         0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000,
                                         0b01110001,
                                         0b00000001,
                                         32])


def test_write_1bpp_graphic_to_block_offset_source():
    source = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
              [0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
              [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
              [0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
              [0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
              [0, 0, 1, 1, 0, 0, 1, 0, 0, 0],
              [0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    target = Block()
    target.from_list([0] * 8)
    assert_equal(8, write_1bpp_graphic_to_block(source, target, 0, x=2, y=1, height=8))
    assert_list_equal(target.to_list(), [0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000,
                                         0b01110001,
                                         0b00000001])


def test_write_1bpp_graphic_to_block_rectangular_short():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0]]
    target = Block()
    target.from_list([0xeb] * 8)
    target[0] = 42
    assert_equal(6, write_1bpp_graphic_to_block(source, target, 2, x=0, y=0, height=6))
    assert_list_equal(target.to_list(), [42, 0xeb,
                                         0b00000011,
                                         0b01110000,
                                         0b01001001,
                                         0b11110000,
                                         0b01001010,
                                         0b11001000])


def test_read_1bpp_graphic_from_block_rectangular_tall():
    source = [[0, 0, 0, 0, 0, 0, 1, 1],
              [0, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 0, 1],
              [1, 1, 1, 1, 0, 0, 0, 0],
              [0, 1, 0, 0, 1, 0, 1, 0],
              [1, 1, 0, 0, 1, 0, 0, 0],
              [0, 1, 1, 1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0, 0, 0, 1],
              [0, 0, 1, 0, 0, 0, 0, 0],
              [0, 0, 1, 1, 0, 0, 0, 0],
              [0, 0, 1, 0, 1, 0, 0, 0],
              [0, 0, 1, 0, 1, 0, 0, 0],
              [0, 1, 1, 0, 0, 0, 0, 0],
              [1, 1, 1, 0, 0, 0, 0, 0],
              [1, 1, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 1]]
    target = Block()
    target.from_list([42, 11, 99, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 112, 113, 114, 115, 116, 12, 21])
    assert_equal(16, write_1bpp_graphic_to_block(source, target, 3, x=0, y=0, height=16))
    assert_list_equal(target.to_list(), [42, 11, 99,
                                         0b00000011,
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
                                         0b00000001,
                                         12, 21])


def test_read_2bpp_graphic_from_block():
    source = Block()
    source.from_list([1, 2, 3,
                      0b01010101,
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
                      0b10111100])
    target = [[0 for x in range(8)] for y in range(8)]
    assert_equal(16, read_2bpp_graphic_from_block(target=target, source=source, offset=3, x=0, y=0, bit_offset=0))
    assert_list_equal(target,
                      [[2, 1, 2, 3, 2, 1, 2, 1],
                       [2, 3, 1, 0, 2, 3, 2, 2],
                       [3, 0, 3, 2, 2, 2, 0, 2],
                       [1, 3, 3, 0, 2, 0, 2, 3],
                       [1, 0, 1, 1, 0, 3, 3, 3],
                       [1, 3, 3, 3, 3, 2, 1, 2],
                       [2, 2, 3, 1, 2, 2, 1, 0],
                       [2, 0, 3, 3, 2, 3, 1, 0]])


def test_read_2bpp_graphic_from_block_offset_xy():
    source = Block()
    source.from_list([0b01010101,
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
                      0b10111100, 5])
    target = [[0 for x in range(10)] for y in range(10)]
    assert_equal(16, read_2bpp_graphic_from_block(target=target, source=source, offset=0, x=2, y=1, bit_offset=0))
    assert_list_equal(target,
                      [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 2, 1, 2, 3, 2, 1, 2, 1],
                       [0, 0, 2, 3, 1, 0, 2, 3, 2, 2],
                       [0, 0, 3, 0, 3, 2, 2, 2, 0, 2],
                       [0, 0, 1, 3, 3, 0, 2, 0, 2, 3],
                       [0, 0, 1, 0, 1, 1, 0, 3, 3, 3],
                       [0, 0, 1, 3, 3, 3, 3, 2, 1, 2],
                       [0, 0, 2, 2, 3, 1, 2, 2, 1, 0],
                       [0, 0, 2, 0, 3, 3, 2, 3, 1, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])


def test_write_2bpp_graphic_to_block():
    source = [[2, 1, 2, 3, 2, 1, 2, 1],
              [2, 3, 1, 0, 2, 3, 2, 2],
              [3, 0, 3, 2, 2, 2, 0, 2],
              [1, 3, 3, 0, 2, 0, 2, 3],
              [1, 0, 1, 1, 0, 3, 3, 3],
              [1, 3, 3, 3, 3, 2, 1, 2],
              [2, 2, 3, 1, 2, 2, 1, 0],
              [2, 0, 3, 3, 2, 3, 1, 0]]
    target = Block()
    target.from_list([0] * 16)
    assert_equal(16, write_2bpp_graphic_to_block(source=source, target=target, offset=0, x=0, y=0, bit_offset=0))
    assert_list_equal(target.to_list(),
                      [0b01010101,
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
                       0b10111100])


def test_write_2bpp_graphic_to_block_offset_xy():
    source = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 2, 1, 2, 3, 2, 1, 2, 1],
              [0, 0, 2, 3, 1, 0, 2, 3, 2, 2],
              [0, 0, 3, 0, 3, 2, 2, 2, 0, 2],
              [0, 0, 1, 3, 3, 0, 2, 0, 2, 3],
              [0, 0, 1, 0, 1, 1, 0, 3, 3, 3],
              [0, 0, 1, 3, 3, 3, 3, 2, 1, 2],
              [0, 0, 2, 2, 3, 1, 2, 2, 1, 0],
              [0, 0, 2, 0, 3, 3, 2, 3, 1, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    target = Block()
    target.from_list([0xff] * 18)
    assert_equal(16, write_2bpp_graphic_to_block(source=source, target=target, offset=1, x=2, y=1, bit_offset=0))
    assert_list_equal(target.to_list(),
                      [0xff,
                       0b01010101,
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
                       0xff])


def test_read_4bpp_graphic_from_block():
    source = Block()
    source.from_list([0b01010110,
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
    target = [[0 for x in range(8)] for y in range(8)]
    assert_equal(32, read_4bpp_graphic_from_block(target=target, source=source, offset=0, x=0, y=0, bit_offset=0))
    assert_list_equal(target,
                      [[8, 1, 12, 9, 6, 5, 3, 2],
                       [11, 5, 8, 14, 1, 7, 15, 0],
                       [8, 13, 3, 7, 2, 0, 2, 3],
                       [10, 0, 4, 14, 7, 10, 11, 9],
                       [8, 8, 12, 9, 13, 12, 2, 6],
                       [11, 14, 14, 4, 14, 4, 10, 7],
                       [12, 2, 12, 8, 4, 15, 12, 14],
                       [10, 13, 12, 1, 10, 11, 11, 2]])


def test_write_4bpp_graphic_to_block():
    source = [[8, 1, 12, 9, 6, 5, 3, 2],
              [11, 5, 8, 14, 1, 7, 15, 0],
              [8, 13, 3, 7, 2, 0, 2, 3],
              [10, 0, 4, 14, 7, 10, 11, 9],
              [8, 8, 12, 9, 13, 12, 2, 6],
              [11, 14, 14, 4, 14, 4, 10, 7],
              [12, 2, 12, 8, 4, 15, 12, 14],
              [10, 13, 12, 1, 10, 11, 11, 2]]
    target = Block()
    target.from_list([0] * 32)
    assert_equal(32, write_4bpp_graphic_to_block(source=source, target=target, offset=0, x=0, y=0, bit_offset=0))
    assert_list_equal(target.to_list(),
                      [
                          0b01010110,
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
                          0b11101110
                      ])